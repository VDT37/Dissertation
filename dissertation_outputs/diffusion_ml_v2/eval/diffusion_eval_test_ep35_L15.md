# Diffusion nowcast scorecard (`test` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 35 (val loss 0.33152407111889187). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.245 | 0.163 | **0.144** | 0.183 |
| RMSE (mm/h) | 1.147 | 0.854 | **0.731** | 0.979 |
| bias (mm/h) | -0.002 | -0.015 | +0.000 | +0.000 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.452 | 0.619 | 0.661 | 0.587 |
| 1 | 0.368 | 0.539 | 0.596 | 0.507 |
| 2 | 0.267 | 0.431 | 0.496 | 0.400 |
| 4 | 0.166 | 0.288 | 0.345 | 0.264 |
| 8 | 0.098 | 0.196 | 0.229 | 0.163 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.536 | 0.689 | 0.760 | 0.677 |
| FAR | 0.461 | 0.288 | 0.266 | 0.331 |
| freq_bias | 0.995 | 0.967 | 1.035 | 1.012 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.0921 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.163 and persistence 0.245.
- **Spread / RMSE**: 0.951 (spread 0.695, ens-mean RMSE 0.731). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.237 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0309, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.793 | 0.903 | 0.944 | 0.968 | 0.985 | 0.991 |
| mean, 1 mm/h | 0.742 | 0.876 | 0.927 | 0.958 | 0.981 | 0.990 |
| mean, 2 mm/h | 0.652 | 0.822 | 0.891 | 0.935 | 0.970 | 0.983 |
| mean, 4 mm/h | 0.495 | 0.711 | 0.811 | 0.877 | 0.934 | 0.957 |
| mean, 8 mm/h | 0.329 | 0.549 | 0.671 | 0.759 | 0.837 | 0.862 |
| member, 0.5 mm/h | 0.737 | 0.871 | 0.927 | 0.961 | 0.986 | 0.994 |
| member, 1 mm/h | 0.665 | 0.829 | 0.900 | 0.944 | 0.978 | 0.990 |
| member, 2 mm/h | 0.556 | 0.756 | 0.851 | 0.912 | 0.963 | 0.981 |
| member, 4 mm/h | 0.404 | 0.639 | 0.766 | 0.853 | 0.928 | 0.958 |
| member, 8 mm/h | 0.255 | 0.483 | 0.637 | 0.754 | 0.861 | 0.907 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.060 | 1.043 | 1.043 | 1.062 | 1.020 | 1.051 | 1.014 |
| model_mean | 0.972 | 0.669 | 0.452 | 0.292 | 0.212 | 0.272 | 0.227 |
| advection | 0.937 | 0.920 | 0.878 | 0.734 | 0.428 | 0.656 | 0.491 |
| persistence | 0.961 | 0.969 | 0.977 | 0.950 | 0.947 | 0.949 | 0.948 |
| _obs share of variance_ | 90.0% | 6.0% | 2.7% | 1.0% | 0.3% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 22.4 |
| model_mean | 25.5 |
| model_member | 22.0 |
| advection | 21.5 |
| persistence | 22.3 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
