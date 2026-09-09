#!/usr/bin/env python3
import argparse
import ast
import glob
import hashlib
import itertools
import json
import math
import os
import random
import shlex
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hpo_spaces as S


def atomic_json(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(obj, fh, indent=2, default=str)
    os.replace(tmp, path)


def git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def param_hash(params):
    blob = json.dumps({k: params[k] for k in sorted(params)}, sort_keys=True,
                      default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


class Tee:
    def __init__(self, path):
        self.fh = open(path, "a", buffering=1)

    def __call__(self, *a):
        msg = " ".join(str(x) for x in a)
        print(msg, flush=True)
        self.fh.write(msg + "\n")


def expand_grid(space):
    axes = space.get("axes", {})
    blocks = space.get("blocks", [])
    design = space.get("design", "ofat+blocks")
    seen, out = set(), []

    def add(params, origin):
        base = dict(S.INCUMBENT)
        base.update(params)
        keys = set(axes) | set(params)
        for b in blocks:
            keys |= set(b["axes"])
        cell = {k: base[k] for k in sorted(keys)}
        h = param_hash(cell)
        if h in seen:
            return
        bad = S.check_constraints(cell)
        if bad:
            out.append({"params": cell, "origin": origin, "invalid": bad})
            seen.add(h)
            return
        seen.add(h)
        out.append({"params": cell, "origin": origin, "invalid": []})

    if design == "cartesian":
        names = list(axes)
        for combo in itertools.product(*(axes[n] for n in names)):
            add(dict(zip(names, combo)), "cartesian")
        return out

    add({}, "incumbent")
    for name, values in axes.items():
        for v in values:
            if v == S.INCUMBENT.get(name):
                continue
            add({name: v}, f"ofat:{name}")
    for b in blocks:
        names = list(b["axes"])
        for combo in itertools.product(*(b["axes"][n] for n in names)):
            add(dict(zip(names, combo)), f"block:{b['name']}")
    return out


def _sample_axis(spec, rng):
    t = spec["type"]
    if t == "cat":
        return rng.choice(spec["choices"])
    if t == "int":
        step = spec.get("step", 1)
        n = int((spec["high"] - spec["low"]) // step)
        return int(spec["low"] + step * rng.randint(0, n))
    if t == "logfloat":
        if spec.get("allow_zero") and rng.random() < 0.15:
            return 0.0
        lo, hi = math.log(spec["low"]), math.log(spec["high"])
        return math.exp(rng.uniform(lo, hi))
    return rng.uniform(spec["low"], spec["high"])


class RandomSampler:
    name = "random"

    def __init__(self, space, seed=0):
        self.space, self.rng = space, random.Random(seed)

    def ask(self, n, observed):
        out = []
        for _ in range(n):
            p = {k: _sample_axis(v, self.rng) for k, v in self.space["axes"].items()}
            out.append(p)
        return out


class TPESampler:
    name = "tpe"

    def __init__(self, space, seed=0, gamma=0.20, n_candidates=32, n_startup=8):
        self.space, self.rng = space, random.Random(seed)
        self.gamma, self.n_candidates, self.n_startup = gamma, n_candidates, n_startup

    @staticmethod
    def _to_internal(spec, v):
        return math.log(max(v, spec["low"] * 1e-3)) if spec["type"] == "logfloat" else float(v)

    @staticmethod
    def _bounds(spec):
        if spec["type"] == "logfloat":
            return math.log(spec["low"]), math.log(spec["high"])
        return float(spec["low"]), float(spec["high"])

    def _parzen(self, spec, values):
        lo, hi = self._bounds(spec)
        rng_width = hi - lo
        xs = sorted(self._to_internal(spec, v) for v in values)
        mus = list(xs) + [(lo + hi) / 2.0]
        sig_floor = rng_width / 20.0
        sigmas = []
        for i, x in enumerate(xs):
            left = x - xs[i - 1] if i > 0 else rng_width
            right = xs[i + 1] - x if i + 1 < len(xs) else rng_width
            sigmas.append(min(max(max(left, right), sig_floor), rng_width))
        sigmas.append(rng_width)
        w = [1.0] * len(xs) + [1.0]
        tot = sum(w)
        return mus, sigmas, [x / tot for x in w], (lo, hi)

    def _logpdf(self, mix, x):
        mus, sigmas, ws, _ = mix
        acc = 0.0
        for m, s, w in zip(mus, sigmas, ws):
            acc += w * math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))
        return math.log(max(acc, 1e-300))

    def _draw(self, mix, rng):
        mus, sigmas, ws, (lo, hi) = mix
        r, acc = rng.random(), 0.0
        for m, s, w in zip(mus, sigmas, ws):
            acc += w
            if r <= acc:
                return min(max(rng.gauss(m, s), lo), hi)
        return rng.uniform(lo, hi)

    @staticmethod
    def _from_internal(spec, x):
        if spec["type"] == "logfloat":
            return math.exp(x)
        if spec["type"] == "int":
            step = spec.get("step", 1)
            return int(round((x - spec["low"]) / step) * step + spec["low"])
        return float(x)

    def ask(self, n, observed):
        usable = [(p, o) for p, o in observed if o is not None and math.isfinite(o)]
        out = []
        for _ in range(n):
            if len(usable) < self.n_startup:
                out.append({k: _sample_axis(v, self.rng)
                            for k, v in self.space["axes"].items()})
                continue
            ranked = sorted(usable, key=lambda t: -t[1])
            n_below = max(1, min(int(math.ceil(self.gamma * len(ranked))), 25))
            below = [p for p, _ in ranked[:n_below]]
            above = [p for p, _ in ranked[n_below:]] or below
            cand_best, score_best = None, -1e300
            for _c in range(self.n_candidates):
                cand, score = {}, 0.0
                for name, spec in self.space["axes"].items():
                    if spec["type"] == "cat":
                        ch = spec["choices"]
                        cb = {c: 1.0 for c in ch}
                        ca = {c: 1.0 for c in ch}
                        for p in below:
                            cb[p[name]] = cb.get(p[name], 1.0) + 1.0
                        for p in above:
                            ca[p[name]] = ca.get(p[name], 1.0) + 1.0
                        tb, ta = sum(cb.values()), sum(ca.values())
                        pick = self.rng.choices(ch, weights=[cb[c] for c in ch])[0]
                        cand[name] = pick
                        score += math.log(cb[pick] / tb) - math.log(ca[pick] / ta)
                        continue
                    mb = self._parzen(spec, [p[name] for p in below])
                    ma = self._parzen(spec, [p[name] for p in above])
                    x = self._draw(mb, self.rng)
                    score += self._logpdf(mb, x) - self._logpdf(ma, x)
                    cand[name] = self._from_internal(spec, x)
                if score > score_best:
                    cand_best, score_best = cand, score
            out.append(cand_best)
            if len(out) < n:
                med = sorted(o for _, o in usable)[len(usable) // 2]
                usable = usable + [(cand_best, med)]
        return out


class OptunaTPESampler:
    name = "optuna-tpe"

    def __init__(self, space, seed=0):
        import optuna
        from optuna.samplers import TPESampler as _T
        self.optuna = optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        self.space = space
        self.study = optuna.create_study(direction="maximize",
                                         sampler=_T(seed=seed, multivariate=True))
        self._n_told = 0

    def _suggest(self, trial):
        p = {}
        for name, spec in self.space["axes"].items():
            if spec["type"] == "cat":
                p[name] = trial.suggest_categorical(name, spec["choices"])
            elif spec["type"] == "int":
                p[name] = trial.suggest_int(name, spec["low"], spec["high"],
                                            step=spec.get("step", 1))
            elif spec["type"] == "logfloat":
                p[name] = trial.suggest_float(name, spec["low"], spec["high"], log=True)
            else:
                p[name] = trial.suggest_float(name, spec["low"], spec["high"])
        return p

    def ask(self, n, observed):
        for params, obj in observed[self._n_told:]:
            if obj is not None and math.isfinite(obj):
                self.study.add_trial(self.optuna.trial.create_trial(
                    params=params,
                    distributions=self._distributions(),
                    value=float(obj)))
            self._n_told += 1
        out = []
        for _ in range(n):
            t = self.study.ask()
            out.append(self._suggest(t))
        return out

    def _distributions(self):
        from optuna import distributions as D
        d = {}
        for name, spec in self.space["axes"].items():
            if spec["type"] == "cat":
                d[name] = D.CategoricalDistribution(spec["choices"])
            elif spec["type"] == "int":
                d[name] = D.IntDistribution(spec["low"], spec["high"],
                                            step=spec.get("step", 1))
            elif spec["type"] == "logfloat":
                d[name] = D.FloatDistribution(spec["low"], spec["high"], log=True)
            else:
                d[name] = D.FloatDistribution(spec["low"], spec["high"])
        return d


def flagify(name, value):
    spec = S.PARAMS.get(name)
    flag = spec["flag"] if spec else "--" + name.replace("_", "-")
    return flag, value


PATH_PASSTHROUGH = ("--vae", "--ckpt", "--latents-dir", "--mu-dir", "--reg",
                    "--ridge-gate", "--resume")


def valueless_flags(script_path):
    try:
        tree = ast.parse(open(script_path, encoding="utf-8").read())
    except Exception:
        return set()
    out = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "add_argument"):
            continue
        action = None
        for kw in node.keywords:
            if kw.arg == "action" and isinstance(kw.value, ast.Constant):
                action = kw.value.value
        if action in ("store_true", "store_false", "count", "help", "version"):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    out.add(a.value)
    return out


def preflight(passthrough, script_path):
    ok_bare = valueless_flags(script_path)
    problems = []
    for i, a in enumerate(passthrough):
        if not a.startswith("--") or a in ok_bare:
            continue
        nxt = passthrough[i + 1] if i + 1 < len(passthrough) else None
        if nxt is None or nxt.startswith("--"):
            problems.append(
                f"{a} was given no value (the next token is "
                f"{'end of command' if nxt is None else nxt}), which usually "
                "means an unset shell variable; check the exports in this shell.")
    for i, a in enumerate(passthrough[:-1]):
        if a in PATH_PASSTHROUGH:
            v = passthrough[i + 1]
            if v.startswith("--") or v == "auto":
                continue
            if not os.path.exists(os.path.expanduser(v)):
                problems.append(f"{a} points at {v}, which does not exist here.")
    return problems


def default_python(executor):
    return "python" if executor == "slurm" else sys.executable


def build_cmd(arm, script_dir, params, rung, trial_dir, passthrough, seed,
              tag=None, python=None):
    meta = S.ARMS[arm]
    cmd = [python or sys.executable, os.path.join(script_dir, meta["script"])]
    for name in sorted(params):
        flag, value = flagify(name, params[name])
        cmd += [flag, str(value)]
    for flag, value in S.rung_flags(arm, rung, params).items():
        if value is True:
            cmd.append(flag)
        elif value is False or value is None:
            continue
        else:
            cmd += [flag, str(value)]
    cmd += ["--seed", str(seed)]
    if meta["kind"] == "infer":
        cmd += [meta["out_flag"], os.path.dirname(trial_dir.rstrip("/")) + "/eval"]
        cmd += ["--tag", tag or ("_" + os.path.basename(trial_dir))]
    else:
        cmd += [meta["out_flag"], trial_dir]
    cmd += list(passthrough)
    return cmd


def _last_block(log, *names):
    for rec in reversed(log):
        for n in names:
            if rec.get(n):
                return rec[n]
    return None


def metrics_from_training(trial_dir):
    lp = os.path.join(trial_dir, "train_log.json")
    if not os.path.exists(lp):
        return None
    try:
        log = json.load(open(lp))
    except Exception:
        return None
    if not log:
        return None
    m = {}
    vs = [r["val"] for r in log if r.get("val")]
    if vs and "loss_w" in vs[0]:
        m["val_loss_w"] = min(v["loss_w"] for v in vs)
        m["val_loss_w_last"] = vs[-1]["loss_w"]
        m["val_metric"] = m["val_loss_w"]
    if vs and "mse" in vs[0]:
        m["val_mse"] = min(v["mse"] for v in vs)
        m["val_mse_last"] = vs[-1]["mse"]
        m.setdefault("val_metric", m["val_mse"])
    if vs and "ev" in vs[0]:
        m["val_ev"] = max(v["ev"] for v in vs)
        m["val_ev_last"] = vs[-1]["ev"]
    tr = log[-1].get("train", {})
    for k in ("loss_w", "mse", "ev"):
        if k in tr:
            m["train_" + k + "_last"] = tr[k]
    m["epochs_run"] = log[-1]["epoch"]
    sys_ = log[-1].get("sys", {})
    m["imgs_per_s"] = sys_.get("imgs_per_s", float("nan"))
    m["epoch_sec"] = sys_.get("epoch_sec", float("nan"))
    m["gpu_gb"] = sys_.get("gpu_gb", float("nan"))
    samp = _last_block(log, "sampled", "decoded")
    if samp:
        for k, v in samp.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                m[k] = v
        for a, b in (("mae", "mae_adv"), ("crps", "crps_adv")):
            if samp.get(b):
                m[a + "_ratio"] = samp[a] / samp[b]
    dp = os.path.join(trial_dir, "DONE")
    if os.path.exists(dp):
        try:
            d = json.load(open(dp))
            m["wall_min"] = d.get("wall_min")
            m["finish_reason"] = d.get("reason")
        except Exception:
            pass
    return m


def metrics_from_eval(json_path):
    if not os.path.exists(json_path):
        return None
    try:
        d = json.load(open(json_path))
    except Exception:
        return None
    det, prob = d.get("deterministic", {}), d.get("probabilistic", {})
    dist = d.get("distribution", {})
    m = {"n_crops": d.get("n_crops"), "wall_min": d.get("wall_min"),
         "members": d.get("members"), "steps": d.get("steps"),
         "guidance": d.get("guidance"), "churn": d.get("churn"),
         "ckpt_epoch": d.get("ckpt_epoch"), "git": d.get("git")}

    def g(method, key, default=float("nan")):
        return det.get(method, {}).get(key, default)

    m["mae"] = g("model_mean", "MAE_mmh")
    m["mae_member"] = g("model_member", "MAE_mmh")
    m["mae_adv"] = g("advection", "MAE_mmh")
    m["mae_pers"] = g("persistence", "MAE_mmh")
    m["rmse"] = g("model_mean", "RMSE_mmh")
    m["rmse_adv"] = g("advection", "RMSE_mmh")
    for meth, pre in (("model_mean", ""), ("model_member", "member_"),
                      ("advection", "adv_"), ("persistence", "pers_")):
        bt = det.get(meth, {}).get("by_threshold", {})
        for t in ("1.0", "8.0"):
            if t in bt:
                m[f"{pre}csi_{float(t):g}"] = bt[t].get("CSI", float("nan"))
    m["csi_1_adv"], m["csi_8_adv"] = m.get("adv_csi_1"), m.get("adv_csi_8")
    m["csi_1_pers"], m["csi_8_pers"] = m.get("pers_csi_1"), m.get("pers_csi_8")
    m["crps_fair"] = prob.get("CRPS_fair_mmh", float("nan"))
    m["crps"] = m["crps_fair"]
    m["crps_adv"] = m["mae_adv"]
    m["crps_pers"] = m["mae_pers"]
    m["spread_rmse_ratio"] = prob.get("spread_rmse_ratio", float("nan"))
    M = float(d.get("members") or 8)
    m["spread_rmse_ideal"] = math.sqrt(M / (M + 1.0))
    m["outlier_rate"] = prob.get("outlier_rate", float("nan"))
    m["outlier_rate_ideal"] = prob.get("outlier_rate_ideal", 2.0 / (M + 1.0))
    m["rank_flatness_rmse"] = prob.get("rank_flatness_rmse", float("nan"))
    bands = dist.get("psd_bands", {})
    for meth, pre in (("model_member", ""), ("model_mean", "mean_"),
                      ("advection", "adv_"), ("persistence", "pers_")):
        b = bands.get(meth, {})
        if b:
            m[pre + "psd_ratio_2_8km"] = b.get("psd_mean_ratio", float("nan"))
            m[pre + "psd_band_power"] = b.get("psd_band_power", float("nan"))
    for a, b in (("mae", "mae_adv"), ("crps", "crps_adv")):
        if m.get(b):
            m[a + "_ratio"] = m[a] / m[b]
    return m


SAFE_FUNCS = {"abs": abs, "min": min, "max": max, "sqrt": math.sqrt,
              "log": math.log, "exp": math.exp, "isfinite": math.isfinite}


def evaluate_expr(expr, metrics):
    env = dict(SAFE_FUNCS)
    for k, v in metrics.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            env[k] = v
    try:
        return eval(expr, {"__builtins__": {}}, env)
    except Exception:
        return None


class LocalExecutor:
    name = "local"

    def __init__(self, log):
        self.log = log

    def submit(self, trial):
        os.makedirs(trial["dir"], exist_ok=True)
        out = open(os.path.join(trial["dir"], "trial.out"), "a", buffering=1)
        out.write(f"\n==== {now()} :: {' '.join(shlex.quote(c) for c in trial['cmd'])}\n")
        trial["_proc"] = subprocess.Popen(trial["cmd"], stdout=out,
                                          stderr=subprocess.STDOUT, cwd=HERE)
        trial["_out"] = out
        trial["pid"] = trial["_proc"].pid
        return trial

    def poll(self, trial):
        p = trial.get("_proc")
        if p is None:
            return True
        rc = p.poll()
        if rc is None:
            return False
        trial["returncode"] = rc
        if trial.get("_out"):
            trial["_out"].close()
        return True

    def kill(self, trial):
        p = trial.get("_proc")
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=30)
            except Exception:
                p.kill()


