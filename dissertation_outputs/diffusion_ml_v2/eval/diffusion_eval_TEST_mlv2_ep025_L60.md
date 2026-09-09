# Diffusion nowcast scorecard (`test` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.3324181713280408). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.337 | 0.278 | **0.248** | 0.299 |
| RMSE (mm/h) | 1.327 | 1.183 | **0.948** | 1.235 |
| bias (mm/h) | -0.004 | -0.022 | -0.002 | -0.002 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.280 | 0.379 | 0.435 | 0.356 |
| 1 | 0.208 | 0.296 | 0.361 | 0.277 |
| 2 | 0.132 | 0.199 | 0.249 | 0.188 |
| 4 | 0.071 | 0.102 | 0.128 | 0.103 |
| 8 | 0.035 | 0.045 | 0.056 | 0.047 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.341 | 0.443 | 0.528 | 0.434 |
| FAR | 0.653 | 0.528 | 0.466 | 0.565 |
| freq_bias | 0.984 | 0.939 | 0.989 | 0.998 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1522 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.278 and persistence 0.337.
- **Spread / RMSE**: 0.892 (spread 0.846, ens-mean RMSE 0.948). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.286 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0665, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.601 | 0.708 | 0.770 | 0.825 | 0.892 | 0.927 |
| mean, 1 mm/h | 0.519 | 0.641 | 0.714 | 0.781 | 0.865 | 0.914 |
| mean, 2 mm/h | 0.376 | 0.505 | 0.589 | 0.669 | 0.776 | 0.846 |
| mean, 4 mm/h | 0.205 | 0.318 | 0.402 | 0.490 | 0.601 | 0.670 |
| mean, 8 mm/h | 0.061 | 0.094 | 0.133 | 0.172 | 0.209 | 0.232 |
| member, 0.5 mm/h | 0.514 | 0.627 | 0.703 | 0.778 | 0.877 | 0.931 |
| member, 1 mm/h | 0.419 | 0.542 | 0.629 | 0.716 | 0.835 | 0.903 |
| member, 2 mm/h | 0.296 | 0.420 | 0.513 | 0.609 | 0.752 | 0.848 |
| member, 4 mm/h | 0.161 | 0.263 | 0.349 | 0.446 | 0.594 | 0.715 |
| member, 8 mm/h | 0.068 | 0.120 | 0.176 | 0.242 | 0.345 | 0.476 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 0.992 | 1.049 | 1.038 | 1.102 | 1.082 | 1.097 | 1.082 |
| model_mean | 0.681 | 0.248 | 0.189 | 0.189 | 0.161 | 0.182 | 0.165 |
| advection | 0.891 | 0.904 | 0.833 | 0.718 | 0.437 | 0.646 | 0.496 |
| persistence | 0.908 | 0.905 | 0.869 | 0.859 | 0.854 | 0.858 | 0.859 |
| _obs share of variance_ | 89.7% | 6.0% | 2.9% | 1.0% | 0.4% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 22.6 |
| model_mean | 33.4 |
| model_member | 22.0 |
| advection | 20.8 |
| persistence | 22.3 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
