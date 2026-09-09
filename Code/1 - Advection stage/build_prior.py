#!/usr/bin/env python3
import argparse
import datetime as dt
import getpass
import io
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

import numpy as np
import h5py
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError

BUCKET   = "met-office-radar-obs-data"
REGION   = "eu-west-2"
FSUFFIX  = "_ODIM_ng_radar_rainrate_composite_1km_UK.h5"

CADENCE_MIN    = 15
N_INPUT        = 4
LEAD_MIN       = 60
CROP           = 256
MARGIN         = 64
CONTEXT        = CROP + 2 * MARGIN
STRIDE         = 256
CAP_MMH        = 128.0
RAIN_THRESH    = 0.1
MIN_VALID_FRAC = 0.90
MIN_RAIN_FRAC  = 0.05
DBR_THRESH     = 0.1
DBR_ZERO       = -15.0
DBR_INV_THR    = -10.0
TEST_YEAR      = 2026
VAL_DAYS       = 2

FRAMES_DIR = None
PRIOR_DIR  = None

def make_s3():
    return boto3.client("s3", region_name=REGION,
                        config=Config(signature_version=UNSIGNED,
                                      retries={"max_attempts": 5, "mode": "standard"}))


def radar_key(t):
    return f"radar/{t:%Y/%m/%d}/{t:%Y%m%d%H%M}{FSUFFIX}"


def read_odim_rainrate(source):
    fh = io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source
    with h5py.File(fh, "r") as f:
        node = f["dataset1"]["data1"]
        raw  = node["data"][...].astype("float32")
        a    = node["what"].attrs
        gain     = float(a.get("gain", 1.0))
        offset   = float(a.get("offset", 0.0))
        nodata   = float(a.get("nodata", -1.0))
        undetect = float(a.get("undetect", 0.0))
    R = raw * gain + offset
    R[raw == nodata]   = np.nan
    R[raw == undetect] = 0.0
    return np.clip(R, 0.0, CAP_MMH)


def frame_path(t):
    return os.path.join(FRAMES_DIR, f"{t:%Y/%m/%d}", f"{t:%Y%m%d%H%M}.h5")


def download_frame(t, s3):
    dst = frame_path(t)
    if os.path.exists(dst):
        return "skip"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=radar_key(t))
        data = obj["Body"].read()
    except ClientError:
        return "missing"
    except Exception as e:
        return f"error:{e}"
    tmp = dst + ".part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, dst)
    return "ok"


def read_frame_local(t):
    p = frame_path(t)
    if not os.path.exists(p):
        return None
    try:
        return read_odim_rainrate(p)
    except Exception:
        return None


def list_day_keys(date, s3):
    prefix = f"radar/{date:%Y/%m/%d}/"
    present = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for o in page.get("Contents", []):
            stamp = o["Key"].rsplit("/", 1)[-1][:12]
            try:
                present.add(dt.datetime.strptime(stamp, "%Y%m%d%H%M"))
            except ValueError:
                pass
    return present


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def build_availability(start, end, workers):
    s3 = make_s3()
    days = list(daterange(start, end))
    avail = set()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(list_day_keys, d, s3): d for d in days}
        for f in as_completed(futs):
            avail |= f.result()
    return avail


def make_temporal_samples(avail, leads):
    step = dt.timedelta(minutes=CADENCE_MIN)
    ref_lead = max(leads)
    out = []
    for t0 in sorted(avail):
        inputs = [t0 - k * step for k in range(N_INPUT - 1, -1, -1)]
        targets = {L: t0 + dt.timedelta(minutes=L) for L in leads}
        if all(ti in avail for ti in inputs) and all(tt in avail for tt in targets.values()):
            out.append({"input_times": inputs, "target_times": targets,
                        "target_time": t0 + dt.timedelta(minutes=ref_lead)})
    return out


def assign_split(date, first_days):
    if date.year == TEST_YEAR:
        return "test"
    if date.day <= VAL_DAYS:
        return "val"
    if first_days and date in first_days:
        return "val"
    return "train"


def split_samples(temporal, avail):
    month_days = {}
    for t in avail:
        month_days.setdefault((t.year, t.month), set()).add(t.date())
    first_by_month = {k: set(sorted(v)[:VAL_DAYS]) for k, v in month_days.items()}
    for s in temporal:
        d = s["target_time"].date()
        s["split"] = assign_split(d, first_by_month.get((d.year, d.month)))
    return temporal


def candidate_windows(shape):
    H, W = shape
    return [(r, c)
            for r in range(0, H - CONTEXT + 1, STRIDE)
            for c in range(0, W - CONTEXT + 1, STRIDE)]


def center_crop(a, size=CROP):
    H, W = a.shape[-2:]
    r = (H - size) // 2
    c = (W - size) // 2
    return a[..., r:r + size, c:c + size]


