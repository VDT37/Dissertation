#!/usr/bin/env python3
import math


ARMS = {
    "ldm": {
        "script": "train_ldm.py",
        "kind": "train",
        "out_flag": "--out",
        "required": [],
        "n_train_rows": 613892,
        "note": "residual LDM: learns delta = z_y - z_A. The ml_v2 arm.",
    },
    "corrdiff": {
        "script": "train_corrdiff.py",
        "kind": "train",
        "out_flag": "--out",
        "required": ["--mu-dir"],
        "n_train_rows": 613892,
        "note": "CorrDiff stage two: learns r' = delta - mu_r on the frozen mu pack.",
    },
    "regression": {
        "script": "train_regression.py",
        "kind": "train",
        "out_flag": "--out",
        "required": [],
        "n_train_rows": 613892,
        "note": "CorrDiff stage one: deterministic conditional mean of the residual.",
    },
    "inference": {
        "script": "evaluate.py",
        "kind": "infer",
        "out_flag": "--out",
        "required": ["--ckpt"],
        "n_train_rows": 0,
        "note": "sampler-only sweep on a frozen checkpoint; no training cost.",
    },
}


PARAMS = {
    "lr":            {"flag": "--lr",            "type": "logfloat", "incumbent": 1e-4,
                      "brief": "learning rate"},
    "batch":         {"flag": "--batch",         "type": "int",      "incumbent": 64,
                      "brief": "batch size"},
    "width":         {"flag": "--width",         "type": "int",      "incumbent": 128,
                      "brief": "UNet width"},
    "mults":         {"flag": "--mults",         "type": "cat",      "incumbent": "1,2,4",
                      "brief": "UNet depth"},
    "attn":          {"flag": "--attn",          "type": "cat",      "incumbent": "16",
                      "brief": "UNet attention resolutions"},
    "dropout":       {"flag": "--dropout",       "type": "float",    "incumbent": 0.0,
                      "brief": "dropout"},
    "weight_decay":  {"flag": "--weight-decay",  "type": "logfloat", "incumbent": 0.0,
                      "brief": "weight decay"},
    "p_mean":        {"flag": "--p-mean",        "type": "float",    "incumbent": -1.2,
                      "brief": "noise schedule (EDM log-sigma mean)"},
    "p_std":         {"flag": "--p-std",         "type": "float",    "incumbent": 1.2,
                      "brief": "noise schedule (EDM log-sigma std)"},
    "cond_mode":     {"flag": "--cond-mode",     "type": "cat",      "incumbent": "full",
                      "brief": "conditioning method"},
    "cond_drop":     {"flag": "--cond-drop",     "type": "float",    "incumbent": 0.1,
                      "brief": "conditioning method (CFG dropout rate)"},
    "ema_decay":     {"flag": "--ema-decay",     "type": "cat",      "incumbent": 0.999,
                      "brief": "EMA horizon"},
    "lr_schedule":   {"flag": "--lr-schedule",   "type": "cat",      "incumbent": "cosine",
                      "brief": "learning rate schedule"},
    "warmup":        {"flag": "--warmup",        "type": "int",      "incumbent": 1000,
                      "brief": "learning rate warmup"},
    "hr_mean_cond":  {"flag": "--hr-mean-cond",  "type": "cat",      "incumbent": "on",
                      "brief": "conditioning method (mu_r in the conditioning stack)"},
    "target":        {"flag": "--target",        "type": "cat",      "incumbent": "delta",
                      "brief": "regression target"},
    "steps":         {"flag": "--steps",         "type": "int",      "incumbent": 25,
                      "brief": "number of diffusion steps"},
    "members":       {"flag": "--members",       "type": "int",      "incumbent": 8,
                      "brief": "ensemble size"},
    "guidance":      {"flag": "--guidance",      "type": "float",    "incumbent": 1.0,
                      "brief": "classifier-free guidance weight"},
    "churn":         {"flag": "--churn",         "type": "float",    "incumbent": 0.0,
                      "brief": "noise schedule (sampler stochasticity S_churn)"},
}

