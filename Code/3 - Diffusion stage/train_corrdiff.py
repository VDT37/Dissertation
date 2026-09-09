#!/usr/bin/env python3
import os, sys, json, time, math, random, getpass, argparse, contextlib

import numpy as np
import torch
from torch.utils.data import DataLoader

from train_ldm import (ZC, COND_CH, UNet, EDMDenoiser, LatentRows, shard_suffix,
                       load_pack_meta, load_diag_crops, sampled_diagnostics,
                       plot_curves, ema_init, ema_update, ema_weights, git_hash,
                       sha256_file)
from train_vae import VAE, atomic_save, atomic_json

USER    = getpass.getuser()
SCRATCH = os.environ.get("DISS_SCRATCH", f"/work/scratch-nopw2/{USER}/dissertation")
LATENTS = os.path.join(SCRATCH, "latents")
OUT     = os.path.expanduser("~/dissertation_outputs/diffusion_corrdiff_v1")
VAE_CKPT = os.path.expanduser("~/dissertation_outputs/vae_v2/vae_best.pt")


def mu_shard_names(mu_dir, split, lead=None):
    suf = shard_suffix(lead)
    return (os.path.join(mu_dir, f"{split}_mu{suf}.npy"),
            os.path.join(mu_dir, f"{split}_mu{suf}_meta.json"))


def check_mu_shard(mu_dir, latents_dir, split, lead=None, reg_sha=None):
    npy, meta_p = mu_shard_names(mu_dir, split, lead)
    if not os.path.exists(meta_p) or not os.path.exists(npy):
        raise SystemExit(f"ERROR: mu pack {npy} / {meta_p} not found. Run "
                         "pack_mu.py --reg <regression ckpt> first.")
    meta = json.load(open(meta_p))
    lat_meta_p = os.path.join(latents_dir,
                              f"{split}_latents{shard_suffix(lead)}_meta.json")
    lat_meta = load_pack_meta(latents_dir, split, lead)
    tag = f"{split}{shard_suffix(lead)}"
    if meta.get("target") != "delta":
        raise SystemExit(
            f"ERROR: [{tag}] mu pack was built from a regression with target "
            f"'{meta.get('target')}', but the diffusion target is delta - mu_r. "
            "Only a --target delta regression can feed --mu-dir.")
    n_rows = np.load(npy, mmap_mode="r").shape[0]
    if n_rows != lat_meta.get("n_files") or meta.get("n_files") != lat_meta.get("n_files"):
        raise SystemExit(
            f"ERROR: [{tag}] mu pack has {n_rows} rows (meta says "
            f"{meta.get('n_files')}) but the latent shard has "
            f"{lat_meta.get('n_files')}; the mu pack is stale. Re-run pack_mu.py.")
    want = sha256_file(lat_meta_p)
    if meta.get("latents_meta_sha") and meta["latents_meta_sha"] != want:
        raise SystemExit(
            f"ERROR: [{tag}] mu pack was built against a different latent pack "
            f"(meta sha {meta['latents_meta_sha'][:12]} vs {want[:12]}). Re-run "
            "pack_mu.py.")
    if reg_sha and meta.get("reg_sha256") != reg_sha:
        raise SystemExit(
            f"ERROR: [{tag}] mu pack was produced by regression checkpoint "
            f"{str(meta.get('reg_sha256'))[:12]}, not the --reg-sha "
            f"{reg_sha[:12]} given on the command line.")
    return npy, meta


def open_mu_split(mu_dir, latents_dir, split, lead=None, n_rows=None, reg_sha=None):
    npy, meta = check_mu_shard(mu_dir, latents_dir, split, lead, reg_sha)
    mm = np.load(npy, mmap_mode="r")
    if n_rows is not None and mm.shape[0] != n_rows:
        raise SystemExit(f"ERROR: {npy} has {mm.shape[0]} rows but the latent pack "
                         f"has {n_rows}; the mu pack is stale (re-run pack_mu.py).")
    print(f"mu pack: {npy} | reg {str(meta.get('reg_sha256'))[:12]} "
          f"(epoch {meta.get('reg_epoch')}) | shard EV {meta.get('ev')}", flush=True)
    return mm, meta


