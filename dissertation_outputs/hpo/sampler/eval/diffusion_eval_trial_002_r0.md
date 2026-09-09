# Diffusion nowcast scorecard (`val` split)

_3000 crops, 8-member ensembles, 50 Heun steps, guidance 1.0. Checkpoint epoch 50 (val loss 0.3314065786726351). FSS from 429 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.379 | 0.323 | **0.273** | 0.328 |
| RMSE (mm/h) | 1.261 | 1.129 | **0.883** | 1.149 |
| bias (mm/h) | +0.000 | -0.017 | +0.001 | +0.001 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.318 | 0.410 | 0.477 | 0.405 |
| 1 | 0.246 | 0.326 | 0.407 | 0.325 |
| 2 | 0.159 | 0.209 | 0.286 | 0.222 |
| 4 | 0.093 | 0.106 | 0.165 | 0.131 |
| 8 | 0.050 | 0.040 | 0.080 | 0.065 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.395 | 0.482 | 0.589 | 0.492 |
| FAR | 0.604 | 0.499 | 0.432 | 0.510 |
| freq_bias | 0.997 | 0.962 | 1.038 | 1.003 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1690 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.379.
- **Spread / RMSE**: 0.892 (spread 0.787, ens-mean RMSE 0.883). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.291 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0608, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.649 | 0.749 | 0.806 | 0.855 | 0.913 | 0.945 |
| mean, 1 mm/h | 0.579 | 0.692 | 0.758 | 0.817 | 0.890 | 0.933 |
| mean, 2 mm/h | 0.443 | 0.572 | 0.651 | 0.727 | 0.831 | 0.895 |
| mean, 4 mm/h | 0.293 | 0.423 | 0.506 | 0.596 | 0.723 | 0.794 |
| mean, 8 mm/h | 0.171 | 0.276 | 0.368 | 0.484 | 0.662 | 0.752 |
| member, 0.5 mm/h | 0.582 | 0.690 | 0.760 | 0.825 | 0.905 | 0.949 |
| member, 1 mm/h | 0.495 | 0.616 | 0.696 | 0.773 | 0.872 | 0.930 |
| member, 2 mm/h | 0.360 | 0.489 | 0.579 | 0.670 | 0.799 | 0.882 |
| member, 4 mm/h | 0.234 | 0.363 | 0.461 | 0.572 | 0.738 | 0.837 |
| member, 8 mm/h | 0.126 | 0.223 | 0.315 | 0.436 | 0.645 | 0.770 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 0.980 | 1.059 | 1.002 | 0.915 | 0.826 | 0.893 | 0.828 |
| model_mean | 0.770 | 0.306 | 0.228 | 0.208 | 0.208 | 0.208 | 0.204 |
| advection | 1.015 | 1.019 | 0.905 | 0.805 | 0.570 | 0.747 | 0.610 |
| persistence | 1.052 | 1.134 | 1.096 | 1.114 | 1.190 | 1.133 | 1.173 |
| _obs share of variance_ | 88.4% | 6.4% | 3.4% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.2 |
| model_mean | 34.2 |
| model_member | 22.6 |
| advection | 21.7 |
| persistence | 23.1 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
