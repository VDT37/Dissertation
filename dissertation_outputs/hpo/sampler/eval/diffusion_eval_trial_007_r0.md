# Diffusion nowcast scorecard (`val` split)

_3000 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 50 (val loss 0.3314065786726351). FSS from 429 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.379 | 0.323 | **0.282** | 0.342 |
| RMSE (mm/h) | 1.261 | 1.129 | **0.893** | 1.211 |
| bias (mm/h) | +0.000 | -0.017 | +0.018 | +0.018 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.318 | 0.410 | 0.474 | 0.402 |
| 1 | 0.246 | 0.326 | 0.406 | 0.321 |
| 2 | 0.159 | 0.209 | 0.287 | 0.218 |
| 4 | 0.093 | 0.106 | 0.168 | 0.128 |
| 8 | 0.050 | 0.040 | 0.079 | 0.062 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.395 | 0.482 | 0.606 | 0.497 |
| FAR | 0.604 | 0.499 | 0.449 | 0.524 |
| freq_bias | 0.997 | 0.962 | 1.099 | 1.043 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1684 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.379.
- **Spread / RMSE**: 0.979 (spread 0.875, ens-mean RMSE 0.893). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.270 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0564, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.644 | 0.745 | 0.802 | 0.850 | 0.907 | 0.938 |
| mean, 1 mm/h | 0.577 | 0.692 | 0.758 | 0.816 | 0.888 | 0.929 |
| mean, 2 mm/h | 0.441 | 0.574 | 0.655 | 0.730 | 0.831 | 0.896 |
| mean, 4 mm/h | 0.292 | 0.424 | 0.506 | 0.592 | 0.717 | 0.795 |
| mean, 8 mm/h | 0.151 | 0.237 | 0.310 | 0.408 | 0.563 | 0.633 |
| member, 0.5 mm/h | 0.577 | 0.686 | 0.757 | 0.823 | 0.902 | 0.946 |
| member, 1 mm/h | 0.489 | 0.611 | 0.692 | 0.769 | 0.869 | 0.926 |
| member, 2 mm/h | 0.357 | 0.489 | 0.582 | 0.674 | 0.804 | 0.885 |
| member, 4 mm/h | 0.229 | 0.358 | 0.455 | 0.563 | 0.725 | 0.828 |
| member, 8 mm/h | 0.124 | 0.221 | 0.313 | 0.433 | 0.642 | 0.766 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.105 | 1.290 | 1.292 | 1.282 | 1.161 | 1.252 | 1.170 |
| model_mean | 0.811 | 0.352 | 0.260 | 0.245 | 0.227 | 0.241 | 0.227 |
| advection | 1.015 | 1.019 | 0.905 | 0.805 | 0.570 | 0.747 | 0.610 |
| persistence | 1.052 | 1.134 | 1.096 | 1.114 | 1.190 | 1.133 | 1.173 |
| _obs share of variance_ | 88.4% | 6.4% | 3.4% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.2 |
| model_mean | 35.3 |
| model_member | 22.8 |
| advection | 21.7 |
| persistence | 23.1 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
