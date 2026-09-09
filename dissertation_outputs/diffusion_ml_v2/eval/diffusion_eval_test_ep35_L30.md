# Diffusion nowcast scorecard (`test` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 35 (val loss 0.33152407111889187). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.293 | 0.216 | **0.188** | 0.234 |
| RMSE (mm/h) | 1.251 | 1.035 | **0.845** | 1.119 |
| bias (mm/h) | -0.003 | -0.017 | -0.004 | -0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.360 | 0.507 | 0.561 | 0.480 |
| 1 | 0.280 | 0.423 | 0.491 | 0.397 |
| 2 | 0.190 | 0.315 | 0.381 | 0.294 |
| 4 | 0.110 | 0.188 | 0.233 | 0.179 |
| 8 | 0.059 | 0.106 | 0.132 | 0.095 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.435 | 0.582 | 0.663 | 0.568 |
| FAR | 0.560 | 0.394 | 0.346 | 0.430 |
| freq_bias | 0.990 | 0.960 | 1.014 | 0.996 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1188 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.216 and persistence 0.293.
- **Spread / RMSE**: 0.928 (spread 0.784, ens-mean RMSE 0.845). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.258 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0475, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.716 | 0.829 | 0.883 | 0.923 | 0.962 | 0.977 |
| mean, 1 mm/h | 0.653 | 0.787 | 0.854 | 0.904 | 0.952 | 0.974 |
| mean, 2 mm/h | 0.537 | 0.698 | 0.784 | 0.848 | 0.913 | 0.947 |
| mean, 4 mm/h | 0.364 | 0.545 | 0.655 | 0.745 | 0.841 | 0.882 |
| mean, 8 mm/h | 0.195 | 0.343 | 0.450 | 0.542 | 0.633 | 0.661 |
| member, 0.5 mm/h | 0.642 | 0.773 | 0.845 | 0.902 | 0.958 | 0.981 |
| member, 1 mm/h | 0.558 | 0.711 | 0.798 | 0.867 | 0.939 | 0.970 |
| member, 2 mm/h | 0.436 | 0.610 | 0.717 | 0.805 | 0.899 | 0.946 |
| member, 4 mm/h | 0.288 | 0.466 | 0.592 | 0.706 | 0.834 | 0.899 |
| member, 8 mm/h | 0.148 | 0.281 | 0.398 | 0.522 | 0.682 | 0.762 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.025 | 0.916 | 0.957 | 1.002 | 0.967 | 0.993 | 0.961 |
| model_mean | 0.848 | 0.383 | 0.249 | 0.207 | 0.170 | 0.198 | 0.176 |
| advection | 0.899 | 0.808 | 0.778 | 0.664 | 0.408 | 0.599 | 0.460 |
| persistence | 0.920 | 0.869 | 0.884 | 0.859 | 0.871 | 0.862 | 0.873 |
| _obs share of variance_ | 89.4% | 6.3% | 2.9% | 1.0% | 0.4% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 22.5 |
| model_mean | 28.3 |
| model_member | 21.8 |
| advection | 21.3 |
| persistence | 22.3 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
