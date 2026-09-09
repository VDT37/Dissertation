# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 15 (val loss 0.4062583218950657). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.362 | 0.293 | **0.244** | 0.297 |
| RMSE (mm/h) | 1.251 | 1.081 | **0.849** | 1.130 |
| bias (mm/h) | -0.001 | -0.016 | +0.000 | +0.000 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.341 | 0.459 | 0.529 | 0.459 |
| 1 | 0.267 | 0.374 | 0.462 | 0.377 |
| 2 | 0.175 | 0.253 | 0.342 | 0.265 |
| 4 | 0.104 | 0.137 | 0.206 | 0.158 |
| 8 | 0.058 | 0.057 | 0.099 | 0.078 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.420 | 0.536 | 0.647 | 0.546 |
| FAR | 0.578 | 0.448 | 0.383 | 0.452 |
| freq_bias | 0.995 | 0.970 | 1.048 | 0.997 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1520 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.293 and persistence 0.362.
- **Spread / RMSE**: 0.938 (spread 0.796, ens-mean RMSE 0.849). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.280 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0534, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.697 | 0.800 | 0.855 | 0.898 | 0.943 | 0.965 |
| mean, 1 mm/h | 0.639 | 0.759 | 0.825 | 0.878 | 0.935 | 0.963 |
| mean, 2 mm/h | 0.531 | 0.677 | 0.759 | 0.828 | 0.905 | 0.944 |
| mean, 4 mm/h | 0.390 | 0.553 | 0.649 | 0.735 | 0.834 | 0.880 |
| mean, 8 mm/h | 0.246 | 0.374 | 0.468 | 0.576 | 0.707 | 0.757 |
| member, 0.5 mm/h | 0.635 | 0.752 | 0.823 | 0.883 | 0.945 | 0.974 |
| member, 1 mm/h | 0.554 | 0.691 | 0.775 | 0.848 | 0.928 | 0.966 |
| member, 2 mm/h | 0.436 | 0.591 | 0.693 | 0.784 | 0.891 | 0.945 |
| member, 4 mm/h | 0.306 | 0.469 | 0.584 | 0.696 | 0.834 | 0.903 |
| member, 8 mm/h | 0.183 | 0.313 | 0.430 | 0.574 | 0.754 | 0.835 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.010 | 1.111 | 1.151 | 1.132 | 0.972 | 1.088 | 0.997 |
| model_mean | 0.843 | 0.407 | 0.306 | 0.266 | 0.220 | 0.253 | 0.229 |
| advection | 0.975 | 1.123 | 1.062 | 0.855 | 0.465 | 0.746 | 0.547 |
| persistence | 0.907 | 0.962 | 1.010 | 0.994 | 0.928 | 0.975 | 0.943 |
| _obs share of variance_ | 89.1% | 6.0% | 3.0% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 31.5 |
| model_member | 22.6 |
| advection | 21.9 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
