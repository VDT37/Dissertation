# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.40331254275482054). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.333 | 0.253 | **0.214** | 0.265 |
| RMSE (mm/h) | 1.203 | 0.992 | **0.790** | 1.058 |
| bias (mm/h) | -0.001 | -0.015 | +0.008 | +0.008 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.388 | 0.532 | 0.592 | 0.522 |
| 1 | 0.311 | 0.446 | 0.528 | 0.439 |
| 2 | 0.213 | 0.320 | 0.411 | 0.322 |
| 4 | 0.129 | 0.186 | 0.268 | 0.201 |
| 8 | 0.072 | 0.088 | 0.145 | 0.107 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.474 | 0.609 | 0.717 | 0.618 |
| FAR | 0.525 | 0.374 | 0.334 | 0.396 |
| freq_bias | 0.996 | 0.973 | 1.076 | 1.023 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1324 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.253 and persistence 0.333.
- **Spread / RMSE**: 0.953 (spread 0.752, ens-mean RMSE 0.790). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.254 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0400, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.745 | 0.849 | 0.897 | 0.932 | 0.965 | 0.978 |
| mean, 1 mm/h | 0.692 | 0.815 | 0.874 | 0.917 | 0.959 | 0.977 |
| mean, 2 mm/h | 0.597 | 0.750 | 0.828 | 0.887 | 0.943 | 0.967 |
| mean, 4 mm/h | 0.462 | 0.644 | 0.742 | 0.821 | 0.897 | 0.930 |
| mean, 8 mm/h | 0.303 | 0.472 | 0.583 | 0.688 | 0.796 | 0.836 |
| member, 0.5 mm/h | 0.687 | 0.809 | 0.873 | 0.922 | 0.968 | 0.986 |
| member, 1 mm/h | 0.613 | 0.758 | 0.837 | 0.897 | 0.956 | 0.981 |
| member, 2 mm/h | 0.502 | 0.673 | 0.771 | 0.849 | 0.929 | 0.965 |
| member, 4 mm/h | 0.366 | 0.554 | 0.675 | 0.779 | 0.890 | 0.938 |
| member, 8 mm/h | 0.236 | 0.404 | 0.534 | 0.661 | 0.808 | 0.867 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.090 | 1.125 | 1.138 | 1.161 | 1.064 | 1.134 | 1.069 |
| model_mean | 0.954 | 0.541 | 0.365 | 0.295 | 0.261 | 0.286 | 0.266 |
| advection | 0.960 | 1.036 | 0.954 | 0.775 | 0.444 | 0.684 | 0.511 |
| persistence | 0.952 | 1.002 | 0.991 | 0.969 | 0.934 | 0.959 | 0.938 |
| _obs share of variance_ | 88.8% | 6.0% | 3.2% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| model_mean | 29.8 |
| model_member | 22.8 |
| advection | 22.1 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