INCUMBENT = {k: v["incumbent"] for k, v in PARAMS.items()}


def n_levels(mults):
    return len(str(mults).split(","))


def valid_attn(attn, mults):
    if attn in ("", None):
        return True
    lo = 64 // (2 ** (n_levels(mults) - 1))
    return all(int(r) >= lo and int(r) <= 64 and (64 % int(r) == 0)
               for r in str(attn).split(","))


def check_constraints(params):
    bad = []
    w = params.get("width", INCUMBENT["width"])
    if int(w) % 8 != 0:
        bad.append(f"width {w} is not divisible by 8 (GroupNorm assertion)")
    if not valid_attn(params.get("attn", INCUMBENT["attn"]),
                      params.get("mults", INCUMBENT["mults"])):
        bad.append(f"attn {params.get('attn')} unreachable with mults "
                   f"{params.get('mults')} (deepest resolution is "
                   f"{64 // 2 ** (n_levels(params.get('mults', INCUMBENT['mults'])) - 1)})")
    if float(params.get("cond_drop", 0.1)) > 0 and \
            params.get("cond_mode", "full") == "a-only" and \
            float(params.get("cond_drop", 0.1)) >= 0.5:
        bad.append("cond_drop >= 0.5 with cond-mode a-only drops almost all signal")
    return bad


RUNGS = {
    "ldm": [
        {"name": "r0", "rows": 60000,  "epochs": 3, "sample_crops": 96, "psd_crops": 96},
        {"name": "r1", "rows": 150000, "epochs": 4, "sample_crops": 96, "psd_crops": 96},
        {"name": "r2", "rows": 613892, "epochs": 6, "sample_crops": 128, "psd_crops": 128},
    ],
    "corrdiff": [
        {"name": "r0", "rows": 60000,  "epochs": 3, "sample_crops": 96, "psd_crops": 96},
        {"name": "r1", "rows": 150000, "epochs": 4, "sample_crops": 96, "psd_crops": 96},
        {"name": "r2", "rows": 613892, "epochs": 6, "sample_crops": 128, "psd_crops": 128},
    ],
    "regression": [
        {"name": "r0", "rows": 60000,  "epochs": 2, "sample_crops": 96, "psd_crops": 96},
        {"name": "r1", "rows": 200000, "epochs": 3, "sample_crops": 96, "psd_crops": 96},
    ],
    "inference": [
        {"name": "r0", "rows": 3000, "epochs": 0, "sample_crops": 0, "psd_crops": 0},
    ],
}