class SlurmExecutor:
    name = "slurm"

    def __init__(self, log, wrapper, extra_sbatch=(), safety=2.0,
                 min_time="00:20:00", max_time="23:30:00", grace=90.0):
        self.log, self.wrapper = log, os.path.expanduser(wrapper)
        self.extra, self.safety = list(extra_sbatch), safety
        self.min_time, self.max_time = min_time, max_time
        self.grace = grace
        if not os.path.exists(self.wrapper):
            raise SystemExit(
                f"ERROR: gpu.sbatch wrapper not found at {self.wrapper}. Create it "
                "(README_jasmin.md section 8) or pass --gpu-sbatch. Never submit a "
                "GPU job to Orchid without the gpuhost007 exclusion.")

    def _walltime(self, hours):
        secs = int(max(self._to_s(self.min_time),
                       min(self._to_s(self.max_time), hours * 3600 * self.safety)))
        return f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"

    @staticmethod
    def _to_s(hhmmss):
        h, m, s = (int(x) for x in hhmmss.split(":"))
        return h * 3600 + m * 60 + s

    def submit(self, trial):
        os.makedirs(trial["dir"], exist_ok=True)
        sb = ["sbatch", "--parsable",
              f"--job-name={trial['job_name']}",
              f"--time={self._walltime(trial['cost_h_est'])}",
              f"--output={os.path.join(trial['dir'], 'slurm-%j.out')}"]
        sb += self.extra + [self.wrapper] + trial["cmd"]
        trial["sbatch"] = sb
        with open(os.path.join(trial["dir"], "submit.sh"), "w") as fh:
            fh.write("#!/bin/sh\n# emitted by hpo_search.py " + now() + "\n")
            fh.write(" ".join(shlex.quote(c) for c in sb) + "\n")
        res = subprocess.run(sb, capture_output=True, text=True, cwd=HERE)
        if res.returncode != 0:
            self.log(f"  SUBMIT FAILED {trial['id']}: {res.stderr.strip()[:300]}")
            trial["error"] = res.stderr.strip()[:500]
            trial["jobid"] = None
            return trial
        trial["jobid"] = res.stdout.strip().split(";")[0]
        trial["_submitted_at"] = time.time()
        self.log(f"  submitted {trial['id']} as job {trial['jobid']}")
        return trial

    def poll(self, trial):
        jid = trial.get("jobid")
        if not jid:
            return True
        if time.time() - trial.get("_submitted_at", 0) < self.grace:
            return False
        res = subprocess.run(["squeue", "-h", "-j", str(jid), "-o", "%T"],
                             capture_output=True, text=True)
        if res.returncode != 0 and "Invalid job id" not in (res.stderr or ""):
            self.log(f"  squeue failed for {trial['id']}: "
                     f"{(res.stderr or '').strip()[:160]}; treating as running")
            return False
        state = res.stdout.strip()
        if not state:
            return True
        trial["slurm_state"] = state.splitlines()[0]
        return False

    def kill(self, trial):
        if trial.get("jobid"):
            subprocess.run(["scancel", str(trial["jobid"])], capture_output=True)