def crop_passes(target_ctx):
    center = center_crop(target_ctx, CROP)
    valid  = np.isfinite(center)
    if valid.mean() < MIN_VALID_FRAC:
        return False
    wet = np.nan_to_num(center) >= RAIN_THRESH
    return (wet[valid].mean() if valid.any() else 0.0) >= MIN_RAIN_FRAC


_OFLOW = _EXTRAP = _TF = None

def _init_pysteps():
    global _OFLOW, _EXTRAP, _TF
    if _OFLOW is None:
        from pysteps import motion, nowcasts
        from pysteps.utils import transformation
        _OFLOW  = motion.get_method("LK")
        _EXTRAP = nowcasts.get_method("extrapolation")
        _TF     = transformation


def to_dbr(R):
    _init_pysteps()
    return _TF.dB_transform(R, threshold=DBR_THRESH, zerovalue=DBR_ZERO)[0]


def from_dbr(R):
    _init_pysteps()
    return _TF.dB_transform(R, threshold=DBR_INV_THR, inverse=True)[0]


def advection_prior(x_ctx_mmh, leads):
    _init_pysteps()
    Rd = np.stack([to_dbr(f) for f in x_ctx_mmh], axis=0)
    Rd[~np.isfinite(Rd)] = DBR_ZERO
    try:
        V = _OFLOW(Rd)
        if not np.isfinite(V).all():
            V = np.nan_to_num(V)
    except Exception:
        V = np.zeros((2,) + Rd.shape[-2:], dtype="float32")
    fc = _EXTRAP(Rd[-1], V, max(leads) // CADENCE_MIN)
    out = {}
    for L in leads:
        f = fc[L // CADENCE_MIN - 1]
        A_dbr = center_crop(np.where(np.isfinite(f), f, DBR_ZERO))
        out[L] = (A_dbr, from_dbr(A_dbr))
    return out


def prior_path(target_time, window, split, lead):
    sub = os.path.join(PRIOR_DIR, split, f"{target_time:%Y%m%d}")
    return os.path.join(sub, f"{target_time:%Y%m%d%H%M}_r{window[0]:04d}_"
                             f"c{window[1]:04d}_L{lead:02d}.npz")


def process_sample(sample):
    inputs = sample["input_times"]
    targets = sample["target_times"]
    ref_target, split = sample["target_time"], sample["split"]
    leads = sorted(targets)
    in_frames = [read_frame_local(t) for t in inputs]
    tgt_frames = {L: read_frame_local(targets[L]) for L in leads}
    if any(f is None for f in in_frames) or any(f is None for f in tgt_frames.values()):
        return 0
    x_full = np.stack(in_frames, axis=0)
    ref_full = tgt_frames[leads[-1]]
    n = 0
    for (r, c) in candidate_windows(x_full.shape[-2:]):
        out_paths = {L: prior_path(ref_target, (r, c), split, L) for L in leads}
        if all(os.path.exists(p) for p in out_paths.values()):
            n += len(leads)
            continue
        sl = (slice(r, r + CONTEXT), slice(c, c + CONTEXT))
        if not crop_passes(ref_full[sl]):
            continue
        x_ctx = x_full[:, sl[0], sl[1]]
        adv = advection_prior(x_ctx, leads)
        x_crop = center_crop(x_ctx).astype("float16")
        for L in leads:
            out = out_paths[L]
            if os.path.exists(out):
                n += 1
                continue
            A_dbr, A_mmh = adv[L]
            y_mmh = center_crop(tgt_frames[L][sl])
            valid = np.isfinite(y_mmh)
            y_dbr = np.where(valid, to_dbr(y_mmh), DBR_ZERO)
            r_dbr = y_dbr - A_dbr
            os.makedirs(os.path.dirname(out), exist_ok=True)
            tmp = out + ".part"
            with open(tmp, "wb") as fh:
                np.savez_compressed(
                    fh,
                    x_mmh=x_crop,
                    A_dbr=A_dbr.astype("float16"), A_mmh=A_mmh.astype("float16"),
                    y_mmh=y_mmh.astype("float16"), r_dbr=r_dbr.astype("float16"),
                    valid=valid, split=split,
                    target=targets[L].isoformat(), lead_min=np.int16(L),
                )
            os.replace(tmp, out)
            n += 1
    return n


THRESHOLDS = [0.5, 1.0, 2.0, 4.0, 8.0]

def _score_file(path):
    try:
        z = np.load(path, allow_pickle=True)
        A = z["A_mmh"].astype("float32"); y = z["y_mmh"].astype("float32")
        valid = z["valid"] & np.isfinite(A)
        cont = {}
        for t in THRESHOLDS:
            o, p = (y >= t), (A >= t)
            cont[t] = (int(np.sum(valid & o & p)),
                       int(np.sum(valid & o & ~p)),
                       int(np.sum(valid & ~o & p)))
        mae = float(np.sum(np.abs(np.nan_to_num(A) - np.nan_to_num(y))[valid]))
        return cont, mae, int(valid.sum())
    except Exception:
        return None


def evaluate(files, workers):
    tot = {t: np.zeros(3) for t in THRESHOLDS}
    mae_sum, npix, skipped = 0.0, 0, 0
    with ProcessPoolExecutor(max_workers=workers,
                             mp_context=mp.get_context("fork")) as ex:
        for res in ex.map(_score_file, files, chunksize=64):
            if res is None:
                skipped += 1
                continue
            cont, mae, n = res
            for t in THRESHOLDS:
                tot[t] += cont[t]
            mae_sum += mae; npix += n
    out = {"n_crops": len(files), "n_skipped": skipped,
           "MAE_mmh": mae_sum / max(npix, 1), "CSI": {}}
    for t in THRESHOLDS:
        H, M, F = tot[t]
        out["CSI"][t] = (H / (H + M + F)) if (H + M + F) > 0 else float("nan")
    return out


def parse_lead(path):
    base = os.path.basename(path)
    if "_L" in base:
        try:
            return int(base.rsplit("_L", 1)[-1].split(".")[0])
        except ValueError:
            return None
    return None


def evaluate_by_lead(files, workers):
    present = {parse_lead(f) for f in files}
    if None in present:
        return {"all": evaluate(files, workers)}
    return {L: evaluate([f for f in files if parse_lead(f) == L], workers)
            for L in sorted(present)}


def connectivity_check():
    print("S3 connectivity self-test ...", flush=True)
    try:
        s3 = make_s3()
        keys = list_day_keys(dt.date(2024, 11, 21), s3)
        print(f"  OK - reached s3://{BUCKET}, found {len(keys)} frames on 2024-11-21.")
        return True
    except (EndpointConnectionError, Exception) as e:
        print(f"  FAILED to reach AWS S3: {e}")
        print("  -> The server likely has no outbound internet. Fallback:")
        print("     download frames on an internet-connected machine and rsync")
        print("     them into the --frames-dir, then re-run with --skip-download.")
        return False


def main():
    ap = argparse.ArgumentParser()
    user = getpass.getuser()
    default_root = os.environ.get("DISS_SCRATCH",
                                  f"/work/scratch-nopw2/{user}/dissertation")
    ap.add_argument("--start", default="2024-11-21", help="subset start (YYYY-MM-DD)")
    ap.add_argument("--end",   default="2025-04-30", help="subset end (YYYY-MM-DD)")
    ap.add_argument("--leads", default="15,30,45,60",
                    help="comma-separated lead times in minutes (multiples of 15), "
                         "one npz per (crop, lead); multi-lead writes to prior_ml/")
    ap.add_argument("--root",  default=default_root, help="scratch root for caches")
    ap.add_argument("--frames-dir", default=None, help="override frame cache dir")
    ap.add_argument("--prior-dir",  default=None, help="override prior cache dir")
    ap.add_argument("--out", default=os.path.expanduser("~/dissertation_outputs"),
                    help="persistent (home) dir for the manifest + baseline JSON")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 8) - 4))
    ap.add_argument("--io-workers", type=int, default=32, help="threads for download")
    ap.add_argument("--check", action="store_true", help="connectivity test then exit")
    ap.add_argument("--skip-download", action="store_true",
                    help="assume frames already in --frames-dir (offline servers)")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--baseline-only", action="store_true",
                    help="skip download+process; just (re)score the existing cache "
                         "and (re)write the manifest. No internet needed.")
    args = ap.parse_args()

    leads = sorted({int(x) for x in args.leads.split(",")})
    for L in leads:
        if L <= 0 or L % CADENCE_MIN != 0:
            sys.exit(f"--leads must be positive multiples of {CADENCE_MIN} min; got {L}")

    if args.check:
        sys.exit(0 if connectivity_check() else 1)

    global FRAMES_DIR, PRIOR_DIR
    FRAMES_DIR = args.frames_dir or os.path.join(args.root, "frames")
    PRIOR_DIR  = args.prior_dir or os.path.join(
        args.root, "prior" if leads == [LEAD_MIN] else "prior_ml")
    for d in (FRAMES_DIR, PRIOR_DIR, args.out):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as e:
            sys.exit(f"ERROR: cannot create {d}: {e}\n"
                     f"       The cache root is currently '{args.root}'. Set it with "
                     "--root (or export DISS_SCRATCH) to a writable volume, for example\n"
                     f"       --root /work/scratch-nopw2/{user}/dissertation")
    print(f"frames -> {FRAMES_DIR}\nprior  -> {PRIOR_DIR}", flush=True)

    if args.baseline_only:
        from collections import Counter
        import glob as _glob
        files = sorted(_glob.glob(os.path.join(PRIOR_DIR, "*", "*", "*.npz")))
        if not files:
            print("no crops in", PRIOR_DIR); sys.exit(1)
        by_split = dict(Counter(f.split(os.sep)[-3] for f in files))
        print(f"[baseline-only] scoring {len(files)} crops  by split: {by_split}")
        base = evaluate_by_lead(files, args.workers)
        manifest = {
            "created": dt.datetime.now().isoformat(timespec="seconds"),
            "start": args.start, "end": args.end,
            "n_crops": len(files), "by_split": by_split,
            "config": {"crop": CROP, "margin": MARGIN, "n_input": N_INPUT,
                       "leads": leads, "val_days": VAL_DAYS},
            "prior_dir": PRIOR_DIR, "baseline_advection_only_by_lead": base,
        }
        for L, sc in base.items():
            tag = f"+{L} min" if L != "all" else "all"
            print(f"  [{tag}] {sc['n_crops'] - sc['n_skipped']} crops | "
                  f"MAE {sc['MAE_mmh']:.4f} | "
                  + " ".join(f"CSI@{t:g} {sc['CSI'][t]:.3f}" for t in THRESHOLDS))
        for d in (args.out, PRIOR_DIR):
            with open(os.path.join(d, "manifest.json"), "w") as fh:
                json.dump(manifest, fh, indent=2)
        print(f"manifest -> {os.path.join(args.out, 'manifest.json')}")
        return

    if not args.skip_download and not connectivity_check():
        sys.exit(1)

    start = dt.date.fromisoformat(args.start)
    end   = dt.date.fromisoformat(args.end)
    t_run = time.time()

    print(f"\n[1/4] Listing S3 availability {start}..{end} ...", flush=True)
    avail = build_availability(start, end, args.io_workers)
    temporal = split_samples(make_temporal_samples(avail, leads), avail)
    from collections import Counter
    by_split = Counter(s["split"] for s in temporal)
    print(f"      {len(avail)} frames -> {len(temporal)} samples x {len(leads)} leads "
          f"{leads}  by split: {dict(by_split)}")

    if not args.skip_download:
        need = set()
        for s in temporal:
            need.update(s["input_times"]); need.update(s["target_times"].values())
        print(f"\n[2/4] Downloading {len(need)} unique frames "
              f"({args.io_workers} threads) ...", flush=True)
        stats = Counter()
        s3dl = make_s3()
        with ThreadPoolExecutor(max_workers=args.io_workers) as ex:
            futs = [ex.submit(download_frame, t, s3dl) for t in sorted(need)]
            for i, f in enumerate(as_completed(futs), 1):
                stats[f.result().split(":")[0]] += 1
                if i % 1000 == 0:
                    print(f"      {i}/{len(need)}  {dict(stats)}", flush=True)
        print(f"      done: {dict(stats)}")
    else:
        print("\n[2/4] --skip-download set: using existing frame cache.")

    print(f"\n[3/4] Building advection prior + residual "
          f"({args.workers} processes) ...", flush=True)
    total = 0
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=ctx) as ex:
        for i, n in enumerate(ex.map(process_sample, temporal, chunksize=8), 1):
            total += n
            if i % 500 == 0:
                print(f"      {i}/{len(temporal)} samples, {total} crops cached", flush=True)
    print(f"      cached {total} crops to {PRIOR_DIR}")

    import glob
    files = sorted(glob.glob(os.path.join(PRIOR_DIR, "*", "*", "*.npz")))
    manifest = {
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "start": args.start, "end": args.end,
        "n_crops": len(files), "by_split": dict(by_split),
        "config": {"crop": CROP, "margin": MARGIN, "n_input": N_INPUT,
                   "leads": leads, "val_days": VAL_DAYS},
        "prior_dir": PRIOR_DIR,
    }
    if not args.no_baseline and files:
        print(f"\n[4/4] Advection-only baseline over {len(files)} crops "
              f"({len(leads)} leads) ...", flush=True)
        base = evaluate_by_lead(files, args.workers)
        manifest["baseline_advection_only_by_lead"] = base
        for L, sc in base.items():
            tag = f"+{L} min" if L != "all" else "all"
            print(f"      [{tag}] MAE {sc['MAE_mmh']:.4f} mm/h | "
                  + " ".join(f"CSI@{t:g} {sc['CSI'][t]:.3f}" for t in THRESHOLDS))

    for d in (args.out, PRIOR_DIR):
        with open(os.path.join(d, "manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=2)
    print(f"\nDone in {(time.time()-t_run)/60:.1f} min. "
          f"Manifest -> {os.path.join(args.out, 'manifest.json')}")


if __name__ == "__main__":
    main()
