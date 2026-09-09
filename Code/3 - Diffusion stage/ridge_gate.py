#!/usr/bin/env python3
import os, sys, json, time, socket, getpass, argparse

import numpy as np

from train_ldm import ZC, shard_suffix, load_pack_meta, git_hash

USER    = getpass.getuser()
SCRATCH = os.environ.get("DISS_SCRATCH", f"/work/scratch-nopw2/{USER}/dissertation")
LATENTS = os.path.join(SCRATCH, "latents")
OUT     = os.path.expanduser("~/dissertation_outputs/regression/ridge_gate.json")

FEATURE_SETS = {"full":   (0, 5 * ZC),
                "x-only": (0, 4 * ZC),
                "a-only": (4 * ZC, 5 * ZC)}


def strided_rows(n, k):
    if k >= n:
        return np.arange(n)
    return np.unique(np.linspace(0, n - 1, k).round().astype(np.int64))


def windows(cond, K):
    C, H, W = cond.shape
    p = K // 2
    if p:
        cond = np.pad(cond, ((0, 0), (p, p), (p, p)))
    win = np.lib.stride_tricks.sliding_window_view(cond, (K, K), axis=(1, 2))
    return np.ascontiguousarray(win.transpose(1, 2, 0, 3, 4)).reshape(H * W, C * K * K)


def accumulate(path, rows, K, c_lo, c_hi, block=16):
    mm = np.load(path, mmap_mode="r")
    C = c_hi - c_lo
    F = C * K * K + 1
    XtX = np.zeros((F, F))
    XtY = np.zeros((F, ZC))
    y_sum = np.zeros(ZC)
    y_sq = np.zeros(ZC)
    n_cells = 0
    for s in range(0, len(rows), block):
        sel = rows[s:s + block]
        raw = np.asarray(mm[sel], dtype="float32")
        cond = raw[:, c_lo:c_hi]
        tgt = raw[:, 5 * ZC:6 * ZC] - raw[:, 4 * ZC:5 * ZC]
        Xs = np.empty((len(sel) * 4096, F))
        Ys = np.empty((len(sel) * 4096, ZC))
        for b in range(len(sel)):
            Xs[b * 4096:(b + 1) * 4096, :F - 1] = windows(cond[b], K)
            Ys[b * 4096:(b + 1) * 4096] = tgt[b].reshape(ZC, -1).T
        Xs[:, F - 1] = 1.0
        XtX += Xs.T @ Xs
        XtY += Xs.T @ Ys
        y_sum += Ys.sum(axis=0)
        y_sq += (Ys * Ys).sum(axis=0)
        n_cells += Ys.shape[0]
    return {"XtX": XtX, "XtY": XtY, "y_sum": y_sum, "y_sq": y_sq, "n": n_cells}


def subset_index(K, c_lo, c_hi, sub_lo, sub_hi):
    F = (c_hi - c_lo) * K * K + 1
    idx = []
    for c in range(sub_lo - c_lo, sub_hi - c_lo):
        idx.extend(range(c * K * K, (c + 1) * K * K))
    idx.append(F - 1)
    return np.array(idx, dtype=np.int64)


def solve_ridge(XtX, XtY, alpha):
    A = XtX.copy()
    F = A.shape[0]
    A[np.arange(F - 1), np.arange(F - 1)] += alpha
    return np.linalg.solve(A, XtY)


def score(acc, W, idx=None):
    XtX = acc["XtX"] if idx is None else acc["XtX"][np.ix_(idx, idx)]
    XtY = acc["XtY"] if idx is None else acc["XtY"][idx]
    sse = float(acc["y_sq"].sum() - 2 * np.sum(W * XtY) + np.sum(W * (XtX @ W)))
    n = acc["n"]
    sq = float(acc["y_sq"].sum())
    var = float(sq - (acc["y_sum"] ** 2).sum() / n)
    return {"sse": sse, "ev_var": 1 - sse / max(var, 1e-12),
            "ev_sm": 1 - sse / max(sq, 1e-12)}


