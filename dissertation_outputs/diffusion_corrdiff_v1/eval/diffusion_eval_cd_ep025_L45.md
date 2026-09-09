# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.40331254275482054). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.362 | 0.293 | **0.247** | 0.301 |
| RMSE (mm/h) | 1.251 | 1.081 | **0.849** | 1.135 |
| bias (mm/h) | -0.001 | -0.016 | +0.006 | +0.006 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.341 | 0.459 | 0.528 | 0.457 |
| 1 | 0.267 | 0.374 | 0.462 | 0.376 |
| 2 | 0.175 | 0.253 | 0.344 | 0.265 |
| 4 | 0.104 | 0.137 | 0.210 | 0.159 |
| 8 | 0.058 | 0.057 | 0.104 | 0.080 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.420 | 0.536 | 0.652 | 0.550 |
| FAR | 0.578 | 0.448 | 0.387 | 0.457 |
| freq_bias | 0.995 | 0.970 | 1.063 | 1.013 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1517 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.293 and persistence 0.362.
- **Spread / RMSE**: 0.947 (spread 0.804, ens-mean RMSE 0.849). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.273 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0515, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.695 | 0.798 | 0.853 | 0.896 | 0.941 | 0.963 |
| mean, 1 mm/h | 0.639 | 0.759 | 0.824 | 0.877 | 0.934 | 0.962 |
| mean, 2 mm/h | 0.534 | 0.679 | 0.761 | 0.828 | 0.905 | 0.944 |
| mean, 4 mm/h | 0.395 | 0.557 | 0.652 | 0.738 | 0.838 | 0.884 |
| mean, 8 mm/h | 0.257 | 0.393 | 0.492 | 0.603 | 0.734 | 0.780 |
| member, 0.5 mm/h | 0.634 | 0.750 | 0.821 | 0.880 | 0.944 | 0.974 |
| member, 1 mm/h | 0.554 | 0.689 | 0.773 | 0.845 | 0.927 | 0.965 |
| member, 2 mm/h | 0.436 | 0.590 | 0.690 | 0.780 | 0.887 | 0.943 |
| member, 4 mm/h | 0.308 | 0.468 | 0.581 | 0.691 | 0.829 | 0.899 |
| member, 8 mm/h | 0.190 | 0.321 | 0.437 | 0.576 | 0.748 | 0.822 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.054 | 1.150 | 1.183 | 1.155 | 0.996 | 1.111 | 1.021 |
| model_mean | 0.878 | 0.424 | 0.315 | 0.273 | 0.232 | 0.262 | 0.239 |
| advection | 0.975 | 1.123 | 1.062 | 0.855 | 0.465 | 0.746 | 0.547 |
| persistence | 0.907 | 0.962 | 1.010 | 0.994 | 0.928 | 0.975 | 0.943 |
| _obs share of variance_ | 89.1% | 6.0% | 3.0% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 32.1 |
| model_member | 22.8 |
| advection | 21.9 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
