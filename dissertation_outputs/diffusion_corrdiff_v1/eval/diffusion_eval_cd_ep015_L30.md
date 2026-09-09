# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 15 (val loss 0.4062583218950657). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.333 | 0.253 | **0.212** | 0.263 |
| RMSE (mm/h) | 1.203 | 0.992 | **0.790** | 1.056 |
| bias (mm/h) | -0.001 | -0.015 | +0.004 | +0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.388 | 0.532 | 0.593 | 0.523 |
| 1 | 0.311 | 0.446 | 0.527 | 0.440 |
| 2 | 0.213 | 0.320 | 0.409 | 0.322 |
| 4 | 0.129 | 0.186 | 0.265 | 0.200 |
| 8 | 0.072 | 0.088 | 0.140 | 0.105 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.474 | 0.609 | 0.713 | 0.614 |
| FAR | 0.525 | 0.374 | 0.330 | 0.392 |
| freq_bias | 0.996 | 0.973 | 1.064 | 1.010 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1327 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.253 and persistence 0.333.
- **Spread / RMSE**: 0.948 (spread 0.749, ens-mean RMSE 0.790). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.259 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0417, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.746 | 0.849 | 0.899 | 0.933 | 0.966 | 0.980 |
| mean, 1 mm/h | 0.691 | 0.815 | 0.875 | 0.918 | 0.960 | 0.978 |
| mean, 2 mm/h | 0.595 | 0.749 | 0.827 | 0.887 | 0.944 | 0.968 |
| mean, 4 mm/h | 0.458 | 0.640 | 0.739 | 0.818 | 0.895 | 0.928 |
| mean, 8 mm/h | 0.296 | 0.463 | 0.575 | 0.680 | 0.786 | 0.827 |
| member, 0.5 mm/h | 0.688 | 0.810 | 0.875 | 0.923 | 0.968 | 0.986 |
| member, 1 mm/h | 0.613 | 0.759 | 0.838 | 0.899 | 0.957 | 0.981 |
| member, 2 mm/h | 0.501 | 0.673 | 0.773 | 0.851 | 0.930 | 0.966 |
| member, 4 mm/h | 0.364 | 0.554 | 0.676 | 0.781 | 0.891 | 0.940 |
| member, 8 mm/h | 0.232 | 0.402 | 0.536 | 0.666 | 0.816 | 0.875 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.053 | 1.114 | 1.136 | 1.154 | 1.023 | 1.118 | 1.037 |
| model_mean | 0.925 | 0.527 | 0.354 | 0.281 | 0.237 | 0.269 | 0.245 |
| advection | 0.960 | 1.036 | 0.954 | 0.775 | 0.444 | 0.684 | 0.511 |
| persistence | 0.952 | 1.002 | 0.991 | 0.969 | 0.934 | 0.959 | 0.938 |
| _obs share of variance_ | 88.8% | 6.0% | 3.2% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| model_mean | 29.3 |
| model_member | 22.6 |
| advection | 22.1 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
