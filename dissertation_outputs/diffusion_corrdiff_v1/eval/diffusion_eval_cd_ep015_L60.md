# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 15 (val loss 0.4062583218950657). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.382 | 0.323 | **0.268** | 0.321 |
| RMSE (mm/h) | 1.283 | 1.140 | **0.888** | 1.175 |
| bias (mm/h) | -0.001 | -0.019 | -0.004 | -0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.307 | 0.404 | 0.482 | 0.412 |
| 1 | 0.237 | 0.321 | 0.413 | 0.332 |
| 2 | 0.153 | 0.207 | 0.293 | 0.227 |
| 4 | 0.089 | 0.105 | 0.168 | 0.132 |
| 8 | 0.048 | 0.040 | 0.078 | 0.063 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.383 | 0.477 | 0.591 | 0.494 |
| FAR | 0.616 | 0.504 | 0.422 | 0.497 |
| freq_bias | 0.996 | 0.961 | 1.022 | 0.982 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1664 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.382.
- **Spread / RMSE**: 0.925 (spread 0.821, ens-mean RMSE 0.888). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.299 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0630, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.656 | 0.758 | 0.816 | 0.865 | 0.920 | 0.950 |
| mean, 1 mm/h | 0.595 | 0.714 | 0.782 | 0.842 | 0.911 | 0.947 |
| mean, 2 mm/h | 0.478 | 0.617 | 0.700 | 0.775 | 0.867 | 0.916 |
| mean, 4 mm/h | 0.340 | 0.485 | 0.575 | 0.663 | 0.777 | 0.835 |
| mean, 8 mm/h | 0.211 | 0.305 | 0.371 | 0.461 | 0.577 | 0.617 |
| member, 0.5 mm/h | 0.594 | 0.705 | 0.778 | 0.844 | 0.921 | 0.961 |
| member, 1 mm/h | 0.510 | 0.639 | 0.725 | 0.804 | 0.900 | 0.950 |
| member, 2 mm/h | 0.390 | 0.532 | 0.632 | 0.728 | 0.852 | 0.921 |
| member, 4 mm/h | 0.268 | 0.412 | 0.518 | 0.629 | 0.780 | 0.867 |
| member, 8 mm/h | 0.160 | 0.266 | 0.370 | 0.510 | 0.704 | 0.803 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.011 | 1.163 | 1.201 | 1.190 | 0.968 | 1.129 | 1.010 |
| model_mean | 0.799 | 0.334 | 0.273 | 0.253 | 0.210 | 0.241 | 0.219 |
| advection | 1.014 | 1.160 | 1.046 | 0.851 | 0.480 | 0.749 | 0.559 |
| persistence | 0.926 | 0.980 | 0.983 | 0.994 | 0.943 | 0.980 | 0.953 |
| _obs share of variance_ | 89.0% | 6.0% | 3.2% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 33.3 |
| model_member | 22.5 |
| advection | 21.6 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