def rung_flags(arm, rung, params):
    rows = rung["rows"]
    if ARMS[arm]["kind"] == "infer":
        return {"--limit": rows}
    batch = int(params.get("batch", INCUMBENT["batch"]))
    steps_per_epoch = max(1, rows // batch)
    total_steps = steps_per_epoch * rung["epochs"]
    warmup = int(min(1000, max(50, round(0.10 * total_steps))))
    out = {
        "--limit": rows,
        "--epochs": rung["epochs"],
        "--warmup": warmup,
        "--psd-crops": rung["psd_crops"],
        "--patience": 0,
        "--no-keep-sampled": True,
    }
    if arm == "regression":
        out["--diag-every"] = rung["epochs"]
        out["--diag-crops"] = rung["sample_crops"]
    else:
        out["--sample-every"] = rung["epochs"]
        out["--sample-crops"] = rung["sample_crops"]
    return out


ANCHOR_IMGS_PER_S = 326.0
ANCHOR_WIDTH = 128
ANCHOR_MULTS = "1,2,4"
ANCHOR_BATCH = 64
ANCHOR_EVAL_MIN = 195.8
ANCHOR_EVAL_CROPS = 13281
ANCHOR_EVAL_MEMBERS = 8
ANCHOR_EVAL_STEPS = 25


def _depth_factor(mults):
    ms = [float(m) for m in str(mults).split(",")]
    s = sum(m * m / (4.0 ** l) for l, m in enumerate(ms))
    anchor = sum(m * m / (4.0 ** l)
                 for l, m in enumerate(float(x) for x in ANCHOR_MULTS.split(",")))
    return s / anchor


def _attn_factor(attn):
    if attn in ("", None):
        return 0.96
    f = 1.0
    for r in str(attn).split(","):
        r = int(r)
        if r >= 64:
            f += 4.0
        elif r >= 32:
            f += 0.45
        elif r >= 16:
            f += 0.0
        else:
            f += 0.02
    return f


def _batch_factor(batch):
    b = float(batch)
    if b >= ANCHOR_BATCH:
        return 0.97 if b > ANCHOR_BATCH else 1.0
    return 1.0 + 0.25 * max(0.0, math.log2(ANCHOR_BATCH / b))


def arch_signature(params):
    return "|".join(str(params.get(k, INCUMBENT[k]))
                    for k in ("width", "mults", "attn", "batch"))


def imgs_per_s(params, measured=None):
    if measured:
        hit = measured.get(arch_signature(params))
        if hit:
            return float(hit)
    w = float(params.get("width", INCUMBENT["width"]))
    factor = ((w / ANCHOR_WIDTH) ** 2
              * _depth_factor(params.get("mults", INCUMBENT["mults"]))
              * _attn_factor(params.get("attn", INCUMBENT["attn"]))
              * _batch_factor(params.get("batch", INCUMBENT["batch"])))
    return ANCHOR_IMGS_PER_S / max(factor, 1e-6)


def train_cost_h(arm, rung, params, measured=None):
    if ARMS[arm]["kind"] == "infer":
        return infer_cost_h(params, n_crops=rung["rows"])
    rows, epochs = rung["rows"], rung["epochs"]
    ips = imgs_per_s(params, measured)
    train_s = rows * epochs / max(ips, 1.0)
    K = rung.get("sample_crops", 0)
    if arm == "regression":
        samp_s = (K / max(ips, 1.0)) if K else 0.0
    else:
        samp_s = (K * 8 * (2 * 25 - 1) / max(ips, 1.0)) if K else 0.0
    val_s = epochs * max(400, rows // 10) / max(ips * 3.0, 1.0)
    return (train_s + samp_s + val_s) / 3600.0


def infer_cost_h(params, n_crops):
    M = float(params.get("members", INCUMBENT["members"]))
    S = float(params.get("steps", INCUMBENT["steps"]))
    g = float(params.get("guidance", INCUMBENT["guidance"]))
    minutes = (ANCHOR_EVAL_MIN
               * (float(n_crops) / ANCHOR_EVAL_CROPS)
               * (M / ANCHOR_EVAL_MEMBERS)
               * ((2 * S - 1) / (2 * ANCHOR_EVAL_STEPS - 1))
               * (2.0 if g > 1.0 else 1.0))
    return minutes / 60.0


def full_fidelity_cost_h(arm, params, epochs=50, measured=None):
    rung = {"rows": ARMS[arm]["n_train_rows"], "epochs": epochs,
            "sample_crops": 16, "psd_crops": 64}
    return train_cost_h(arm, rung, params, measured)


SPACES = {

    "ldm_coarse": {
        "arm": "ldm",
        "stage": "grid",
        "design": "ofat+blocks",
        "note": ("Stage 1 coarse screen, one factor at a time around the ml_v2 "
                 "incumbent, plus two small cartesian blocks where an interaction "
                 "is expected on physical grounds."),
        "blocks": [
            {"name": "lr_x_batch", "design": "cartesian",
             "axes": {"lr": [5e-5, 1e-4, 2e-4], "batch": [32, 64, 128]}},
            {"name": "conditioning", "design": "cartesian",
             "axes": {"cond_mode": ["full", "a-only"], "cond_drop": [0.0, 0.1, 0.2]}},
        ],
        "axes": {
            "width":        [96, 128, 192],
            "mults":        ["1,2,4", "1,2,2,4"],
            "attn":         ["16", "16,32"],
            "dropout":      [0.0, 0.05, 0.10],
            "weight_decay": [0.0, 1e-4, 1e-2],
            "p_mean":       [-1.6, -1.2, -0.81],
            "p_std":        [1.2, 1.6],
        },
    },

    "ldm_refine": {
        "arm": "ldm",
        "stage": "tpe",
        "design": "sampled",
        "note": ("Stage 2 Bayesian refinement. Tree-structured Parzen estimator "
                 "over the continuous axes only, seeded with every stage 1 trial "
                 "so the surrogate starts from real observations rather than cold."),
        "axes": {
            "lr":           {"type": "logfloat", "low": 3e-5, "high": 4e-4},
            "width":        {"type": "int",      "low": 96,  "high": 192, "step": 32},
            "dropout":      {"type": "float",    "low": 0.0, "high": 0.15},
            "weight_decay": {"type": "logfloat", "low": 1e-6, "high": 3e-2,
                             "allow_zero": True},
            "p_mean":       {"type": "float",    "low": -2.0, "high": -0.6},
            "p_std":        {"type": "float",    "low": 1.0,  "high": 1.8},
            "cond_drop":    {"type": "float",    "low": 0.0,  "high": 0.25},
        },
    },

    "corrdiff_coarse": {
        "arm": "corrdiff",
        "stage": "grid",
        "design": "ofat+blocks",
        "note": ("Stage 1 coarse screen for the CorrDiff arm. Narrower than the "
                 "LDM screen by design: the two trainers share their training "
                 "regime, so the LDM screen's verdict on lr, batch and "
                 "architecture transfers, and this screen spends its cells on the "
                 "second-residual target's own noise schedule and the mu_r "
                 "conditioning."),
        "blocks": [
            {"name": "mu_conditioning", "design": "cartesian",
             "axes": {"hr_mean_cond": ["on", "off"], "cond_drop": [0.0, 0.1, 0.2]}},
        ],
        "axes": {
            "lr":      [5e-5, 1e-4, 2e-4],
            "p_mean":  [-1.6, -1.2, -0.81],
            "p_std":   [1.2, 1.6],
            "width":   [128, 192],
        },
    },

    "corrdiff_refine": {
        "arm": "corrdiff",
        "stage": "tpe",
        "design": "sampled",
        "note": "Stage 2 Bayesian refinement for the CorrDiff arm.",
        "axes": {
            "lr":           {"type": "logfloat", "low": 3e-5, "high": 4e-4},
            "p_mean":       {"type": "float",    "low": -2.0, "high": -0.6},
            "p_std":        {"type": "float",    "low": 1.0,  "high": 1.8},
            "dropout":      {"type": "float",    "low": 0.0,  "high": 0.15},
            "weight_decay": {"type": "logfloat", "low": 1e-6, "high": 3e-2,
                             "allow_zero": True},
            "cond_drop":    {"type": "float",    "low": 0.0,  "high": 0.25},
        },
    },

    "regression_coarse": {
        "arm": "regression",
        "stage": "grid",
        "design": "ofat+blocks",
        "note": ("Screen for the deterministic conditional-mean network that "
                 "feeds the CorrDiff arm. No noise schedule here: this net is "
                 "trained under a plain regression loss, so the searchable set is "
                 "optimisation and capacity only."),
        "blocks": [],
        "axes": {
            "lr":           [5e-5, 1e-4, 2e-4, 4e-4],
            "width":        [96, 128, 192],
            "weight_decay": [0.0, 1e-4, 1e-2],
            "dropout":      [0.0, 0.05],
        },
    },

    "inference_grid": {
        "arm": "inference",
        "stage": "grid",
        "design": "ofat+blocks",
        "note": ("Stage 4 sampler sweep on a frozen checkpoint. One factor at a "
                 "time around the production sampler setting."),
        "blocks": [],
        "axes": {
            "steps":    [18, 25, 50],
            "members":  [4, 8, 16],
            "guidance": [1.0, 1.25, 1.5],
            "churn":    [0.0, 10.0, 40.0],
        },
    },

    "inference_grid_full": {
        "arm": "inference",
        "stage": "grid",
        "design": "cartesian",
        "note": ("Full cartesian sampler grid, 81 cells. Only affordable at a "
                 "small --limit; print the plan before running it."),
        "blocks": [],
        "axes": {
            "steps":    [18, 25, 50],
            "members":  [4, 8, 16],
            "guidance": [1.0, 1.25, 1.5],
            "churn":    [0.0, 10.0, 40.0],
        },
    },
}


PSD_CEILING_POOLED = 0.903


OBJECTIVES = {
    "crps_ss":   {"expr": "1.0 - crps / crps_adv",
                  "desc": "CRPS skill score against the advection prior on identical crops"},
    "crps_ss_pers": {"expr": "1.0 - crps / crps_pers",
                     "desc": "CRPS skill score against persistence"},
    "mae_ss":    {"expr": "1.0 - mae / mae_adv",
                  "desc": "MAE skill score against advection (ensemble mean)"},
    "csi8_ss":   {"expr": "csi_8 - csi_8_adv",
                  "desc": "heavy-rain CSI advantage over advection (noisy; not a primary)"},
    "val_loss":  {"expr": "-val_loss_w",
                  "desc": "negated weighted EDM validation loss (smoothness-biased; diagnostic only)"},
    "val_ev":    {"expr": "val_ev",
                  "desc": "held-out explained variance of the regression target (GATE-C's metric)"},
    "psd_gap":   {"expr": "-abs(psd_ratio_2_8km - psd_ceiling)",
                  "desc": "closeness of member small-scale power to the measured codec ceiling"},
    "composite": {"expr": "(1.0 - crps / crps_adv) - 0.25 * abs(psd_ratio_2_8km - psd_ceiling)",
                  "desc": ("CRPS skill score against advection, penalised for "
                           "departing from the codec PSD ceiling in either direction")},
    "infer_composite": {
        "expr": ("(1.0 - crps_fair / mae_adv) "
                 "- 0.50 * abs(spread_rmse_ratio - spread_rmse_ideal)"),
        "desc": ("fair-CRPS skill score against advection, penalised for "
                 "dispersion error against the M-dependent ideal sqrt((M+1)/M)")},
}

GATES = {
    "none":        {"expr": "True", "desc": "no admissibility gate"},
    "mae_vs_adv":  {"expr": "mae <= 1.01 * mae_adv",
                    "desc": ("ensemble-mean MAE must be within 1 percent of the "
                             "advection prior on identical crops. This is LDM.md "
                             "section 6 criterion (a) written as a hard gate.")},
    "beats_persistence": {"expr": "mae <= mae_pers",
                          "desc": "must at least beat persistence on MAE"},
    "both":        {"expr": "(mae <= 1.01 * mae_adv) and (mae <= mae_pers)",
                    "desc": "within 1 percent of advection and better than persistence"},
    "gate_c":      {"expr": "val_ev >= 0.10",
                    "desc": ("CorrDiff GATE-C: pooled held-out explained variance "
                             "of at least 0.10 for the learned mean to be worth "
                             "the 26.2-hour diffusion retrain")},
}

DEFAULT_OBJECTIVE = {"ldm": "composite", "corrdiff": "composite",
                     "regression": "val_ev", "inference": "infer_composite"}
DEFAULT_GATE = {"ldm": "mae_vs_adv", "corrdiff": "mae_vs_adv",
                "regression": "gate_c", "inference": "none"}


def sha_schedule(n_trials, rungs, eta=3):
    out, n = [], int(n_trials)
    for r in rungs:
        out.append((r, max(1, n)))
        n = max(1, int(math.floor(n / float(eta))))
    return out
