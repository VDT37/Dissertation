# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.40331254275482054). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.281 | 0.193 | **0.166** | 0.210 |
| RMSE (mm/h) | 1.103 | 0.831 | **0.684** | 0.912 |
| bias (mm/h) | -0.001 | -0.015 | +0.009 | +0.009 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.476 | 0.641 | 0.686 | 0.621 |
| 1 | 0.396 | 0.559 | 0.624 | 0.541 |
| 2 | 0.290 | 0.433 | 0.515 | 0.420 |
| 4 | 0.187 | 0.284 | 0.372 | 0.285 |
| 8 | 0.107 | 0.168 | 0.235 | 0.170 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.567 | 0.708 | 0.795 | 0.711 |
| FAR | 0.432 | 0.273 | 0.257 | 0.307 |
| freq_bias | 0.998 | 0.974 | 1.070 | 1.027 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1044 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.193 and persistence 0.281.
- **Spread / RMSE**: 0.942 (spread 0.644, ens-mean RMSE 0.684). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.235 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0254, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.812 | 0.912 | 0.949 | 0.970 | 0.986 | 0.991 |
| mean, 1 mm/h | 0.767 | 0.890 | 0.935 | 0.962 | 0.983 | 0.990 |
| mean, 2 mm/h | 0.690 | 0.848 | 0.909 | 0.947 | 0.976 | 0.987 |
| mean, 4 mm/h | 0.574 | 0.775 | 0.860 | 0.914 | 0.956 | 0.972 |
| mean, 8 mm/h | 0.428 | 0.648 | 0.757 | 0.834 | 0.904 | 0.932 |
| member, 0.5 mm/h | 0.764 | 0.887 | 0.936 | 0.966 | 0.988 | 0.995 |
| member, 1 mm/h | 0.700 | 0.851 | 0.914 | 0.953 | 0.983 | 0.992 |
| member, 2 mm/h | 0.603 | 0.792 | 0.877 | 0.930 | 0.972 | 0.986 |
| member, 4 mm/h | 0.475 | 0.704 | 0.818 | 0.893 | 0.953 | 0.975 |
| member, 8 mm/h | 0.337 | 0.571 | 0.708 | 0.813 | 0.905 | 0.940 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.081 | 1.075 | 1.083 | 1.054 | 0.996 | 1.038 | 0.997 |
| model_mean | 1.015 | 0.699 | 0.496 | 0.334 | 0.274 | 0.318 | 0.284 |
| advection | 0.955 | 0.923 | 0.876 | 0.729 | 0.425 | 0.647 | 0.487 |
| persistence | 0.986 | 0.977 | 0.991 | 0.985 | 0.959 | 0.978 | 0.962 |
| _obs share of variance_ | 88.3% | 6.4% | 3.3% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| model_mean | 26.8 |
| model_member | 22.8 |
| advection | 22.3 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
