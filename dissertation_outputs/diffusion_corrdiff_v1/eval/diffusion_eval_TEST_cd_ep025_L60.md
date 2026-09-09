# Diffusion nowcast scorecard (`test` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.40331254275482054). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.337 | 0.278 | **0.238** | 0.287 |
| RMSE (mm/h) | 1.327 | 1.183 | **0.931** | 1.213 |
| bias (mm/h) | -0.004 | -0.022 | -0.004 | -0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.280 | 0.379 | 0.454 | 0.377 |
| 1 | 0.208 | 0.296 | 0.382 | 0.298 |
| 2 | 0.132 | 0.199 | 0.270 | 0.205 |
| 4 | 0.071 | 0.102 | 0.143 | 0.113 |
| 8 | 0.035 | 0.045 | 0.066 | 0.053 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.341 | 0.443 | 0.548 | 0.457 |
| FAR | 0.653 | 0.528 | 0.443 | 0.539 |
| freq_bias | 0.984 | 0.939 | 0.985 | 0.992 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1472 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.278 and persistence 0.337.
- **Spread / RMSE**: 0.893 (spread 0.831, ens-mean RMSE 0.931). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.289 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0643, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.619 | 0.728 | 0.791 | 0.845 | 0.908 | 0.941 |
| mean, 1 mm/h | 0.542 | 0.666 | 0.740 | 0.805 | 0.884 | 0.928 |
| mean, 2 mm/h | 0.400 | 0.534 | 0.621 | 0.702 | 0.804 | 0.867 |
| mean, 4 mm/h | 0.236 | 0.364 | 0.460 | 0.561 | 0.693 | 0.765 |
| mean, 8 mm/h | 0.077 | 0.118 | 0.163 | 0.221 | 0.283 | 0.310 |
| member, 0.5 mm/h | 0.536 | 0.654 | 0.732 | 0.807 | 0.900 | 0.948 |
| member, 1 mm/h | 0.444 | 0.574 | 0.665 | 0.752 | 0.865 | 0.927 |
| member, 2 mm/h | 0.321 | 0.456 | 0.556 | 0.657 | 0.797 | 0.884 |
| member, 4 mm/h | 0.182 | 0.299 | 0.397 | 0.505 | 0.665 | 0.782 |
| member, 8 mm/h | 0.073 | 0.130 | 0.189 | 0.265 | 0.392 | 0.524 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.031 | 1.092 | 1.128 | 1.239 | 1.200 | 1.229 | 1.198 |
| model_mean | 0.780 | 0.270 | 0.208 | 0.215 | 0.193 | 0.210 | 0.196 |
| advection | 0.891 | 0.904 | 0.833 | 0.718 | 0.437 | 0.646 | 0.496 |
| persistence | 0.908 | 0.905 | 0.869 | 0.859 | 0.854 | 0.858 | 0.859 |
| _obs share of variance_ | 89.7% | 6.0% | 2.9% | 1.0% | 0.4% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 22.6 |
| model_mean | 32.6 |
| model_member | 22.1 |
| advection | 20.8 |
| persistence | 22.3 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