def pool_moments(metas, key):
    S = sum(m[key]["sum"] for m in metas)
    SS = sum(m[key]["sumsq"] for m in metas)
    N = sum(m[key]["count"] for m in metas)
    var = max(SS / N - (S / N) ** 2, 0.0)
    return float(math.sqrt(var)), var, float(SS / N)


class MuLatentRows(LatentRows):
    def __init__(self, paths, mu_paths, limit=None):
        if isinstance(paths, str):
            paths = [paths]
        paths = list(paths)
        mu_paths = list(mu_paths)
        if len(mu_paths) != len(paths):
            raise SystemExit(f"ERROR: {len(mu_paths)} mu shards for {len(paths)} "
                             "latent shards; they must pair 1:1.")
        for lp, mp in zip(paths, mu_paths):
            if not os.path.exists(mp):
                raise SystemExit(f"ERROR: mu pack {mp} not found (run pack_mu.py).")
            nl = np.load(lp, mmap_mode="r").shape[0]
            nm = np.load(mp, mmap_mode="r").shape[0]
            if nl != nm:
                raise SystemExit(f"ERROR: {mp} has {nm} rows but {lp} has {nl}; "
                                 "the mu pack is stale. Re-run pack_mu.py.")
        super().__init__(paths, limit=limit)
        self.mu_paths = mu_paths
        self._mu = None

    def __getitem__(self, i):
        row, s = super().__getitem__(i)
        if self._mu is None:
            self._mu = [np.load(p, mmap_mode="r") for p in self.mu_paths]
        mu = np.asarray(self._mu[s][int(self.local[i])], dtype="float32")
        return torch.cat([row, torch.from_numpy(mu)], dim=0), s


