#!/usr/bin/env python3
import os, time, argparse

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter

from sample import load_codec, read_truth, open_split, LATENTS, VAE_CKPT
from train_ldm import ZC
from train_corrdiff import open_mu_split
from evaluate import (THRESHOLDS, SCALES, WET, new_det, acc_det,
                                finish_det, psd_band_metrics, run_stamp,
                                append_runs_row)
from train_regression import load_regression, slice_cond
from train_vae import from_dbr, radial_psd, atomic_json

OUT = os.path.expanduser("~/dissertation_outputs/regression/eval")
METHODS = ("regression_mean", "codec_advection", "codec_oracle",
           "advection", "persistence")

REF_ADVECTION = {60: {"MAE_mmh": 0.323, "RMSE_mmh": 1.140,
                      "CSI@1": 0.321, "CSI@8": 0.040}}
REF_TOL = 0.10


@torch.no_grad()
def decode_latent(vae, z, latent_scale, mean, std, device, batch=32):
    outs = []
    z = z.to(device)
    for s in range(0, z.shape[0], batch):
        outs.append(vae.decode(z[s:s + batch] / latent_scale).float().cpu())
    y_dbr = torch.cat(outs)[:, 0].numpy() * std + mean
    return from_dbr(y_dbr)


def evaluate(args, device):
    mm, files, n_all, meta = open_split(args.latents_dir, args.split, args.lead)
    if args.limit and args.limit < n_all:
        idx = np.unique(np.linspace(0, n_all - 1, args.limit).round().astype(int))
    else:
        idx = np.arange(n_all)
    n = len(idx)
    print(f"  crops {n}/{n_all} ({'stride' if n < n_all else 'full split'}) | "
          f"first {os.path.basename(os.path.dirname(files[idx[0]]))} | "
          f"last {os.path.basename(os.path.dirname(files[idx[-1]]))}", flush=True)

    vae = load_codec(args.vae, meta, device, strict_sha=not args.allow_vae_mismatch)
    latent_scale = float(meta["latent_scale"])
    mean, std = float(meta["norm"]["mean"]), float(meta["norm"]["std"])

    net = ck = mu_mm = supplied = None
    cond_mode = target = None
    lead_idx = None
    if args.field == "regression":
        if not args.reg:
            raise SystemExit("ERROR: --field regression needs --reg <checkpoint>")
        net, ck, cond_mode, target, ck_leads = load_regression(args.reg, device)
        if ck_leads:
            if args.lead is None or args.lead not in ck_leads:
                raise SystemExit(f"ERROR: the regression is lead-conditioned on "
                                 f"{ck_leads}; pass --lead <minutes>.")
            lead_idx = ck_leads.index(args.lead)
        if target == "z_y" and args.anchor == "zA":
            raise SystemExit(
                "ERROR: this regression predicts z_y directly (variant a), so its "
                "mean is not an increment on z_A. Pass --anchor none.")
    elif args.field == "mu-pack":
        if not args.mu_dir:
            raise SystemExit("ERROR: --field mu-pack needs --mu-dir")
        mu_mm, mu_meta = open_mu_split(args.mu_dir, args.latents_dir, args.split,
                                       args.lead, n_rows=n_all, reg_sha=args.reg_sha)
        target = mu_meta.get("target")
        if target == "z_y" and args.anchor == "zA":
            raise SystemExit("ERROR: this mu pack predicts z_y; pass --anchor none.")
    elif args.field == "npy":
        if not args.npy:
            raise SystemExit("ERROR: --field npy needs --npy <path>")
        supplied = np.load(args.npy, mmap_mode="r")
        if supplied.shape[0] != n_all:
            raise SystemExit(f"ERROR: {args.npy} has {supplied.shape[0]} rows but "
                             f"the split has {n_all}; they must align row for row.")

    active = [m for m in METHODS if m != "codec_oracle" or args.oracle]
    det = {m: new_det() for m in active}
    fss = {(m, t, s): [0.0, 0.0] for m in active
           for t in THRESHOLDS for s in SCALES}
    rbins = np.logspace(np.log10(WET), np.log10(128), 41)
    hist = {k: np.zeros(len(rbins) - 1) for k in ["obs"] + active}
    wet_area = {k: [0.0, 0] for k in hist}
    psd = {k: None for k in hist}
    n_psd = fss_done = 0
    fss_every = max(1, n // max(args.fss_sample, 1))
    psd_stride = n / max(args.psd_sample, 1)

    t0 = time.time()
    done = 0
    for s0 in range(0, n, args.batch):
        sel = idx[s0:s0 + args.batch]
        rows = torch.from_numpy(np.asarray(mm[sel], dtype="float32"))
        y, A, P, V = read_truth([files[i] for i in sel])
        zA = rows[:, 4 * ZC:5 * ZC]
        zy = rows[:, 5 * ZC:6 * ZC]

        if args.field == "regression":
            c = slice_cond(rows, cond_mode).to(device)
            li = (torch.full((c.shape[0],), lead_idx, dtype=torch.long,
                             device=device) if lead_idx is not None else None)
            mu_r = net(c, li).float().cpu()
        elif args.field == "mu-pack":
            mu_r = torch.from_numpy(np.asarray(mu_mm[sel], dtype="float32"))
        else:
            mu_r = None

        if args.field in ("regression", "mu-pack"):
            z_fc = (zA + mu_r) if args.anchor == "zA" else mu_r
            fc = decode_latent(vae, z_fc, latent_scale, mean, std, device, args.batch)
        elif args.field == "advection":
            fc = A
        else:
            fc = np.asarray(supplied[sel], dtype="float32")

        cadv = decode_latent(vae, zA, latent_scale, mean, std, device, args.batch)
        cora = (decode_latent(vae, zy, latent_scale, mean, std, device, args.batch)
                if args.oracle else None)

        fields = {"regression_mean": fc, "codec_advection": cadv,
                  "advection": A, "persistence": P}
        if cora is not None:
            fields["codec_oracle"] = cora

        for b in range(len(sel)):
            pos = s0 + b
            v = V[b]
            if not v.any():
                continue
            for name, F in fields.items():
                acc_det(det[name], F[b], y[b], v)
                vals = F[b][v]
                hist[name] += np.histogram(vals[vals >= WET], bins=rbins)[0]
                wet_area[name][0] += float((vals >= WET).mean())
                wet_area[name][1] += 1
            vals = y[b][v]
            hist["obs"] += np.histogram(vals[vals >= WET], bins=rbins)[0]
            wet_area["obs"][0] += float((vals >= WET).mean())
            wet_area["obs"][1] += 1

            if (v.mean() > 0.99 and n_psd < args.psd_sample
                    and pos >= n_psd * psd_stride):
                po = radial_psd(y[b])
                psd["obs"] = po if psd["obs"] is None else psd["obs"] + po
                for name, F in fields.items():
                    p = radial_psd(F[b])
                    psd[name] = p if psd[name] is None else psd[name] + p
                n_psd += 1

            if pos % fss_every == 0:
                for name, F in fields.items():
                    for t in THRESHOLDS:
                        Io = (np.nan_to_num(y[b]) >= t).astype("float32")
                        If = (np.nan_to_num(F[b]) >= t).astype("float32")
                        for sc in SCALES:
                            if sc > 1:
                                Mo = uniform_filter(Io, sc, mode="constant")
                                Mf = uniform_filter(If, sc, mode="constant")
                            else:
                                Mo, Mf = Io, If
                            fss[(name, t, sc)][0] += float(((Mf - Mo) ** 2).sum())
                            fss[(name, t, sc)][1] += float((Mf ** 2 + Mo ** 2).sum())
                fss_done += 1
            done += 1
        el = max(time.time() - t0, 1e-9)
        print(f"  {done}/{n} crops | {done/el:.2f} crops/s | "
              f"eta {(n-done)/max(done/el,1e-9)/60:.1f} min", flush=True)

    scored = [m for m in active if det[m]["n"] > 0]
    res = {m: finish_det(det[m]) for m in scored}
    fss_out = {}
    for (name, t, sc), (num, den_) in fss.items():
        if name not in scored:
            continue
        fss_out[f"{name}|{t}|{sc}"] = (1 - num / den_) if den_ > 0 else float("nan")
        fss_out[f"{name}|{t}|{sc}|num"] = num
        fss_out[f"{name}|{t}|{sc}|den"] = den_
    psd_avg = {k: (None if v is None else v / max(n_psd, 1)) for k, v in psd.items()}
    dist = {"rbins": rbins.tolist(),
            "hist": {k: v.tolist() for k, v in hist.items()},
            "psd": {k: (None if v is None else v.tolist()) for k, v in psd_avg.items()},
            "n_psd": n_psd,
            "psd_bands": {k: psd_band_metrics(psd_avg[k], psd_avg["obs"])
                          for k in psd_avg if k != "obs"},
            "wet_area": {k: (v[0] / max(v[1], 1)) for k, v in wet_area.items()},
            "wet_area_n": int(wet_area["obs"][1])}

    mae = {m: res[m]["MAE_mmh"] for m in scored}
    gates = {
        "gate_d_metric": "MAE_mmh of regression_mean vs codec_advection",
        "gate_d_pass": bool(mae["regression_mean"] <= mae["codec_advection"]),
        "margin_vs_codec_advection": mae["codec_advection"] - mae["regression_mean"],
        "margin_vs_advection": mae["advection"] - mae["regression_mean"],
        "codec_penalty": mae["codec_advection"] - mae["advection"],
    }
    if "codec_oracle" in mae:
        span = mae["codec_advection"] - mae["codec_oracle"]
        gates["fraction_of_codec_span"] = (
            (mae["codec_advection"] - mae["regression_mean"]) / span
            if abs(span) > 1e-12 else float("nan"))

    r = {"field": args.field, "anchor": args.anchor, "target": target,
         "split": args.split, "lead": args.lead, "n_crops": n,
         "n_crops_available": n_all,
         "subsample": "stride" if n < n_all else "full",
         "seed": args.seed,
         "reg_ckpt": (os.path.abspath(args.reg) if args.reg else None),
         "reg_epoch": (ck or {}).get("epoch"),
         "reg_val_mse": (ck or {}).get("val_mse"),
         "mu_dir": (os.path.abspath(args.mu_dir) if args.mu_dir else None),
         "vae": os.path.abspath(args.vae),
         "vae_sha256": meta.get("vae_sha256"),
         "sigma_data": meta.get("sigma_data"),
         "latent_scale": latent_scale,
         "n_fss_crops": fss_done, "methods": scored,
         **run_stamp(args),
         "deterministic": res, "fss": fss_out, "gates": gates,
         "distribution": dist}
    return r


STYLE = {"obs": ("k", 2.2), "regression_mean": ("C0", 1.8),
         "codec_advection": ("C4", 1.4), "codec_oracle": ("C2", 1.4),
         "advection": ("C1", 1.4), "persistence": ("C3", 1.2)}


def make_plots(r, png):
    d, dist = r["deterministic"], r["distribution"]
    names = r["methods"]
    rb = np.array(dist["rbins"]); rc = np.sqrt(rb[:-1] * rb[1:])
    fig, ax = plt.subplots(2, 2, figsize=(13, 10))

    for k in ["obs"] + names:
        h = np.array(dist["hist"][k]); h = h / max(h.sum(), 1)
        c, lw = STYLE[k]
        ax[0, 0].loglog(rc, h, color=c, lw=lw, label=k)
    ax[0, 0].set(title="Rain-rate distribution (wet pixels)", xlabel="mm/h",
                 ylabel="frequency")
    ax[0, 0].legend(fontsize=8); ax[0, 0].grid(alpha=0.3)

    for k in ["obs"] + names:
        p = dist["psd"].get(k)
        if p is None:
            continue
        p = np.array(p); kk = np.arange(1, len(p)); wl = 256.0 / kk
        c, lw = STYLE[k]
        ax[0, 1].loglog(wl, p[1:], color=c, lw=lw, label=k)
    ax[0, 1].set(title=f"Power spectrum ({dist['n_psd']} clean crops)",
                 xlabel="wavelength (km)", ylabel="power")
    ax[0, 1].invert_xaxis(); ax[0, 1].legend(fontsize=8); ax[0, 1].grid(alpha=0.3)

    for m in names:
        c, lw = STYLE[m]
        ax[1, 0].plot(THRESHOLDS, [d[m]["by_threshold"][t]["CSI"] for t in THRESHOLDS],
                      "o-", color=c, lw=lw, label=m)
    ax[1, 0].set(title="CSI vs threshold", xlabel="mm/h", ylabel="CSI",
                 xscale="log", ylim=(0, 1))
    ax[1, 0].legend(fontsize=8); ax[1, 0].grid(alpha=0.3)

    g = r["gates"]
    ax[1, 1].bar(names, [d[m]["MAE_mmh"] for m in names],
                 color=[STYLE[m][0] for m in names])
    ax[1, 1].set(title=f"MAE (mm/h) | GATE-D "
                       f"{'PASS' if g['gate_d_pass'] else 'FAIL'} vs codec floor "
                       f"({g['margin_vs_codec_advection']:+.4f}) | vs raw advection "
                       f"{g['margin_vs_advection']:+.4f}",
                 ylabel="mm/h")
    ax[1, 1].tick_params(axis="x", rotation=20)
    ax[1, 1].grid(alpha=0.3, axis="y")

    plt.tight_layout(); plt.savefig(png, dpi=120, bbox_inches="tight"); plt.close()
    print("plots ->", png, flush=True)


def write_markdown(r, md):
    d, dist, g = r["deterministic"], r["distribution"], r["gates"]
    names = r["methods"]
    hdr = "| metric | " + " | ".join(names) + " |"
    sep = "|---" * (len(names) + 1) + "|"
    L = [f"# Deterministic scorecard: `{r['field']}` "
         f"(`{r['split']}` split, lead {r['lead']})\n",
         f"_{r['n_crops']} of {r['n_crops_available']} crops ({r['subsample']}), "
         f"anchor `{r['anchor']}`, target `{r['target']}`. "
         f"Regression epoch {r['reg_epoch']} (val MSE {r['reg_val_mse']}). "
         f"FSS from {r['n_fss_crops']} crops, PSD from {dist['n_psd']}. "
         f"git `{r.get('git')}`._\n",
         "`codec_advection` is the codec floor (the advection field pushed "
         "through the same encode-decode round trip the learned mean pays) and "
         "`codec_oracle` is the codec ceiling (decode of the encoded truth). A "
         "latent method is judged between them before it is judged against raw "
         "advection.\n",
         "## GATE-D\n",
         f"- Verdict: **{'PASS' if g['gate_d_pass'] else 'FAIL'}** "
         f"({g['gate_d_metric']}).",
         f"- Margin against the codec floor: {g['margin_vs_codec_advection']:+.4f} "
         "mm/h (positive = the learned mean beats the round-tripped advection "
         "field, i.e. mu_r learned something that survives to pixels).",
         f"- Margin against raw advection: {g['margin_vs_advection']:+.4f} mm/h, "
         "the pixel-space headline.",
         f"- Codec round-trip penalty on advection alone: "
         f"{g['codec_penalty']:+.4f} mm/h."]
    if "fraction_of_codec_span" in g:
        L.append(f"- Fraction of the achievable codec span (floor to ceiling) "
                 f"recovered: {g['fraction_of_codec_span']:.3f}.")
    L += ["\n## Pixel error (lower is better)\n", hdr, sep,
          "| MAE (mm/h) | " + " | ".join(f"{d[m]['MAE_mmh']:.4f}" for m in names) + " |",
          "| RMSE (mm/h) | " + " | ".join(f"{d[m]['RMSE_mmh']:.4f}" for m in names) + " |",
          "| bias (mm/h) | " + " | ".join(f"{d[m]['bias_mmh']:+.4f}" for m in names) + " |",
          "\n## CSI by threshold (higher is better)\n",
          "| mm/h | " + " | ".join(names) + " |", sep]
    for t in THRESHOLDS:
        L.append(f"| {t:g} | " + " | ".join(
            f"{d[m]['by_threshold'][t]['CSI']:.4f}" for m in names) + " |")
    L += ["\n## Detection at 1 mm/h\n", hdr, sep]
    for k in ("POD", "FAR", "freq_bias"):
        L.append(f"| {k} | " + " | ".join(
            f"{d[m]['by_threshold'][1.0][k]:.4f}" for m in names) + " |")
    L += ["\n## FSS (neighbourhood scales, km)\n",
          "| field, threshold | " + " | ".join(f"{s} km" for s in SCALES) + " |",
          "|---" * (len(SCALES) + 1) + "|"]
    for m in names:
        for t in (1.0, 8.0):
            row = " | ".join(f"{r['fss'][f'{m}|{t}|{s}']:.3f}" for s in SCALES)
            L.append(f"| {m}, {t:g} mm/h | {row} |")
    bands = dist.get("psd_bands") or {}
    if any(bands.values()):
        ref = bands[names[0]]["bands"]
        L += [f"\n## Power spectrum by band ({dist['n_psd']} clean crops)\n",
              "Forecast band power divided by observed band power, 1.0 = matched. "
              "Bands partition the resolved spectrum. Both 2-8 km estimators are "
              "given because they disagree materially; the band power ratio is the "
              "headline (`docs/designs/Metrics_Catalogue.md`).\n",
              "| field | " + " | ".join(b for b in ref) +
              " | 2-8 km band power | 2-8 km mean-of-ratios |",
              "|---" * (len(ref) + 3) + "|"]
        for m in names:
            b = bands.get(m)
            if not b:
                continue
            L.append(f"| {m} | " +
                     " | ".join(f"{b['bands'][k]['ratio']:.3f}" for k in ref) +
                     f" | {b['psd_band_power']:.3f} | {b['psd_mean_ratio']:.3f} |")
        L.append("| _obs share of variance_ | " +
                 " | ".join(f"{ref[k]['obs_share']*100:.1f}%" for k in ref) +
                 " | | |")
    L += ["\n## Wet-area fraction (>= 0.1 mm/h)\n", "| field | % |", "|---|---|"]
    for k, v in dist["wet_area"].items():
        L.append(f"| {k} | {v*100:.1f} |")
    open(md, "w").write("\n".join(L) + "\n")
    print("tables ->", md, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", default="regression",
                    choices=["regression", "mu-pack", "advection", "npy"],
                    help="regression = run the frozen net from --reg; mu-pack = "
                         "read mu_r from a pack_mu.py memmap; advection = score A "
                         "alone; npy = an (n,256,256) mm/h array aligned with the "
                         "split")
    ap.add_argument("--reg", default=None, help="regression checkpoint")
    ap.add_argument("--mu-dir", default=None, help="required for --field mu-pack")
    ap.add_argument("--reg-sha", default=None,
                    help="assert the mu pack's reg_sha256 (--field mu-pack)")
    ap.add_argument("--npy", default=None, help="required for --field npy")
    ap.add_argument("--anchor", choices=["zA", "none"], default="zA",
                    help="zA = decode(z_A + mu_r) for a --target delta regression; "
                         "none = decode(mu_r) alone, which is what variant (a) needs")
    ap.add_argument("--oracle", dest="oracle", action="store_true", default=True,
                    help="also score the codec ceiling decode(z_y) (default on)")
    ap.add_argument("--no-oracle", dest="oracle", action="store_false")
    ap.add_argument("--vae", default=VAE_CKPT)
    ap.add_argument("--latents-dir", default=LATENTS)
    ap.add_argument("--split", default="val", choices=["val", "train", "test"])
    ap.add_argument("--lead", type=int, default=None)
    ap.add_argument("--batch", type=int, default=32, help="crops per decode pass")
    ap.add_argument("--limit", type=int, default=None,
                    help="strided subsample, never a truncation")
    ap.add_argument("--fss-sample", type=int, default=400)
    ap.add_argument("--psd-sample", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--tag", default="", help="suffix for the output filenames")
    ap.add_argument("--allow-vae-mismatch", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no GPU found; decoding on CPU is slow but feasible.",
              flush=True)

    t0 = time.time()
    r = evaluate(args, device)
    r["wall_min"] = round((time.time() - t0) / 60, 1)

    d, g = r["deterministic"], r["gates"]
    print(f"\n=== {r['split']} split, lead {r['lead']}, {r['n_crops']} crops, "
          f"field {r['field']} ===")
    for m in r["methods"]:
        print(f"  {m:16s} MAE {d[m]['MAE_mmh']:.4f} | RMSE {d[m]['RMSE_mmh']:.4f} | "
              f"CSI@1 {d[m]['by_threshold'][1.0]['CSI']:.4f} | "
              f"CSI@8 {d[m]['by_threshold'][8.0]['CSI']:.4f}")
    print(f"  GATE-D {'PASS' if g['gate_d_pass'] else 'FAIL'}: "
          f"{g['margin_vs_codec_advection']:+.4f} mm/h against the codec floor | "
          f"{g['margin_vs_advection']:+.4f} against raw advection")
    ref = REF_ADVECTION.get(args.lead if args.lead is not None else 60)
    if ref and args.field == "advection":
        got = {"MAE_mmh": d["advection"]["MAE_mmh"],
               "RMSE_mmh": d["advection"]["RMSE_mmh"],
               "CSI@1": d["advection"]["by_threshold"][1.0]["CSI"],
               "CSI@8": d["advection"]["by_threshold"][8.0]["CSI"]}
        worst = max(abs(got[k] - v) / max(abs(v), 1e-9) for k, v in ref.items())
        print(f"  reproduction check ({'PASS' if worst <= REF_TOL else 'FAIL'}) "
              f"against the single60 full-split advection column "
              f"(13,281 crops), tolerance {REF_TOL:.0%}:")
        for k, v in ref.items():
            print(f"    {k:9s} here {got[k]:.4f} | recorded {v:.4f} "
                  f"({100*(got[k]-v)/max(abs(v),1e-9):+.1f}%)")
        if worst > REF_TOL:
            print("    outside tolerance: the validity mask, the crop set or "
                  "the dBR round trip differs from the other scripts")
        print(f"    codec round trip on the same field costs "
              f"{d['codec_advection']['MAE_mmh'] - d['advection']['MAE_mmh']:+.4f} "
              f"mm/h of MAE (codec_advection vs advection).")
    for k in ("regression_mean", "codec_advection", "codec_oracle", "advection"):
        pb = r["distribution"]["psd_bands"].get(k)
        if pb:
            print(f"  PSD 2-8 km  {k:16s} band power {pb['psd_band_power']:.3f} "
                  f"| mean-of-ratios {pb['psd_mean_ratio']:.3f}")
    if "codec_oracle" in r["methods"]:
        print(f"  codec bounds on these {r['n_crops']} crops: floor "
              f"{d['codec_advection']['MAE_mmh']:.4f} -> ceiling "
              f"{d['codec_oracle']['MAE_mmh']:.4f} mm/h MAE")

    tag = args.tag or ""
    atomic_json(r, os.path.join(args.out, f"det_eval{tag}.json"))
    make_plots(r, os.path.join(args.out, f"det_eval{tag}.png"))
    write_markdown(r, os.path.join(args.out, f"det_eval{tag}.md"))
    append_runs_row(r, r["methods"], args.out)
    print(f"\ndone in {r['wall_min']:.1f} min", flush=True)


if __name__ == "__main__":
    main()