class Study:
    def __init__(self, out, spec, log):
        self.out, self.spec, self.log = out, spec, log
        os.makedirs(out, exist_ok=True)
        self.trials_path = os.path.join(out, "trials.jsonl")
        self.tp_path = os.path.join(out, "throughput.json")
        self.throughput = {}
        if os.path.exists(self.tp_path):
            try:
                self.throughput = json.load(open(self.tp_path))
            except Exception:
                self.throughput = {}
        sp = os.path.join(out, "study.json")
        if os.path.exists(sp):
            old = json.load(open(sp))
            drift = [k for k in ("space", "arm", "objective", "gate", "seed")
                     if old.get(k) != spec.get(k)]
            if drift:
                raise SystemExit(
                    f"ERROR: {sp} already describes a different study (differs on "
                    f"{', '.join(drift)}). Point --out at a new directory rather "
                    "than mixing two studies in one trials table.")
            spec["created"] = old.get("created", spec["created"])
            spec["reruns"] = old.get("reruns", 0) + 1
        atomic_json(spec, sp)

    def event(self, **row):
        row = {"ts": now(), **row}
        with open(self.trials_path, "a") as fh:
            fh.write(json.dumps(row, default=str) + "\n")

    def note_throughput(self, params, metrics):
        ips = metrics.get("imgs_per_s") if metrics else None
        if ips and math.isfinite(ips) and ips > 0:
            self.throughput[S.arch_signature(params)] = round(float(ips), 1)
            atomic_json(self.throughput, self.tp_path)

    def spent_gpu_h(self):
        tot = 0.0
        if not os.path.exists(self.trials_path):
            return 0.0
        for line in open(self.trials_path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") != "finish":
                continue
            wm = (r.get("metrics") or {}).get("wall_min")
            if wm is None:
                wm = r.get("wall_min")
            if wm:
                tot += float(wm) / 60.0
        return tot


def failure_tail(trial, n=12):
    cands = sorted(glob.glob(os.path.join(trial["dir"], "slurm-*.out")),
                   key=os.path.getmtime, reverse=True)
    path = cands[0] if cands else os.path.join(trial["dir"], "trial.out")
    if not os.path.exists(path):
        return None
    try:
        with open(path, errors="replace") as fh:
            lines = [ln.rstrip() for ln in fh.read().splitlines() if ln.strip()]
    except Exception:
        return None
    return lines[-n:] if lines else None


def trial_done(arm, trial):
    if S.ARMS[arm]["kind"] == "infer":
        return os.path.exists(trial["eval_json"])
    return os.path.exists(os.path.join(trial["dir"], "DONE"))


def collect(arm, trial, baselines, psd_ceiling, objective_expr, gate_expr):
    m = (metrics_from_eval(trial["eval_json"]) if S.ARMS[arm]["kind"] == "infer"
         else metrics_from_training(trial["dir"]))
    if m is None:
        return None, None, None
    b = (baselines or {}).get(trial["rung"]["name"], {})
    for k, v in b.items():
        m.setdefault(k, v)
    m.setdefault("psd_ceiling", psd_ceiling)
    obj = evaluate_expr(objective_expr, m)
    gate = evaluate_expr(gate_expr, m)
    return m, (float(obj) if isinstance(obj, (int, float)) else None), bool(gate)


def median_prune_check(running, log):
    curves = {}
    for t in running:
        lp = os.path.join(t["dir"], "train_log.json")
        if not os.path.exists(lp):
            continue
        try:
            rec = json.load(open(lp))
        except Exception:
            continue
        curves[t["id"]] = {r["epoch"]: r["val"]["loss_w"] for r in rec if r.get("val")}
    killed = []
    for t in running:
        c = curves.get(t["id"], {})
        if not c:
            continue
        ep = max(c)
        peers = [v[ep] for k, v in curves.items() if k != t["id"] and ep in v]
        if len(peers) < 3:
            continue
        med = sorted(peers)[len(peers) // 2]
        if c[ep] > med:
            log(f"  prune {t['id']}: val {c[ep]:.4f} > median {med:.4f} at epoch {ep}")
            killed.append(t)
    return killed


def plan_table(arm, cells, schedule, throughput, log):
    rows, total = [], 0.0
    for rung, n_keep in schedule:
        per = [S.train_cost_h(arm, rung, c["params"], throughput)
               for c in cells[:n_keep]]
        sub = sum(per)
        total += sub
        rows.append({"rung": rung["name"], "rows": rung["rows"],
                     "epochs": rung["epochs"], "n_trials": len(per),
                     "gpu_h": round(sub, 2),
                     "gpu_h_per_trial": round(sub / max(len(per), 1), 3)})
    full = (sum(S.full_fidelity_cost_h(arm, c["params"], measured=throughput)
                for c in cells) if S.ARMS[arm]["kind"] == "train" else 0.0)
    log("")
    log(f"  {'rung':<6} {'rows':>8} {'epochs':>7} {'trials':>7} {'GPU-h/trial':>12} {'GPU-h':>8}")
    for r in rows:
        log(f"  {r['rung']:<6} {r['rows']:>8} {r['epochs']:>7} {r['n_trials']:>7} "
            f"{r['gpu_h_per_trial']:>12.3f} {r['gpu_h']:>8.2f}")
    log(f"  {'TOTAL':<6} {'':>8} {'':>7} {'':>7} {'':>12} {total:>8.2f}")
    if full:
        log(f"\n  the same {len(cells)} configurations trained to 50 epochs at full "
            f"fidelity: {full:.0f} A100-hours")
        log(f"  multi-fidelity screening cost: {total:.1f} A100-hours "
            f"({100.0 * total / max(full, 1e-9):.1f} percent of that)")
    log("")
    return rows, total, full


def main():
    ap = argparse.ArgumentParser(
        description="Hyperparameter optimisation for the LDM and CorrDiff arms.",
        epilog="Everything after a bare -- is appended verbatim to every trial command.")
    ap.add_argument("--space", required=True, choices=sorted(S.SPACES),
                    help="search space from hpo_spaces.SPACES")
    ap.add_argument("--out", required=True, help="study directory")
    ap.add_argument("--exec", dest="executor", default="dry",
                    choices=["dry", "local", "slurm"],
                    help="dry (default) plans and costs the study without running it")
    ap.add_argument("--sampler", default=None,
                    choices=["grid", "random", "tpe", "optuna-tpe"],
                    help="default: the space's own declared stage")
    ap.add_argument("--n-trials", type=int, default=24,
                    help="number of configurations for random/tpe (grid uses its own size)")
    ap.add_argument("--parallel", type=int, default=1,
                    help="trials in flight at once (the orchid QoS allows 8); "
                         "under --exec local they all share one GPU")
    ap.add_argument("--eta", type=int, default=3,
                    help="successive-halving reduction factor")
    ap.add_argument("--rungs", default=None,
                    help="comma-separated rung names to use, e.g. r0,r1")
    ap.add_argument("--objective", default=None,
                    help="name from hpo_spaces.OBJECTIVES, or a raw expression "
                         "(larger is better)")
    ap.add_argument("--gate", default=None,
                    help="name from hpo_spaces.GATES, or a raw boolean expression")
    ap.add_argument("--psd-ceiling", type=float, default=S.PSD_CEILING_POOLED,
                    help="codec oracle 2-8 km PSD ratio, mean-of-ratios estimator "
                         "(the one psd_ratio_2_8km uses)")
    ap.add_argument("--baselines", default=None,
                    help="baselines.json from hpo_baselines.py (paired persistence)")
    ap.add_argument("--seed", type=int, default=0,
                    help="pinned on every trial so comparisons stay paired")
    ap.add_argument("--sampler-seed", type=int, default=0)
    ap.add_argument("--seed-from", default=None,
                    help="another study directory whose finished trials seed the "
                         "surrogate for a tpe run")
    ap.add_argument("--seed-from-rung", default=None,
                    help="which rung of --seed-from to take observations from "
                         "(default: the cheapest rung)")
    ap.add_argument("--budget-gpu-h", type=float, default=None,
                    help="refuse to launch a study whose plan exceeds this")
    ap.add_argument("--max-trials", type=int, default=None,
                    help="truncate the candidate list; the drop is logged, never silent")
    ap.add_argument("--prune", default="none", choices=["none", "median"])
    ap.add_argument("--poll", type=int, default=60, help="seconds between polls")
    ap.add_argument("--gpu-sbatch", default="~/dissertation/gpu.sbatch")
    ap.add_argument("--sbatch-extra", default="",
                    help="extra sbatch flags, e.g. '--qos=orchid --account=orchid'")
    ap.add_argument("--python", default=None,
                    help="interpreter for trial commands (default: 'python' under "
                         "--exec slurm, sys.executable otherwise)")
    ap.add_argument("--script-dir", default=HERE,
                    help="where the stage scripts live (default: next to this "
                         "file)")
    ap.add_argument("--force", action="store_true",
                    help="launch even if the plan exceeds --budget-gpu-h")
    ap.add_argument("passthrough", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    passthrough = [a for a in args.passthrough if a != "--"]
    if args.python is None:
        args.python = default_python(args.executor)
    space = S.SPACES[args.space]
    arm = space["arm"]
    meta = S.ARMS[arm]
    os.makedirs(args.out, exist_ok=True)
    log = Tee(os.path.join(args.out, "hpo.log"))

    missing = [f for f in meta["required"] if f not in passthrough]
    if missing and args.executor != "dry":
        raise SystemExit(f"ERROR: the {arm} arm requires {', '.join(missing)}; pass "
                         f"them after a bare -- on the command line.")

    bad_args = preflight(passthrough, os.path.join(args.script_dir, meta["script"]))
    if bad_args:
        log("\nPRE-FLIGHT FAILED. Nothing was submitted.")
        for p in bad_args:
            log(f"  - {p}")
        log("\nThe pass-through arguments as this shell expanded them:")
        log("  " + " ".join(shlex.quote(a) for a in passthrough))
        raise SystemExit(1)

    obj_name = args.objective or S.DEFAULT_OBJECTIVE[arm]
    gate_name = args.gate or S.DEFAULT_GATE[arm]
    obj_expr = S.OBJECTIVES.get(obj_name, {}).get("expr", obj_name)
    gate_expr = S.GATES.get(gate_name, {}).get("expr", gate_name)

    rungs = S.RUNGS[arm]
    if args.rungs:
        want = [r.strip() for r in args.rungs.split(",")]
        rungs = [r for r in rungs if r["name"] in want]
        if not rungs:
            raise SystemExit(f"ERROR: --rungs {args.rungs} matched no rung of arm {arm}.")

    sampler_kind = args.sampler or space["stage"]
    baselines = json.load(open(args.baselines)) if args.baselines else None
    if baselines is None and arm != "inference":
        log("WARNING: no --baselines given, so mae_pers and crps_pers will be "
            "undefined in the objective and gate. Run hpo_baselines.py first.")

    spec = {"space": args.space, "arm": arm, "sampler": sampler_kind,
            "objective": obj_name, "objective_expr": obj_expr,
            "gate": gate_name, "gate_expr": gate_expr,
            "rungs": rungs, "eta": args.eta, "seed": args.seed,
            "sampler_seed": args.sampler_seed, "n_trials": args.n_trials,
            "psd_ceiling": args.psd_ceiling, "passthrough": passthrough,
            "executor": args.executor, "parallel": args.parallel,
            "prune": args.prune, "git": git_hash(), "created": now(),
            "space_note": space.get("note"), "reruns": 0,
            "host": os.uname().nodename if hasattr(os, "uname") else "windows"}
    study = Study(args.out, spec, log)

    log(f"\n=== study {args.space} :: arm {arm} :: sampler {sampler_kind} "
        f":: git {spec['git']} ===")
    log(f"objective (maximised): {obj_name} = {obj_expr}")
    log(f"        admissibility: {gate_name} = {gate_expr}")
    log("           rung ladder: " +
        ", ".join(f"{r['name']}({r['rows']}x{r['epochs']})" for r in rungs))

    if sampler_kind == "grid":
        cells = expand_grid(space)
        bad = [c for c in cells if c["invalid"]]
        for c in bad:
            log(f"  SKIP invalid cell {c['origin']}: {'; '.join(c['invalid'])}")
        cells = [c for c in cells if not c["invalid"]]
        sampler = None
    else:
        sampler = {"random": RandomSampler,
                   "tpe": TPESampler,
                   "optuna-tpe": OptunaTPESampler}[sampler_kind](
            space, seed=args.sampler_seed)
        cells = None

    seeded = []
    if args.seed_from:
        rp = os.path.join(args.seed_from, "ranking.json")
        if os.path.exists(rp):
            prev = json.load(open(rp))
            want = args.seed_from_rung or (prev.get("spec", {}).get("rungs")
                                           or [{}])[0].get("name")
            keys = set(space.get("axes", {}))
            skipped = 0
            for r in prev.get("trials", []):
                if r.get("objective") is None:
                    continue
                if want and r.get("rung") != want:
                    skipped += 1
                    continue
                p = {k: v for k, v in (r.get("params") or {}).items() if k in keys}
                if len(p) == len(keys):
                    seeded.append((p, r["objective"]))
            log(f"seeded the surrogate with {len(seeded)} observations from "
                f"{args.seed_from} at rung '{want}' ({skipped} rows at other rungs "
                "ignored so the surrogate sees one fidelity only)")
            if not seeded:
                log("  WARNING: nothing usable was seeded. Check that the earlier "
                    "study's parameters cover every axis of this space.")
        else:
            log(f"WARNING: --seed-from {args.seed_from} has no ranking.json; "
                "starting cold.")

    if cells is None:
        proposals = sampler.ask(args.n_trials, seeded)
        cells = []
        for p in proposals:
            full = dict(S.INCUMBENT)
            full.update(p)
            keys = sorted(set(space["axes"]))
            cell = {k: full[k] for k in keys}
            bad = S.check_constraints(cell)
            cells.append({"params": cell, "origin": sampler.name, "invalid": bad})
        for c in [c for c in cells if c["invalid"]]:
            log(f"  SKIP invalid proposal: {'; '.join(c['invalid'])}")
        cells = [c for c in cells if not c["invalid"]]

    if args.max_trials and len(cells) > args.max_trials:
        log(f"  NOTE: candidate list truncated from {len(cells)} to {args.max_trials} "
            f"by --max-trials. Dropped cells: "
            f"{', '.join(c['origin'] for c in cells[args.max_trials:])}")
        cells = cells[:args.max_trials]

    log(f"\n{len(cells)} candidate configurations")
    for i, c in enumerate(cells):
        diff = {k: v for k, v in c["params"].items() if v != S.INCUMBENT.get(k)}
        log(f"  {i:>3} {c['origin']:<22} " +
            (", ".join(f"{k}={v}" for k, v in sorted(diff.items())) or "(incumbent)"))

    schedule = S.sha_schedule(len(cells), rungs, eta=args.eta)
    rows, total, full = plan_table(arm, cells, schedule, study.throughput, log)

    example = build_cmd(arm, args.script_dir, cells[0]["params"], rungs[0],
                        os.path.join(args.out, "trial_000_" + rungs[0]["name"]),
                        passthrough, args.seed, tag="_trial_000_" + rungs[0]["name"],
                        python=args.python)
    log("example trial command (candidate 0 at rung " + rungs[0]["name"] + "):")
    log("  " + " ".join(shlex.quote(c) for c in example))
    log("")

    atomic_json({"spec": spec, "candidates": cells, "schedule": rows,
                 "gpu_h_planned": round(total, 2),
                 "gpu_h_if_full_fidelity": round(full, 1),
                 "example_cmd": example},
                os.path.join(args.out, "plan.json"))

    if args.budget_gpu_h and total > args.budget_gpu_h and not args.force:
        raise SystemExit(
            f"\nERROR: planned {total:.1f} A100-hours exceeds --budget-gpu-h "
            f"{args.budget_gpu_h}. Reduce --n-trials or --rungs, drop a rung, or "
            "pass --force if the budget figure is the thing that is wrong.")

    if args.executor == "dry":
        log(f"\ndry run: plan written to {os.path.join(args.out, 'plan.json')}. "
            "Re-run with --exec slurm (JASMIN) or --exec local (L4) to execute.")
        return

    if args.executor == "slurm":
        ex = SlurmExecutor(log, args.gpu_sbatch,
                           extra_sbatch=shlex.split(args.sbatch_extra))
    else:
        ex = LocalExecutor(log)

    survivors = list(range(len(cells)))
    ranking = []
    n_finished = n_ok = 0
    for rung, n_keep in schedule:
        survivors = survivors[:n_keep]
        log(f"\n---- rung {rung['name']} ({rung['rows']} rows x {rung['epochs']} "
            f"epochs) :: {len(survivors)} trials ----")
        trials = []
        for idx in survivors:
            params = cells[idx]["params"]
            tid = f"trial_{idx:03d}_{rung['name']}"
            tdir = os.path.join(args.out, tid)
            t = {"id": tid, "index": idx, "rung": rung, "params": params,
                 "dir": tdir, "origin": cells[idx]["origin"],
                 "param_hash": param_hash(params),
                 "job_name": f"hpo-{args.space}-{idx:03d}{rung['name']}",
                 "eval_json": os.path.join(args.out, "eval",
                                           f"diffusion_eval_{tid}.json"),
                 "cost_h_est": S.train_cost_h(arm, rung, params, study.throughput)}
            t["cmd"] = build_cmd(arm, args.script_dir, params, rung, tdir, passthrough,
                                 args.seed, tag=f"_{tid}", python=args.python)
            cp = os.path.join(tdir, "hpo_trial.json")
            if os.path.exists(cp):
                old = json.load(open(cp))
                if old.get("param_hash") != t["param_hash"]:
                    raise SystemExit(
                        f"ERROR: {tdir} was created for a different configuration "
                        f"({old.get('param_hash')} != {t['param_hash']}). The search "
                        "space changed since this study started. Use a new --out.")
            os.makedirs(tdir, exist_ok=True)
            atomic_json({k: t[k] for k in
                         ("id", "index", "params", "param_hash", "origin",
                          "cmd", "cost_h_est")} | {"rung": rung["name"]}, cp)
            trials.append(t)

        pending, resumed = [], []
        for t in trials:
            (resumed if trial_done(arm, t) else pending).append(t)
        for t in resumed:
            log(f"  resume: {t['id']} already has its completion marker, skipping")
            study.event(event="skip", trial=t["id"], rung=rung["name"],
                        params=t["params"])

        inflight, queue = [], list(pending)
        while queue or inflight:
            while queue and len(inflight) < max(1, args.parallel):
                t = queue.pop(0)
                spent = study.spent_gpu_h()
                if args.budget_gpu_h and spent > args.budget_gpu_h and not args.force:
                    log(f"  BUDGET STOP: {spent:.1f} A100-hours already spent, "
                        f"limit {args.budget_gpu_h}. {len(queue) + 1} trials not "
                        "launched; re-run with a higher --budget-gpu-h to continue.")
                    queue = []
                    break
                t["t0"] = time.time()
                study.event(event="launch", trial=t["id"], rung=rung["name"],
                            params=t["params"], cost_h_est=round(t["cost_h_est"], 3),
                            cmd=" ".join(shlex.quote(c) for c in t["cmd"]))
                ex.submit(t)
                inflight.append(t)
            if not inflight:
                break
            time.sleep(args.poll)
            if args.prune == "median" and len(inflight) > 3:
                for t in median_prune_check(inflight, log):
                    ex.kill(t)
                    t["pruned"] = True
                    study.event(event="prune", trial=t["id"], rung=rung["name"])
            still = []
            for t in inflight:
                if ex.poll(t) or t.get("pruned"):
                    m, obj, gate = collect(arm, t, baselines, args.psd_ceiling,
                                           obj_expr, gate_expr)
                    t["metrics"], t["objective"], t["gate_pass"] = m, obj, gate
                    t["wall_min"] = round((time.time() - t["t0"]) / 60.0, 1)
                    study.note_throughput(t["params"], m)
                    ok = trial_done(arm, t)
                    study.event(event="finish", trial=t["id"], rung=rung["name"],
                                params=t["params"], objective=obj, gate_pass=gate,
                                complete=ok, pruned=bool(t.get("pruned")),
                                wall_min=t["wall_min"], jobid=t.get("jobid"),
                                returncode=t.get("returncode"), metrics=m)
                    tag = ("PRUNED" if t.get("pruned") else
                           ("ok" if ok else "INCOMPLETE"))
                    log(f"  {t['id']:<24} {tag:<10} objective "
                        f"{('%.5f' % obj) if obj is not None else '   n/a':>10} "
                        f"gate {'pass' if gate else 'FAIL':<4} "
                        f"{t['wall_min']:.1f} min")
                    if not ok and not t.get("pruned"):
                        for line in (failure_tail(t) or ["(no output captured)"]):
                            log(f"      | {line}")
                    n_finished += 1
                    n_ok += 1 if ok else 0
                else:
                    still.append(t)
            inflight = still
            if n_finished >= 2 and n_ok == 0:
                for u in inflight:
                    ex.kill(u)
                raise SystemExit(
                    f"\nERROR: the first {n_finished} trials produced no metrics, so "
                    "the trial command itself is broken. Its output is above; the "
                    "usual causes are --python, a missing --latents-dir or --mu-dir "
                    "on the compute node, or a missing gpu.sbatch wrapper. Fix it "
                    "and re-run the same command; completed trials are skipped.")

        scored = []
        for t in trials:
            if "objective" not in t:
                m, obj, gate = collect(arm, t, baselines, args.psd_ceiling,
                                       obj_expr, gate_expr)
                t["metrics"], t["objective"], t["gate_pass"] = m, obj, gate
            scored.append(t)
        scored.sort(key=lambda t: (0 if t.get("gate_pass") else 1,
                                   -(t["objective"] if t["objective"] is not None
                                     else -1e300)))
        survivors = [t["index"] for t in scored]
        ranking = [{"rung": rung["name"], "trial": t["id"], "index": t["index"],
                    "origin": t["origin"], "params": t["params"],
                    "objective": t["objective"], "gate_pass": t.get("gate_pass"),
                    "wall_min": t.get("wall_min"), "metrics": t.get("metrics")}
                   for t in scored] + ranking
        atomic_json({"spec": spec, "trials": ranking},
                    os.path.join(args.out, "ranking.json"))
        log(f"  rung {rung['name']} ranking: " +
            ", ".join(f"{t['id'].split('_')[1]}"
                      f"({'%.4f' % t['objective'] if t['objective'] is not None else 'na'})"
                      for t in scored[:6]))

    best = next((r for r in ranking if r["gate_pass"]), ranking[0] if ranking else None)
    if best:
        log(f"\nBEST: {best['trial']}  objective {best['objective']}")
        diff = {k: v for k, v in best["params"].items() if v != S.INCUMBENT.get(k)}
        log("  differs from the incumbent on: " +
            (", ".join(f"{k}={v}" for k, v in sorted(diff.items())) or "nothing"))
        if meta["kind"] == "train":
            full_h = S.full_fidelity_cost_h(arm, best["params"],
                                            measured=study.throughput)
            full_rung = {"name": "full", "rows": meta["n_train_rows"], "epochs": 50,
                         "sample_crops": 16, "psd_crops": 64}
            conf = build_cmd(arm, args.script_dir, best["params"], full_rung,
                             os.path.join(os.path.dirname(args.out.rstrip("/\\")),
                                          f"{args.space}_winner"),
                             passthrough, args.seed, python=args.python)
            conf = [c for c in conf if c != "--no-keep-sampled"]
            if "--limit" in conf:
                i = conf.index("--limit")
                del conf[i:i + 2]
            for a, b in (("--patience", "15"), ("--sample-every", "5")):
                if a in conf:
                    conf[conf.index(a) + 1] = b
            log("\nConfirm the winner at full fidelity before quoting it.")
            log(f"  estimated cost: {full_h:.1f} A100-hours")
            log("  " + " ".join(shlex.quote(c) for c in conf))
            atomic_json({"trial": best["trial"], "params": best["params"],
                         "objective": best["objective"],
                         "full_fidelity_gpu_h": round(full_h, 2),
                         "confirm_cmd": conf},
                        os.path.join(args.out, "winner.json"))
    log(f"\ntotal measured GPU time this study: {study.spent_gpu_h():.2f} hours")
    log(f"next: python hpo_report.py --study {args.out}")


if __name__ == "__main__":
    main()