def corrdiff_loss_terms(denoiser, rows, cond_mode, p_mean, p_std, cond_drop,
                        device, generator=None, lead_idx=None, hr_mean_cond=False):
    z_A = rows[:, 4 * ZC:5 * ZC]
    z_y = rows[:, 5 * ZC:6 * ZC]
    mu = rows[:, 6 * ZC:7 * ZC]
    delta = (z_y - z_A) - mu
    cond = rows[:, :5 * ZC] if cond_mode == "full" else z_A
    if hr_mean_cond:
        cond = torch.cat([cond, mu], dim=1)
    B = rows.shape[0]

    if generator is None:
        n = torch.randn(B, device=device)
        eps = torch.randn_like(delta)
        u = torch.rand(B, device=device)
    else:
        n = torch.randn(B, device=device, generator=generator)
        eps = torch.randn(delta.shape, device=device, generator=generator)
        u = torch.ones(B, device=device)
    sigma = (p_mean + p_std * n).exp().view(B, 1, 1, 1)
    if cond_drop > 0:
        keep = (u >= cond_drop).float().view(B, 1, 1, 1)
        cond = cond * keep

    x = delta + sigma * eps
    D = denoiser(x, sigma, cond, lead_idx)
    sd = denoiser.sigma_data
    w = (sigma ** 2 + sd ** 2) / (sigma * sd) ** 2
    err2 = (D.float() - delta.float()) ** 2
    return (w.float() * err2).mean(), err2.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--warmup", type=int, default=1000, help="lr warmup steps")
    ap.add_argument("--lr-schedule", choices=["cosine", "constant"], default="cosine")
    ap.add_argument("--weight-decay", type=float, default=0.0)
    ap.add_argument("--width", type=int, default=128, help="UNet base channels (div by 8)")
    ap.add_argument("--mults", default="1,2,4", help="channel multipliers per level")
    ap.add_argument("--attn", default="16", help="resolutions with self-attention (csv)")
    ap.add_argument("--dropout", type=float, default=0.0)
    ap.add_argument("--ema-decay", type=float, default=0.999)
    ap.add_argument("--cond-mode", choices=["full", "a-only"], default="full")
    ap.add_argument("--cond-drop", type=float, default=0.1,
                    help="conditioning dropout prob (enables CF guidance; 0 = off)")
    ap.add_argument("--p-mean", type=float, default=-1.2)
    ap.add_argument("--p-std", type=float, default=1.2)
    ap.add_argument("--mu-dir", required=True,
                    help="directory of {split}_mu{_LNN}.npy packs from pack_mu.py. "
                         "Required: without a frozen mean this is train_ldm.py.")
    ap.add_argument("--hr-mean-cond", choices=["on", "off"], default="on",
                    help="concatenate mu_r as 4 extra conditioning channels "
                         "(24 -> 28 input channels); off = the mean enters "
                         "only through the target")
    ap.add_argument("--reg-sha", default=None,
                    help="assert the mu pack was produced by this regression "
                         "checkpoint sha256; a mismatch is fatal")
    ap.add_argument("--sigma-data", type=float, default=None,
                    help="override; by default pooled from the mu pack's "
                         "resid_moments, never copied from the plain arm")
    ap.add_argument("--sample-every", type=int, default=5,
                    help="epochs between sampled diagnostics (0 = off)")
    ap.add_argument("--sample-steps", type=int, default=25)
    ap.add_argument("--sample-members", type=int, default=8)
    ap.add_argument("--sample-crops", type=int, default=16)
    ap.add_argument("--sample-batch", type=int, default=128)
    ap.add_argument("--no-keep-sampled", dest="keep_sampled", action="store_false",
                    help="do not archive EMA weights as ckpt_epNNN.pt at each "
                         "sampled epoch")
    ap.add_argument("--psd-crops", type=int, default=64)
    ap.add_argument("--guidance", type=float, default=1.0)
    ap.add_argument("--churn", type=float, default=0.0)
    ap.add_argument("--patience", type=int, default=0,
                    help="0 = never early stop")
    ap.add_argument("--limit", type=int, default=None, help="cap rows")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--leads", default=None, help="e.g. 15,30,45,60")
    ap.add_argument("--latents-dir", default=LATENTS)
    ap.add_argument("--vae", default=VAE_CKPT, help="codec ckpt (diagnostics decode)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--resume", default=None,
                    help="path to diff_last.pt, or 'auto' to pick it up from --out")
    ap.add_argument("--ignore-done", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    done_p = os.path.join(args.out, "DONE")
    if os.path.exists(done_p) and not args.ignore_done:
        print(f"DONE marker exists ({done_p}); nothing to do. "
              "Use --ignore-done to force.", flush=True)
        return

    torch.manual_seed(args.seed); random.seed(args.seed); np.random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.backends.cudnn.benchmark = True
    else:
        print("WARNING: no GPU found, running on CPU (very slow)", flush=True)

    leads = ([int(x) for x in args.leads.split(",") if x.strip()]
             if args.leads else None)
    shard_leads = leads if leads else [None]

    resume_path = args.resume
    if resume_path == "auto":
        cand = os.path.join(args.out, "diff_last.pt")
        resume_path = cand if os.path.exists(cand) else None
        print(f"resume auto: {'found ' + cand if resume_path else 'fresh start'}",
              flush=True)
    resume_ck = torch.load(resume_path, map_location="cpu") if resume_path else None
    if resume_ck is not None:
        rc = resume_ck["config"]
        if not rc.get("mu_dir"):
            raise SystemExit(
                f"ERROR: {resume_path} was written by train_ldm.py (no mu_dir in "
                "its config). Resuming a plain LDM run as a CorrDiff run would "
                "change the target mid-run. Use train_ldm.py, or start a fresh "
                "CorrDiff run with a new --out.")
        for k in ("width", "mults", "attn", "cond_mode", "dropout", "cond_drop",
                  "ema_decay", "p_mean", "p_std", "mu_dir", "hr_mean_cond"):
            if rc[k] != getattr(args, k):
                print(f"resume: overriding --{k.replace('_', '-')} "
                      f"{getattr(args, k)} -> {rc[k]} (from checkpoint)", flush=True)
            setattr(args, k, rc[k])
        if rc.get("leads") != leads:
            raise SystemExit(
                f"ERROR: checkpoint was trained with leads {rc.get('leads')} but "
                f"--leads gives {leads}. Resuming would change the lead embedding.")

    tr_metas = [load_pack_meta(args.latents_dir, "train", L) for L in shard_leads]
    va_metas = [load_pack_meta(args.latents_dir, "val", L) for L in shard_leads]
    tr_meta = tr_metas[0]
    if tr_meta.get("zc") != ZC:
        raise SystemExit(f"ERROR: pack zc={tr_meta.get('zc')} but trainer ZC={ZC}.")
    shas = {m.get("vae_sha256") for m in tr_metas + va_metas}
    if len(shas) != 1:
        raise SystemExit("ERROR: the latent packs were encoded with different VAE "
                         "checkpoints; re-run pack_latents.py.")
    latent_scale = float(tr_meta["latent_scale"])
    mean, std = float(tr_meta["norm"]["mean"]), float(tr_meta["norm"]["std"])

    mu_tr = [check_mu_shard(args.mu_dir, args.latents_dir, "train", L, args.reg_sha)
             for L in shard_leads]
    mu_va = [check_mu_shard(args.mu_dir, args.latents_dir, "val", L, args.reg_sha)
             for L in shard_leads]
    mu_tr_paths = [p for p, _ in mu_tr]
    mu_va_paths = [p for p, _ in mu_va]
    mu_tr_metas = [m for _, m in mu_tr]
    reg_shas = {m.get("reg_sha256") for m in mu_tr_metas + [m for _, m in mu_va]}
    if len(reg_shas) != 1:
        raise SystemExit("ERROR: the mu shards were produced by different "
                         "regression checkpoints; re-run pack_mu.py so every "
                         "shard and split shares one frozen mean.")
    reg_sha256 = reg_shas.pop()
    sigma_data_resid, var_r, sq_r = pool_moments(mu_tr_metas, "resid_moments")
    sd_delta, var_d, sq_d = pool_moments(tr_metas, "delta_moments")
    ev_pack = float(1.0 - sq_r / sq_d) if sq_d > 0 else float("nan")
    ev_pack_var = float(1.0 - var_r / var_d) if var_d > 0 else float("nan")
    per = ", ".join(f"+{L}min sd' {float(m['sigma_data_resid']):.4f}/EV {float(m['ev']):.3f}"
                    for L, m in zip(shard_leads, mu_tr_metas))
    print(f"CorrDiff: mu packs from {args.mu_dir} (reg {str(reg_sha256)[:12]})\n"
          f"  pooled sigma_data_resid {sigma_data_resid:.4f} "
          f"(delta was {sd_delta:.4f}, pooled EV {ev_pack:.4f}) from [{per}]",
          flush=True)

    sigma_data = args.sigma_data if args.sigma_data else sigma_data_resid
    if resume_ck is not None:
        sigma_data = resume_ck["config"]["sigma_data"]
    if not (0.02 <= sigma_data <= 2.0):
        raise SystemExit(f"ERROR: sigma_data={sigma_data:.4f} looks wrong; check "
                         "the mu pack's resid_moments.")

    tr_paths = [os.path.join(args.latents_dir, f"train_latents{shard_suffix(L)}.npy")
                for L in shard_leads]
    va_paths = [os.path.join(args.latents_dir, f"val_latents{shard_suffix(L)}.npy")
                for L in shard_leads]
    tr_ds = MuLatentRows(tr_paths, mu_tr_paths, limit=args.limit)
    va_ds = MuLatentRows(va_paths, mu_va_paths,
                         limit=max(400, args.limit // 10) if args.limit else None)
    dl_kw = dict(num_workers=args.workers, pin_memory=True,
                 persistent_workers=args.workers > 0,
                 prefetch_factor=4 if args.workers > 0 else None)
    dl_tr = DataLoader(tr_ds, batch_size=args.batch, shuffle=True, drop_last=True, **dl_kw)
    dl_va = DataLoader(va_ds, batch_size=args.batch, shuffle=False, **dl_kw)
    nsteps = len(dl_tr)
    if nsteps == 0:
        raise SystemExit("ERROR: no training batches (check --limit / --batch).")

    mults = tuple(int(m) for m in args.mults.split(","))
    attn_res = tuple(int(r) for r in args.attn.split(",") if r.strip())
    hr_mean_cond = args.hr_mean_cond == "on"
    cond_ch = COND_CH[args.cond_mode] + (ZC if hr_mean_cond else 0)
    n_leads = len(leads) if leads else 0
    unet = UNet(in_ch=ZC + cond_ch, out_ch=ZC, width=args.width, mults=mults,
                dropout=args.dropout, attn_res=attn_res, n_leads=n_leads)
    denoiser = EDMDenoiser(unet, sigma_data).to(device)
    n_par = sum(p.numel() for p in denoiser.parameters())
    opt = torch.optim.AdamW(denoiser.parameters(), lr=args.lr,
                            betas=(0.9, 0.999), weight_decay=args.weight_decay)
    ema = ema_init(denoiser)

    use_amp = device == "cuda"
    def amp():
        return (torch.autocast("cuda", dtype=torch.bfloat16) if use_amp
                else contextlib.nullcontext())

    total_steps = args.epochs * nsteps
    def lr_at(step):
        base = args.lr * min(step / max(args.warmup, 1), 1.0)
        if args.lr_schedule == "constant" or step < args.warmup:
            return base
        t = min((step - args.warmup) / max(total_steps - args.warmup, 1), 1.0)
        return args.lr * 0.5 * (1.0 + math.cos(math.pi * t))

    vae = None
    diag = cond_diag = anchor_diag = lead_diag = None
    if args.sample_every > 0:
        if not os.path.exists(args.vae):
            print(f"WARNING: --vae {args.vae} not found; sampled diagnostics "
                  "disabled.", flush=True)
            args.sample_every = 0
        else:
            vsha = sha256_file(args.vae)
            if tr_meta.get("vae_sha256") and vsha != tr_meta["vae_sha256"]:
                raise SystemExit(
                    f"ERROR: --vae {args.vae} (sha {vsha[:12]}) is not the "
                    f"checkpoint that produced the latent pack "
                    f"(sha {tr_meta['vae_sha256'][:12]}).")
            vck = torch.load(args.vae, map_location=device)
            vae = VAE(w=vck["config"]["width"], zc=vck["config"]["zc"]).to(device)
            vae.load_state_dict(vck["model"])
            vae.eval()
            diag, rows_diag, diag_idx, lead_diag = load_diag_crops(
                args.latents_dir, va_ds, args.sample_crops, leads)
            if diag is None:
                args.sample_every = 0
            else:
                mu_diag = rows_diag[:, 6 * ZC:7 * ZC]
                cond_diag = rows_diag[:, :5 * ZC] if args.cond_mode == "full" \
                    else rows_diag[:, 4 * ZC:5 * ZC]
                if hr_mean_cond:
                    cond_diag = torch.cat([cond_diag, mu_diag], dim=1)
                anchor_diag = rows_diag[:, 4 * ZC:5 * ZC] + mu_diag
                if not leads:
                    lead_diag = None
                print(f"diagnostics: {len(diag)} fixed val crops "
                      f"(rows {diag_idx[0]}..{diag_idx[-1]}), "
                      f"{args.sample_members} members, {args.sample_steps} steps",
                      flush=True)

    start_ep, best, best_ep, global_step = 1, float("inf"), 0, 0
    log = []
    if resume_ck is not None:
        denoiser.load_state_dict(resume_ck["model"])
        opt.load_state_dict(resume_ck["opt"])
        ema = {k: v.float().to(device) for k, v in resume_ck["ema"].items()}
        start_ep = resume_ck["epoch"] + 1
        best, best_ep = resume_ck.get("best", float("inf")), resume_ck.get("best_ep", 0)
        global_step = resume_ck.get("global_step", (start_ep - 1) * nsteps)
        lp = os.path.join(args.out, "train_log.json")
        if os.path.exists(lp):
            log = json.load(open(lp))
        print(f"resumed at epoch {start_ep} (best {best:.4f} @ ep{best_ep})", flush=True)

    best_disk = None
    bp0 = os.path.join(args.out, "diff_best.pt")
    if os.path.exists(bp0):
        try:
            best_disk = torch.load(bp0, map_location="cpu").get("val_loss")
        except Exception:
            best_disk = None

    config = {"width": args.width, "mults": args.mults, "attn": args.attn,
              "leads": leads,
              "dropout": args.dropout, "cond_mode": args.cond_mode,
              "cond_drop": args.cond_drop, "lr": args.lr, "warmup": args.warmup,
              "lr_schedule": args.lr_schedule, "batch": args.batch,
              "weight_decay": args.weight_decay, "ema_decay": args.ema_decay,
              "p_mean": args.p_mean, "p_std": args.p_std,
              "sigma_data": sigma_data, "latent_scale": latent_scale,
              "norm": {"mean": mean, "std": std}, "seed": args.seed,
              "epochs": args.epochs, "limit": args.limit,
              "trainer": "train_corrdiff.py",
              "mu_dir": os.path.abspath(args.mu_dir),
              "hr_mean_cond": args.hr_mean_cond,
              "reg_sha256": reg_sha256,
              "sigma_data_resid": sigma_data_resid,
              "sigma_data_delta": sd_delta,
              "ev": ev_pack, "ev_var": ev_pack_var,
              "in_ch": ZC + cond_ch,
              "vae_sha256": tr_meta.get("vae_sha256"), "git": git_hash(),
              "argv": sys.argv,
              "n_train": len(tr_ds), "n_val": len(va_ds), "n_params": n_par}
    atomic_json(config, os.path.join(args.out, "config.json"))
    with open(os.path.join(args.out, "runs.jsonl"), "a") as fh:
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                             "event": "start", "resumed_from_epoch": start_ep - 1,
                             "config": config}) + "\n")
    print(f"device={device} | denoiser {n_par/1e6:.1f}M params | "
          f"cond={args.cond_mode} ({cond_ch}ch) | in_ch={ZC + cond_ch} | "
          f"sigma_data={sigma_data:.4f} | latent_scale={latent_scale:.3f} | "
          f"target r' = delta - mu_r, hr_mean_cond={args.hr_mean_cond}", flush=True)
    print(f"train rows {len(tr_ds)} | val rows {len(va_ds)} | {nsteps} steps/epoch "
          f"(batch {args.batch}) | weighted loss starts near 1.0 by construction",
          flush=True)
    if device == "cuda":
        p = torch.cuda.get_device_properties(0)
        print(f"GPU: {p.name} | {p.total_memory/1e9:.0f} GB total", flush=True)

    log_every = min(200, max(10, nsteps // 5))

    def ckpt_last():
        return {"model": denoiser.state_dict(),
                "ema": {k: v.cpu() for k, v in ema.items()},
                "opt": opt.state_dict(), "epoch": ep, "global_step": global_step,
                "best": best, "best_ep": best_ep, "config": config}

    def ckpt_best():
        return {"model": {k: v.cpu() for k, v in ema.items()},
                "config": config, "epoch": ep, "val_loss": best,
                "sigma_data": sigma_data, "latent_scale": latent_scale,
                "norm": {"mean": mean, "std": std}, "cond_mode": args.cond_mode}

    t_all = time.time()
    reason = "completed"
    ep = start_ep - 1
    if start_ep > args.epochs:
        print(f"resume: checkpoint is already at epoch {start_ep - 1} >= "
              f"--epochs {args.epochs}; nothing to train, writing DONE.", flush=True)
        reason = "already-complete"
    for ep in range(start_ep, args.epochs + 1):
        denoiser.train()
        sums = {"loss_w": 0.0, "loss_raw": 0.0, "gn": 0.0}
        seen, t0 = 0, time.time()
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()

        for i, (rows, lead_b) in enumerate(dl_tr, 1):
            rows = rows.to(device, non_blocking=True)
            lead_b = lead_b.to(device, non_blocking=True).long() if leads else None
            lr = lr_at(global_step)
            for gparam in opt.param_groups:
                gparam["lr"] = lr
            with amp():
                loss_w, loss_raw = corrdiff_loss_terms(
                    denoiser, rows, args.cond_mode, args.p_mean, args.p_std,
                    args.cond_drop, device, lead_idx=lead_b,
                    hr_mean_cond=hr_mean_cond)
            opt.zero_grad(set_to_none=True)
            loss_w.backward()
            gn = torch.nn.utils.clip_grad_norm_(denoiser.parameters(), 1.0)
            opt.step()
            ema_update(ema, denoiser, args.ema_decay)

            sums["loss_w"] += loss_w.item()
            sums["loss_raw"] += loss_raw.item()
            sums["gn"] += float(gn)
            seen += rows.size(0); global_step += 1
            if i % log_every == 0:
                ips = seen / (time.time() - t0)
                print(f"  ep{ep} step {i}/{nsteps} | loss_w {sums['loss_w']/i:.4f} "
                      f"raw {sums['loss_raw']/i:.4f} | lr {lr:.2e} "
                      f"| gn {sums['gn']/i:.2f} | {ips:.0f} img/s", flush=True)
        dt = time.time() - t0

        denoiser.eval()
        vl_w = vl_raw = 0.0
        sampled = None
        with ema_weights(denoiser, ema):
            g = torch.Generator(device=device).manual_seed(1234)
            with torch.no_grad():
                for rows, lead_b in dl_va:
                    rows = rows.to(device, non_blocking=True)
                    lead_b = lead_b.to(device, non_blocking=True).long() if leads else None
                    with amp():
                        lw, lraw = corrdiff_loss_terms(
                            denoiser, rows, args.cond_mode, args.p_mean, args.p_std,
                            0.0, device, generator=g, lead_idx=lead_b,
                            hr_mean_cond=hr_mean_cond)
                    vl_w += lw.item(); vl_raw += lraw.item()
            vl_w /= max(len(dl_va), 1); vl_raw /= max(len(dl_va), 1)
            if args.sample_every > 0 and (ep % args.sample_every == 0 or ep == args.epochs):
                sampled = sampled_diagnostics(
                    denoiser, vae, diag, cond_diag, anchor_diag, latent_scale,
                    mean, std, device, args,
                    os.path.join(args.out, f"samples_ep{ep:03d}.png"),
                    lead_diag=lead_diag)
        if not math.isfinite(vl_w):
            raise SystemExit(f"ERROR: validation loss is not finite at epoch {ep}; "
                             "training diverged. Resume from diff_last.pt with a "
                             "lower --lr.")

        gpu = torch.cuda.max_memory_allocated() / 1e9 if device == "cuda" else 0.0
        rec = {"epoch": ep,
               "train": {"loss_w": sums["loss_w"] / nsteps,
                         "loss_raw": sums["loss_raw"] / nsteps,
                         "grad_norm": sums["gn"] / nsteps, "lr": lr},
               "val": {"loss_w": vl_w, "loss_raw": vl_raw},
               "sampled": sampled,
               "sys": {"epoch_sec": round(dt, 1), "gpu_gb": round(gpu, 2),
                       "imgs_per_s": round(seen / dt, 1)}}
        log.append(rec)
        msg = (f"epoch {ep:3d}/{args.epochs} | train {rec['train']['loss_w']:.4f} "
               f"| val {vl_w:.4f} (raw {vl_raw:.4f}) | {dt:.0f}s "
               f"| {rec['sys']['imgs_per_s']:.0f} img/s | GPU {gpu:.1f} GB")
        if sampled:
            msg += (f"\n  sampled: MAE {sampled['mae']:.3f} (adv {sampled['mae_adv']:.3f}) "
                    f"| CSI@1 {sampled['csi_1']:.3f} (adv {sampled['csi_1_adv']:.3f}) "
                    f"| CSI@8 {sampled['csi_8']:.3f} (adv {sampled['csi_8_adv']:.3f}) "
                    f"| CRPS {sampled['crps']:.3f} (adv {sampled['crps_adv']:.3f}) "
                    f"| PSD 2-8km {sampled['psd_ratio_2_8km']:.2f}")
            if ep == 5:
                ratio = sampled["mae"] / max(sampled["mae_adv"], 1e-9)
                bad = ratio > 1.012 or vl_w > 0.95
                msg += (f"\n  ABORT-E ({'FAIL' if bad else 'PASS'}) at epoch 5: "
                        f"MAE/advection {ratio:.4f} against 1.012, weighted val "
                        f"loss {vl_w:.4f} against 0.95")
        print(msg, flush=True)

        if vl_w < best:
            best, best_ep = vl_w, ep
            if best_disk is None or vl_w < best_disk:
                atomic_save(ckpt_best(), os.path.join(args.out, "diff_best.pt"))
                best_disk = vl_w
                print(f"  new best (val loss_w {best:.4f}) -> diff_best.pt", flush=True)
            else:
                print(f"  val improved ({vl_w:.4f}) but diff_best.pt already holds "
                      f"{best_disk:.4f} (from a run killed mid-save); kept", flush=True)
        if sampled and args.keep_sampled:
            ck = ckpt_best()
            ck["val_loss"] = vl_w
            ck["sampled"] = sampled
            atomic_save(ck, os.path.join(args.out, f"ckpt_ep{ep:03d}.pt"))
        atomic_save(ckpt_last(), os.path.join(args.out, "diff_last.pt"))
        atomic_json(log, os.path.join(args.out, "train_log.json"))
        plot_curves(log, os.path.join(args.out, "curves.png"))

        if args.patience and ep - best_ep >= args.patience:
            print(f"early stop: no improvement for {args.patience} epochs "
                  f"(best ep{best_ep}, val loss_w {best:.4f})", flush=True)
            reason = "early-stop"
            break

    wall_min = (time.time() - t_all) / 60
    summary = {"reason": reason, "epochs_run": ep, "best": best, "best_ep": best_ep,
               "wall_min": round(wall_min, 1),
               "sigma_data": sigma_data, "ev": ev_pack, "reg_sha256": reg_sha256,
               "last_sampled": next((r["sampled"] for r in reversed(log)
                                     if r.get("sampled")), None)}
    atomic_json({**summary, "config": config}, done_p)
    with open(os.path.join(args.out, "runs.jsonl"), "a") as fh:
        fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                             "event": "finish", **summary, "config": config}) + "\n")
    print(f"\n{reason}: total {wall_min:.1f} min | best val loss_w {best:.4f} "
          f"(ep{best_ep}) | DONE written -> the sbatch chain will stop", flush=True)


if __name__ == "__main__":
    main()
