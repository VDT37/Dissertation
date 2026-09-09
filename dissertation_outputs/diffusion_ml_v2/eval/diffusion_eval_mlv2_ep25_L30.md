# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.3324181713280408). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.333 | 0.253 | **0.220** | 0.273 |
| RMSE (mm/h) | 1.203 | 0.992 | **0.801** | 1.073 |
| bias (mm/h) | -0.001 | -0.015 | +0.007 | +0.007 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.388 | 0.532 | 0.580 | 0.507 |
| 1 | 0.311 | 0.446 | 0.514 | 0.423 |
| 2 | 0.213 | 0.320 | 0.395 | 0.307 |
| 4 | 0.129 | 0.186 | 0.255 | 0.192 |
| 8 | 0.072 | 0.088 | 0.134 | 0.101 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.474 | 0.609 | 0.704 | 0.600 |
| FAR | 0.525 | 0.374 | 0.345 | 0.411 |
| freq_bias | 0.996 | 0.973 | 1.074 | 1.019 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1359 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.253 and persistence 0.333.
- **Spread / RMSE**: 0.951 (spread 0.762, ens-mean RMSE 0.801). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.252 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0420, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.735 | 0.838 | 0.888 | 0.925 | 0.960 | 0.975 |
| mean, 1 mm/h | 0.679 | 0.802 | 0.863 | 0.909 | 0.954 | 0.973 |
| mean, 2 mm/h | 0.580 | 0.733 | 0.813 | 0.875 | 0.937 | 0.963 |
| mean, 4 mm/h | 0.445 | 0.625 | 0.724 | 0.805 | 0.884 | 0.920 |
| mean, 8 mm/h | 0.289 | 0.454 | 0.568 | 0.679 | 0.791 | 0.826 |
| member, 0.5 mm/h | 0.673 | 0.794 | 0.859 | 0.910 | 0.961 | 0.982 |
| member, 1 mm/h | 0.596 | 0.739 | 0.819 | 0.883 | 0.948 | 0.976 |
| member, 2 mm/h | 0.482 | 0.650 | 0.749 | 0.830 | 0.916 | 0.956 |
| member, 4 mm/h | 0.350 | 0.532 | 0.651 | 0.757 | 0.875 | 0.930 |
| member, 8 mm/h | 0.228 | 0.392 | 0.520 | 0.652 | 0.806 | 0.866 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.061 | 1.092 | 1.085 | 1.043 | 0.905 | 1.005 | 0.924 |
| model_mean | 0.920 | 0.520 | 0.351 | 0.273 | 0.231 | 0.261 | 0.238 |
| advection | 0.960 | 1.036 | 0.954 | 0.775 | 0.444 | 0.684 | 0.511 |
| persistence | 0.952 | 1.002 | 0.991 | 0.969 | 0.934 | 0.959 | 0.938 |
| _obs share of variance_ | 88.8% | 6.0% | 3.2% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| model_mean | 30.2 |
| model_member | 22.8 |
| advection | 22.1 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
