#!/usr/bin/env python3
import os, json, getpass, argparse

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from train_ldm import (ZC, COND_CH, UNet, EDMDenoiser, edm_sample,
                       load_pack_meta, shard_suffix)
from train_vae import VAE, from_dbr

USER    = getpass.getuser()
SCRATCH = os.environ.get("DISS_SCRATCH", f"/work/scratch-nopw2/{USER}/dissertation")
LATENTS = os.path.join(SCRATCH, "latents")
DIFF    = os.path.expanduser("~/dissertation_outputs/diffusion")
VAE_CKPT = os.path.expanduser("~/dissertation_outputs/vae_v2/vae_best.pt")


def load_denoiser(ckpt_path, device):
    if not os.path.exists(ckpt_path):
        raise SystemExit(f"ERROR: checkpoint not found: {ckpt_path}")
    ck = torch.load(ckpt_path, map_location=device)
    cfg = ck["config"]
    sigma_data = ck.get("sigma_data", cfg.get("sigma_data"))
    if sigma_data is None:
        raise SystemExit("ERROR: checkpoint has no sigma_data; it was not written "
                         "by this version of train_ldm.py")
    mults = tuple(int(m) for m in cfg["mults"].split(","))
    attn = tuple(int(r) for r in cfg["attn"].split(",") if r.strip())
    cond_mode = ck.get("cond_mode", cfg["cond_mode"])
    ck_leads = cfg.get("leads")
    hr_mean_cond = cfg.get("hr_mean_cond", "off") == "on"
    in_ch = ZC + COND_CH[cond_mode] + (ZC if hr_mean_cond else 0)
    unet = UNet(in_ch=in_ch, out_ch=ZC, width=cfg["width"],
                mults=mults, dropout=cfg["dropout"], attn_res=attn,
                n_leads=len(ck_leads) if ck_leads else 0)
    den = EDMDenoiser(unet, sigma_data).to(device)
    den.load_state_dict(ck["model"])
    den.eval()
    n = sum(p.numel() for p in den.parameters())
    print(f"denoiser: {ckpt_path}", flush=True)
    print(f"  epoch {ck.get('epoch')} | val_loss {ck.get('val_loss', float('nan')):.4f} "
          f"| {n/1e6:.1f}M params | cond={cond_mode} | in_ch={in_ch} "
          f"| sigma_data={sigma_data:.4f}"
          f"{' | leads ' + str(ck_leads) if ck_leads else ''}"
          f"{' | CorrDiff: hr_mean_cond on' if hr_mean_cond else ''}", flush=True)
    if cfg.get("mu_dir") and not hr_mean_cond:
        print("  NOTE: this checkpoint was trained on r' = delta - mu_r with "
              "hr_mean_cond off. The mean still enters through the anchor, so "
              "sampling it without a mu pack gives wrong fields.", flush=True)
    return den, ck, cond_mode, ck_leads, hr_mean_cond


