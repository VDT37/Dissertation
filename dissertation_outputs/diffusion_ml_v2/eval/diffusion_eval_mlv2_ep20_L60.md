# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 20 (val loss 0.3334581483106177). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.382 | 0.323 | **0.279** | 0.335 |
| RMSE (mm/h) | 1.283 | 1.140 | **0.905** | 1.191 |
| bias (mm/h) | -0.001 | -0.019 | -0.006 | -0.006 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.307 | 0.404 | 0.459 | 0.385 |
| 1 | 0.237 | 0.321 | 0.389 | 0.306 |
| 2 | 0.153 | 0.207 | 0.267 | 0.206 |
| 4 | 0.089 | 0.105 | 0.150 | 0.119 |
| 8 | 0.048 | 0.040 | 0.068 | 0.058 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.383 | 0.477 | 0.564 | 0.463 |
| FAR | 0.616 | 0.504 | 0.444 | 0.525 |
| freq_bias | 0.996 | 0.961 | 1.014 | 0.975 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1727 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.382.
- **Spread / RMSE**: 0.915 (spread 0.828, ens-mean RMSE 0.905). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.295 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0669, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.634 | 0.735 | 0.794 | 0.845 | 0.905 | 0.938 |
| mean, 1 mm/h | 0.568 | 0.685 | 0.753 | 0.815 | 0.890 | 0.931 |
| mean, 2 mm/h | 0.443 | 0.576 | 0.658 | 0.735 | 0.833 | 0.886 |
| mean, 4 mm/h | 0.311 | 0.444 | 0.528 | 0.614 | 0.728 | 0.790 |
| mean, 8 mm/h | 0.200 | 0.289 | 0.356 | 0.444 | 0.543 | 0.568 |
| member, 0.5 mm/h | 0.564 | 0.671 | 0.742 | 0.810 | 0.895 | 0.944 |
| member, 1 mm/h | 0.478 | 0.599 | 0.682 | 0.762 | 0.867 | 0.927 |
| member, 2 mm/h | 0.359 | 0.490 | 0.582 | 0.676 | 0.809 | 0.891 |
| member, 4 mm/h | 0.248 | 0.379 | 0.477 | 0.585 | 0.742 | 0.843 |
| member, 8 mm/h | 0.152 | 0.245 | 0.337 | 0.471 | 0.669 | 0.763 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.027 | 1.193 | 1.189 | 1.181 | 1.031 | 1.140 | 1.057 |
| model_mean | 0.757 | 0.334 | 0.264 | 0.237 | 0.200 | 0.227 | 0.207 |
| advection | 1.014 | 1.160 | 1.046 | 0.851 | 0.480 | 0.749 | 0.559 |
| persistence | 0.926 | 0.980 | 0.983 | 0.994 | 0.943 | 0.980 | 0.953 |
| _obs share of variance_ | 89.0% | 6.0% | 3.2% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 34.2 |
| model_member | 22.2 |
| advection | 21.6 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
