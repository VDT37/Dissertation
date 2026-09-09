# Diffusion nowcast scorecard (`val` split)

_3000 crops, 8-member ensembles, 25 Heun steps, guidance 1.25. Checkpoint epoch 50 (val loss 0.3314065786726351). FSS from 429 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.379 | 0.323 | **0.270** | 0.318 |
| RMSE (mm/h) | 1.261 | 1.129 | **0.880** | 1.126 |
| bias (mm/h) | +0.000 | -0.017 | -0.009 | -0.009 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.318 | 0.410 | 0.476 | 0.410 |
| 1 | 0.246 | 0.326 | 0.403 | 0.328 |
| 2 | 0.159 | 0.209 | 0.276 | 0.224 |
| 4 | 0.093 | 0.106 | 0.154 | 0.134 |
| 8 | 0.050 | 0.040 | 0.076 | 0.068 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.395 | 0.482 | 0.575 | 0.497 |
| FAR | 0.604 | 0.499 | 0.426 | 0.508 |
| freq_bias | 0.997 | 0.962 | 1.000 | 1.009 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1699 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.379.
- **Spread / RMSE**: 0.854 (spread 0.751, ens-mean RMSE 0.880). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.312 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0634, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.647 | 0.745 | 0.802 | 0.852 | 0.911 | 0.944 |
| mean, 1 mm/h | 0.576 | 0.687 | 0.753 | 0.813 | 0.888 | 0.932 |
| mean, 2 mm/h | 0.432 | 0.559 | 0.639 | 0.716 | 0.822 | 0.886 |
| mean, 4 mm/h | 0.274 | 0.393 | 0.470 | 0.557 | 0.679 | 0.744 |
| mean, 8 mm/h | 0.157 | 0.246 | 0.323 | 0.426 | 0.590 | 0.664 |
| member, 0.5 mm/h | 0.586 | 0.688 | 0.755 | 0.820 | 0.901 | 0.946 |
| member, 1 mm/h | 0.498 | 0.613 | 0.690 | 0.765 | 0.866 | 0.927 |
| member, 2 mm/h | 0.362 | 0.486 | 0.573 | 0.662 | 0.792 | 0.876 |
| member, 4 mm/h | 0.238 | 0.364 | 0.457 | 0.565 | 0.728 | 0.824 |
| member, 8 mm/h | 0.132 | 0.226 | 0.313 | 0.430 | 0.633 | 0.752 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 0.886 | 0.952 | 0.972 | 0.959 | 0.895 | 0.943 | 0.889 |
| model_mean | 0.699 | 0.279 | 0.224 | 0.211 | 0.215 | 0.212 | 0.210 |
| advection | 1.015 | 1.019 | 0.905 | 0.805 | 0.570 | 0.747 | 0.610 |
| persistence | 1.052 | 1.134 | 1.096 | 1.114 | 1.190 | 1.133 | 1.173 |
| _obs share of variance_ | 88.4% | 6.4% | 3.4% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.2 |
| model_mean | 34.4 |
| model_member | 22.6 |
| advection | 21.7 |
| persistence | 23.1 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