def load_codec(vae_path, pack_meta, device, strict_sha=True):
    if not os.path.exists(vae_path):
        raise SystemExit(f"ERROR: VAE checkpoint not found: {vae_path}")
    import hashlib
    h = hashlib.sha256()
    with open(vae_path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    sha = h.hexdigest()
    want = pack_meta.get("vae_sha256")
    if want and sha != want:
        msg = (f"VAE mismatch: --vae has sha {sha[:12]} but the latent pack was "
               f"encoded with {want[:12]}. Decoding latents with a different codec "
               "gives wrong fields.")
        if strict_sha:
            raise SystemExit("ERROR: " + msg + " Pass --allow-vae-mismatch to override.")
        print("WARNING: " + msg, flush=True)
    ck = torch.load(vae_path, map_location=device)
    vae = VAE(w=ck["config"]["width"], zc=ck["config"]["zc"]).to(device)
    vae.load_state_dict(ck["model"])
    vae.eval()
    return vae


@torch.no_grad()
def sample_ensemble(den, vae, rows, cond_mode, latent_scale, mean, std,
                    members=8, steps=25, guidance=1.0, churn=0.0, seed=0,
                    device="cuda", decode_batch=32, lead_idx=None,
                    mu=None, hr_mean_cond=False):
    K = rows.shape[0]
    rows = rows.to(device)
    cond = rows[:, :5 * ZC] if cond_mode == "full" else rows[:, 4 * ZC:5 * ZC]
    zA = rows[:, 4 * ZC:5 * ZC]
    if mu is not None:
        mu = mu.to(device)
        if hr_mean_cond:
            cond = torch.cat([cond, mu], dim=1)
    anchor = zA if mu is None else zA + mu
    li = (torch.full((K,), int(lead_idx), dtype=torch.long, device=device)
          if lead_idx is not None else None)
    out = np.empty((K, members, 256, 256), dtype="float32")
    for m in range(members):
        g = torch.Generator(device=device).manual_seed(seed + 1000 * m)
        delta = edm_sample(den, cond, steps=steps, guidance=guidance,
                           churn=churn, generator=g, lead_idx=li)
        mu_lat = (anchor + delta) / latent_scale
        dec = []
        for s in range(0, K, decode_batch):
            dec.append(vae.decode(mu_lat[s:s + decode_batch]).float().cpu())
        y_dbr = torch.cat(dec)[:, 0].numpy() * std + mean
        out[:, m] = from_dbr(y_dbr)
    return out


def resolve_lead_idx(ck_leads, lead):
    if not ck_leads:
        if lead is not None:
            print(f"NOTE: --lead {lead} selects the pack shard; this checkpoint is "
                  "not lead-conditioned, so the model itself gets no lead input.",
                  flush=True)
        return None
    if lead is None:
        raise SystemExit(f"ERROR: this checkpoint is lead-conditioned on {ck_leads}. "
                         "Pass --lead <minutes> so the right shard and embedding "
                         "are used.")
    if lead not in ck_leads:
        raise SystemExit(f"ERROR: --lead {lead} was not trained; checkpoint leads "
                         f"are {ck_leads}.")
    return ck_leads.index(lead)


def read_truth(npz_files):
    y, A, P, V = [], [], [], []
    for f in npz_files:
        if not os.path.exists(f):
            raise SystemExit(f"ERROR: source crop missing: {f}\n"
                             "The npz cache is needed for the ground truth and the "
                             "advection/persistence baselines (scratch wiped?).")
        z = np.load(f, allow_pickle=True)
        y.append(z["y_mmh"].astype("float32"))
        A.append(z["A_mmh"].astype("float32"))
        P.append(z["x_mmh"].astype("float32")[-1])
        V.append(z["valid"] & np.isfinite(z["A_mmh"]) & np.isfinite(z["x_mmh"][-1]))
    return (np.stack(y), np.stack(A), np.stack(P), np.stack(V))


def check_corrdiff_pairing(ck, mu_dir):
    trained_with_mu = bool(ck.get("config", {}).get("mu_dir"))
    if trained_with_mu and not mu_dir:
        raise SystemExit(
            "ERROR: this checkpoint was trained on the CorrDiff residual "
            f"r' = delta - mu_r (config mu_dir={ck['config']['mu_dir']}). Pass "
            "--mu-dir pointing at the pack_mu.py output built from the same "
            "frozen regression, or the reconstruction is missing the mean.")
    if mu_dir and not trained_with_mu:
        raise SystemExit(
            "ERROR: --mu-dir was given but this checkpoint was trained on plain "
            "delta = z_y - z_A. Adding mu_r to the anchor would double-count it.")


def open_split(latents_dir, split, lead=None, limit=None):
    suf = shard_suffix(lead)
    meta = load_pack_meta(latents_dir, split, lead)
    idx_p = os.path.join(latents_dir, f"{split}_latents{suf}_index.json")
    if not os.path.exists(idx_p):
        raise SystemExit(f"ERROR: {idx_p} not found (needed to locate ground truth).")
    files = json.load(open(idx_p))
    npy = os.path.join(latents_dir, f"{split}_latents{suf}.npy")
    mm = np.load(npy, mmap_mode="r")
    n = mm.shape[0]
    if n != len(files):
        raise SystemExit(f"ERROR: {npy} has {n} rows but its index lists "
                         f"{len(files)} files; the pack is inconsistent.")
    if limit:
        n = min(limit, n)
    return mm, files, n, meta


def montage(y, A, P, members, png, vmax=8.0, n_members_shown=3):
    K = y.shape[0]
    ens = members.mean(axis=1)
    cols = 4 + n_members_shown
    fig, ax = plt.subplots(K, cols, figsize=(3.1 * cols, 3.1 * K), squeeze=False)
    for r in range(K):
        panels = [(y[r], "obs y"), (P[r], "persistence"), (A[r], "advection A"),
                  (ens[r], f"ens mean ({members.shape[1]})")]
        panels += [(members[r, m], f"member {m + 1}") for m in range(n_members_shown)]
        for c, (img, ttl) in enumerate(panels):
            ax[r, c].imshow(img, vmin=0, vmax=vmax, cmap="viridis")
            ax[r, c].set_title(f"{ttl}  max {np.nanmax(img):.1f}", fontsize=8)
            ax[r, c].axis("off")
    plt.tight_layout()
    plt.savefig(png, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"montage -> {png}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(DIFF, "diff_best.pt"))
    ap.add_argument("--vae", default=VAE_CKPT)
    ap.add_argument("--latents-dir", default=LATENTS)
    ap.add_argument("--split", default="val", choices=["val", "train", "test"])
    ap.add_argument("--lead", type=int, default=None, help="lead shard (multi-lead pack)")
    ap.add_argument("--crops", type=int, default=8, help="number of crops to sample")
    ap.add_argument("--members", type=int, default=8)
    ap.add_argument("--steps", type=int, default=25, help="Heun sampler steps")
    ap.add_argument("--guidance", type=float, default=1.0,
                    help="classifier-free guidance weight (1 = plain conditional)")
    ap.add_argument("--churn", type=float, default=0.0, help="EDM S_churn")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stride", type=int, default=None,
                    help="pick crops every N rows (default: spread evenly)")
    ap.add_argument("--out", default=os.path.join(DIFF, "samples"))
    ap.add_argument("--mu-dir", default=None,
                    help="pack_mu.py directory, required for a checkpoint "
                         "trained with train_corrdiff.py")
    ap.add_argument("--reg-sha", default=None,
                    help="assert the mu pack's regression sha256; fatal on mismatch")
    ap.add_argument("--allow-vae-mismatch", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: no GPU found; sampling on CPU is very slow.", flush=True)

    mm, files, n, meta = open_split(args.latents_dir, args.split, args.lead)
    den, ck, cond_mode, ck_leads, hr_mean_cond = load_denoiser(args.ckpt, device)
    check_corrdiff_pairing(ck, args.mu_dir)
    mu_mm = None
    if args.mu_dir:
        from train_corrdiff import open_mu_split
        mu_mm = open_mu_split(args.mu_dir, args.latents_dir, args.split, args.lead,
                              n_rows=n, reg_sha=args.reg_sha)[0]
    lead_idx = resolve_lead_idx(ck_leads, args.lead)
    vae = load_codec(args.vae, meta, device, strict_sha=not args.allow_vae_mismatch)
    latent_scale = float(meta["latent_scale"])
    mean, std = float(meta["norm"]["mean"]), float(meta["norm"]["std"])

    K = min(args.crops, n)
    if args.stride:
        sel = np.arange(0, min(n, K * args.stride), args.stride)[:K]
    else:
        sel = np.linspace(0, n - 1, K).astype(int)
    rows = torch.from_numpy(np.asarray(mm[sel], dtype="float32"))
    mu_rows = (torch.from_numpy(np.asarray(mu_mm[sel], dtype="float32"))
               if mu_mm is not None else None)
    y, A, P, V = read_truth([files[i] for i in sel])

    print(f"sampling {K} crops x {args.members} members, {args.steps} steps "
          f"(guidance {args.guidance}, churn {args.churn}) ...", flush=True)
    members = sample_ensemble(den, vae, rows, cond_mode, latent_scale, mean, std,
                              members=args.members, steps=args.steps,
                              guidance=args.guidance, churn=args.churn,
                              seed=args.seed, device=device, lead_idx=lead_idx,
                              mu=mu_rows, hr_mean_cond=hr_mean_cond)

    npz = os.path.join(args.out, "ensembles.npz")
    np.savez_compressed(npz, y=y, A=A, persistence=P, valid=V, members=members,
                        rows=sel, files=np.array([files[i] for i in sel]),
                        members_n=args.members, steps=args.steps,
                        guidance=args.guidance, churn=args.churn, seed=args.seed)
    print(f"ensembles -> {npz}", flush=True)
    montage(y, A, P, members, os.path.join(args.out, "montage.png"))

    ens = members.mean(axis=1)
    print(f"\nquick check over these {K} crops (masked):")
    print(f"  obs max      {np.nanmax(np.where(V, y, np.nan)):.1f} mm/h")
    print(f"  member max   {np.nanmax(np.where(V[:, None], members, np.nan)):.1f} mm/h")
    print(f"  ens-mean max {np.nanmax(np.where(V, ens, np.nan)):.1f} mm/h")
    print(f"  MAE  model-mean {np.abs(ens - y)[V].mean():.3f} | "
          f"advection {np.abs(A - y)[V].mean():.3f} | "
          f"persistence {np.abs(P - y)[V].mean():.3f}")


if __name__ == "__main__":
    main()
