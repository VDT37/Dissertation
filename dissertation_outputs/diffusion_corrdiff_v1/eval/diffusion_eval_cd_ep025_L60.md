# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.40331254275482054). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.382 | 0.323 | **0.271** | 0.326 |
| RMSE (mm/h) | 1.283 | 1.140 | **0.889** | 1.183 |
| bias (mm/h) | -0.001 | -0.019 | +0.003 | +0.003 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.307 | 0.404 | 0.480 | 0.410 |
| 1 | 0.237 | 0.321 | 0.413 | 0.330 |
| 2 | 0.153 | 0.207 | 0.295 | 0.227 |
| 4 | 0.089 | 0.105 | 0.172 | 0.133 |
| 8 | 0.048 | 0.040 | 0.082 | 0.065 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.383 | 0.477 | 0.596 | 0.496 |
| FAR | 0.616 | 0.504 | 0.426 | 0.503 |
| freq_bias | 0.996 | 0.961 | 1.038 | 0.999 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1660 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.382.
- **Spread / RMSE**: 0.938 (spread 0.834, ens-mean RMSE 0.889). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.290 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0610, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.655 | 0.756 | 0.814 | 0.863 | 0.918 | 0.947 |
| mean, 1 mm/h | 0.595 | 0.713 | 0.781 | 0.840 | 0.909 | 0.946 |
| mean, 2 mm/h | 0.481 | 0.619 | 0.701 | 0.776 | 0.867 | 0.916 |
| mean, 4 mm/h | 0.347 | 0.493 | 0.583 | 0.671 | 0.786 | 0.845 |
| mean, 8 mm/h | 0.223 | 0.324 | 0.396 | 0.492 | 0.611 | 0.645 |
| member, 0.5 mm/h | 0.592 | 0.702 | 0.774 | 0.840 | 0.919 | 0.960 |
| member, 1 mm/h | 0.509 | 0.636 | 0.720 | 0.800 | 0.897 | 0.948 |
| member, 2 mm/h | 0.390 | 0.529 | 0.626 | 0.721 | 0.845 | 0.917 |
| member, 4 mm/h | 0.268 | 0.408 | 0.512 | 0.621 | 0.771 | 0.859 |
| member, 8 mm/h | 0.165 | 0.270 | 0.371 | 0.507 | 0.698 | 0.795 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.051 | 1.172 | 1.183 | 1.150 | 0.961 | 1.098 | 0.996 |
| model_mean | 0.830 | 0.347 | 0.279 | 0.257 | 0.219 | 0.246 | 0.226 |
| advection | 1.014 | 1.160 | 1.046 | 0.851 | 0.480 | 0.749 | 0.559 |
| persistence | 0.926 | 0.980 | 0.983 | 0.994 | 0.943 | 0.980 | 0.953 |
| _obs share of variance_ | 89.0% | 6.0% | 3.2% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 34.0 |
| model_member | 22.7 |
| advection | 21.6 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
