# Diffusion nowcast scorecard (`val` split)

_3000 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 50 (val loss 0.3314065786726351). FSS from 429 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.379 | 0.323 | **0.275** | 0.332 |
| RMSE (mm/h) | 1.261 | 1.129 | **0.885** | 1.166 |
| bias (mm/h) | +0.000 | -0.017 | +0.004 | +0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.318 | 0.410 | 0.475 | 0.404 |
| 1 | 0.246 | 0.326 | 0.406 | 0.324 |
| 2 | 0.159 | 0.209 | 0.286 | 0.220 |
| 4 | 0.093 | 0.106 | 0.165 | 0.130 |
| 8 | 0.050 | 0.040 | 0.080 | 0.064 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.395 | 0.482 | 0.592 | 0.492 |
| FAR | 0.604 | 0.499 | 0.437 | 0.514 |
| freq_bias | 0.997 | 0.962 | 1.052 | 1.011 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1690 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.379.
- **Spread / RMSE**: 0.916 (spread 0.811, ens-mean RMSE 0.885). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.286 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0599, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.647 | 0.748 | 0.805 | 0.854 | 0.912 | 0.943 |
| mean, 1 mm/h | 0.578 | 0.692 | 0.758 | 0.817 | 0.890 | 0.932 |
| mean, 2 mm/h | 0.443 | 0.573 | 0.652 | 0.728 | 0.832 | 0.896 |
| mean, 4 mm/h | 0.292 | 0.423 | 0.507 | 0.597 | 0.724 | 0.795 |
| mean, 8 mm/h | 0.170 | 0.276 | 0.368 | 0.484 | 0.662 | 0.752 |
| member, 0.5 mm/h | 0.581 | 0.689 | 0.759 | 0.824 | 0.905 | 0.949 |
| member, 1 mm/h | 0.493 | 0.614 | 0.695 | 0.772 | 0.871 | 0.930 |
| member, 2 mm/h | 0.357 | 0.487 | 0.577 | 0.669 | 0.798 | 0.881 |
| member, 4 mm/h | 0.232 | 0.361 | 0.459 | 0.569 | 0.736 | 0.836 |
| member, 8 mm/h | 0.123 | 0.220 | 0.312 | 0.432 | 0.641 | 0.766 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 0.999 | 1.108 | 1.064 | 0.988 | 0.893 | 0.964 | 0.894 |
| model_mean | 0.781 | 0.315 | 0.238 | 0.221 | 0.220 | 0.221 | 0.217 |
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