def per_channel_ev(acc, W, idx=None):
    XtX = acc["XtX"] if idx is None else acc["XtX"][np.ix_(idx, idx)]
    XtY = acc["XtY"] if idx is None else acc["XtY"][idx]
    out = []
    for c in range(ZC):
        w = W[:, c]
        sse = float(acc["y_sq"][c] - 2 * w @ XtY[:, c] + w @ (XtX @ w))
        sq = float(acc["y_sq"][c])
        out.append(1 - sse / max(sq, 1e-12))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--latents-dir", default=LATENTS)
    ap.add_argument("--leads", default="15,30,45,60")
    ap.add_argument("--fit-rows", type=int, default=20000,
                    help="train rows sampled by stride")
    ap.add_argument("--eval-rows", type=int, default=5000,
                    help="held-out val rows sampled by stride")
    ap.add_argument("--kernel", type=int, default=3,
                    help="receptive field in latent cells: 1, 3 or 5")
    ap.add_argument("--features", choices=["full", "a-only", "x-only"],
                    default="full",
                    help="full also reports the x-only and a-only submatrices, "
                         "which cost nothing extra")
    ap.add_argument("--alphas", default="1e-4,1e-3,1e-2,1e-1,1,10")
    ap.add_argument("--block", type=int, default=16,
                    help="rows per BLAS block (memory ~ block * 4096 * F * 8 B)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)

    K = args.kernel
    if K % 2 == 0 or K < 1:
        raise SystemExit(f"ERROR: --kernel must be odd and >= 1, got {K}.")
    alphas = [float(a) for a in args.alphas.split(",") if a.strip()]
    leads = [int(x) for x in args.leads.split(",") if x.strip()] or [None]
    c_lo, c_hi = FEATURE_SETS[args.features]
    subsets = (["full", "x-only", "a-only"] if args.features == "full"
               else [args.features])

    result = {"kernel": K, "features": args.features, "alphas": alphas,
              "fit_rows": args.fit_rows, "eval_rows": args.eval_rows,
              "latents_dir": os.path.abspath(args.latents_dir),
              "git": git_hash(), "host": socket.gethostname(),
              "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "argv": sys.argv,
              "by_lead": {}}

    for L in leads:
        suf = shard_suffix(L)
        tr_p = os.path.join(args.latents_dir, f"train_latents{suf}.npy")
        va_p = os.path.join(args.latents_dir, f"val_latents{suf}.npy")
        if not (os.path.exists(tr_p) and os.path.exists(va_p)):
            print(f"[+{L}min] shard missing ({tr_p}); skipping", flush=True)
            continue
        tr_meta = load_pack_meta(args.latents_dir, "train", L)
        n_tr = np.load(tr_p, mmap_mode="r").shape[0]
        n_va = np.load(va_p, mmap_mode="r").shape[0]
        rows_tr = strided_rows(n_tr, args.fit_rows)
        rows_va = strided_rows(n_va, args.eval_rows)
        t0 = time.time()
        print(f"[+{L}min] accumulating {len(rows_tr)} train rows "
              f"({(c_hi - c_lo)}ch x {K}x{K} = {(c_hi-c_lo)*K*K + 1} features) ...",
              flush=True)
        A_tr = accumulate(tr_p, rows_tr, K, c_lo, c_hi, args.block)
        A_va = accumulate(va_p, rows_va, K, c_lo, c_hi, args.block)
        print(f"[+{L}min] accumulated in {time.time() - t0:.0f}s "
              f"({A_tr['n']:,} train cells, {A_va['n']:,} eval cells)", flush=True)

        entry = {"n_train_rows": int(len(rows_tr)), "n_eval_rows": int(len(rows_va)),
                 "n_train_cells": A_tr["n"], "n_eval_cells": A_va["n"],
                 "sigma_data_pack": tr_meta.get("sigma_data")}
        for sub in subsets:
            s_lo, s_hi = FEATURE_SETS[sub]
            idx = (None if (s_lo, s_hi) == (c_lo, c_hi)
                   else subset_index(K, c_lo, c_hi, s_lo, s_hi))
            XtX = A_tr["XtX"] if idx is None else A_tr["XtX"][np.ix_(idx, idx)]
            XtY = A_tr["XtY"] if idx is None else A_tr["XtY"][idx]
            best = None
            scan = []
            for a in alphas:
                try:
                    W = solve_ridge(XtX, XtY, a)
                except np.linalg.LinAlgError:
                    print(f"  alpha {a:g}: singular system, skipped", flush=True)
                    continue
                fit = score(A_tr, W, idx)
                ev = score(A_va, W, idx)
                scan.append({"alpha": a, "ev_fit": fit["ev_var"],
                             "ev_eval": ev["ev_var"], "ev_eval_sm": ev["ev_sm"]})
                if best is None or ev["ev_var"] > best["ev_eval"]:
                    best = {"alpha": a, "ev_fit": fit["ev_var"],
                            "ev_fit_sm": fit["ev_sm"], "ev_eval": ev["ev_var"],
                            "ev_eval_sm": ev["ev_sm"],
                            "ev_eval_per_channel": per_channel_ev(A_va, W, idx),
                            "n_features": int(XtX.shape[0])}
            if best is None:
                continue
            best["scan"] = scan
            entry[sub] = best
            print(f"  [+{L}min] {sub:7s} K={K} best alpha {best['alpha']:g} | "
                  f"EV fit {best['ev_fit']:.4f} | EV held-out {best['ev_eval']:.4f} "
                  f"(second-moment {best['ev_eval_sm']:.4f}) | per channel "
                  + ", ".join(f"{v:.3f}" for v in best["ev_eval_per_channel"]),
                  flush=True)
        result["by_lead"][str(L)] = entry

    tmp = args.out + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(result, fh, indent=2)
    os.replace(tmp, args.out)
    print(f"\nridge gate -> {args.out}", flush=True)

    print("\nEV_ridge is a lower bound on what R_phi can reach; compare it "
          "against train_regression.py's val EV using ev_eval_sm.", flush=True)
    for L, e in result["by_lead"].items():
        row = e.get("full") or e.get(args.features)
        if row:
            print(f"  +{L}min  EV_ridge(held out) = {row['ev_eval']:.4f} "
                  f"[sm {row['ev_eval_sm']:.4f}]", flush=True)


if __name__ == "__main__":
    main()
