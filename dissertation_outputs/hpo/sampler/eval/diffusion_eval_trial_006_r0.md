# Diffusion nowcast scorecard (`val` split)

_3000 crops, 8-member ensembles, 25 Heun steps, guidance 1.5. Checkpoint epoch 50 (val loss 0.3314065786726351). FSS from 429 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.379 | 0.323 | **0.272** | 0.313 |
| RMSE (mm/h) | 1.261 | 1.129 | **0.890** | 1.121 |
| bias (mm/h) | +0.000 | -0.017 | -0.016 | -0.016 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.318 | 0.410 | 0.470 | 0.411 |
| 1 | 0.246 | 0.326 | 0.393 | 0.330 |
| 2 | 0.159 | 0.209 | 0.262 | 0.224 |
| 4 | 0.093 | 0.106 | 0.143 | 0.132 |
| 8 | 0.050 | 0.040 | 0.071 | 0.066 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.395 | 0.482 | 0.556 | 0.498 |
| FAR | 0.604 | 0.499 | 0.428 | 0.507 |
| freq_bias | 0.997 | 0.962 | 0.972 | 1.010 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1751 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.379.
- **Spread / RMSE**: 0.818 (spread 0.728, ens-mean RMSE 0.890). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.349 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0698, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.641 | 0.736 | 0.794 | 0.846 | 0.909 | 0.943 |
| mean, 1 mm/h | 0.565 | 0.674 | 0.741 | 0.803 | 0.883 | 0.930 |
| mean, 2 mm/h | 0.415 | 0.538 | 0.618 | 0.698 | 0.809 | 0.874 |
| mean, 4 mm/h | 0.254 | 0.363 | 0.435 | 0.518 | 0.636 | 0.701 |
| mean, 8 mm/h | 0.140 | 0.213 | 0.279 | 0.372 | 0.512 | 0.570 |
| member, 0.5 mm/h | 0.587 | 0.683 | 0.748 | 0.812 | 0.896 | 0.943 |
| member, 1 mm/h | 0.499 | 0.607 | 0.681 | 0.756 | 0.859 | 0.921 |
| member, 2 mm/h | 0.361 | 0.479 | 0.561 | 0.649 | 0.781 | 0.869 |
| member, 4 mm/h | 0.234 | 0.351 | 0.437 | 0.540 | 0.695 | 0.788 |
| member, 8 mm/h | 0.129 | 0.213 | 0.290 | 0.399 | 0.592 | 0.704 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 0.836 | 0.929 | 0.997 | 1.010 | 0.941 | 0.993 | 0.936 |
| model_mean | 0.661 | 0.294 | 0.242 | 0.219 | 0.220 | 0.219 | 0.216 |
| advection | 1.015 | 1.019 | 0.905 | 0.805 | 0.570 | 0.747 | 0.610 |
| persistence | 1.052 | 1.134 | 1.096 | 1.114 | 1.190 | 1.133 | 1.173 |
| _obs share of variance_ | 88.4% | 6.4% | 3.4% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.2 |
| model_mean | 34.2 |
| model_member | 22.7 |
| advection | 21.7 |
| persistence | 23.1 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
