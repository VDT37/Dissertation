# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.3324181713280408). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.281 | 0.193 | **0.169** | 0.215 |
| RMSE (mm/h) | 1.103 | 0.831 | **0.692** | 0.923 |
| bias (mm/h) | -0.001 | -0.015 | +0.006 | +0.006 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.476 | 0.641 | 0.678 | 0.611 |
| 1 | 0.396 | 0.559 | 0.615 | 0.530 |
| 2 | 0.290 | 0.433 | 0.504 | 0.410 |
| 4 | 0.187 | 0.284 | 0.362 | 0.276 |
| 8 | 0.107 | 0.168 | 0.225 | 0.164 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.567 | 0.708 | 0.786 | 0.700 |
| FAR | 0.432 | 0.273 | 0.261 | 0.315 |
| freq_bias | 0.998 | 0.974 | 1.064 | 1.021 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1068 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.193 and persistence 0.281.
- **Spread / RMSE**: 0.941 (spread 0.652, ens-mean RMSE 0.692). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.236 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0275, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.806 | 0.907 | 0.945 | 0.967 | 0.984 | 0.990 |
| mean, 1 mm/h | 0.761 | 0.884 | 0.931 | 0.959 | 0.982 | 0.989 |
| mean, 2 mm/h | 0.680 | 0.839 | 0.903 | 0.942 | 0.974 | 0.986 |
| mean, 4 mm/h | 0.563 | 0.765 | 0.851 | 0.907 | 0.952 | 0.968 |
| mean, 8 mm/h | 0.418 | 0.638 | 0.750 | 0.830 | 0.901 | 0.926 |
| member, 0.5 mm/h | 0.757 | 0.879 | 0.930 | 0.962 | 0.986 | 0.994 |
| member, 1 mm/h | 0.692 | 0.843 | 0.907 | 0.948 | 0.981 | 0.991 |
| member, 2 mm/h | 0.592 | 0.780 | 0.865 | 0.921 | 0.967 | 0.983 |
| member, 4 mm/h | 0.464 | 0.690 | 0.804 | 0.882 | 0.948 | 0.971 |
| member, 8 mm/h | 0.334 | 0.567 | 0.705 | 0.809 | 0.902 | 0.936 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.050 | 1.047 | 1.049 | 1.009 | 0.932 | 0.988 | 0.938 |
| model_mean | 0.984 | 0.666 | 0.477 | 0.318 | 0.252 | 0.300 | 0.265 |
| advection | 0.955 | 0.923 | 0.876 | 0.729 | 0.425 | 0.647 | 0.487 |
| persistence | 0.986 | 0.977 | 0.991 | 0.985 | 0.959 | 0.978 | 0.962 |
| _obs share of variance_ | 88.3% | 6.4% | 3.3% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| model_mean | 26.9 |
| model_member | 22.7 |
| advection | 22.3 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
