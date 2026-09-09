# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.3324181713280408). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.362 | 0.293 | **0.255** | 0.312 |
| RMSE (mm/h) | 1.251 | 1.081 | **0.862** | 1.150 |
| bias (mm/h) | -0.001 | -0.016 | +0.005 | +0.005 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.341 | 0.459 | 0.512 | 0.438 |
| 1 | 0.267 | 0.374 | 0.444 | 0.355 |
| 2 | 0.175 | 0.253 | 0.324 | 0.248 |
| 4 | 0.104 | 0.137 | 0.193 | 0.148 |
| 8 | 0.058 | 0.057 | 0.091 | 0.074 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.420 | 0.536 | 0.636 | 0.528 |
| FAR | 0.578 | 0.448 | 0.404 | 0.479 |
| freq_bias | 0.995 | 0.970 | 1.067 | 1.012 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1562 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.293 and persistence 0.362.
- **Spread / RMSE**: 0.944 (spread 0.814, ens-mean RMSE 0.862). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.268 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0533, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.681 | 0.783 | 0.839 | 0.884 | 0.933 | 0.957 |
| mean, 1 mm/h | 0.621 | 0.741 | 0.808 | 0.863 | 0.925 | 0.955 |
| mean, 2 mm/h | 0.510 | 0.654 | 0.737 | 0.809 | 0.892 | 0.933 |
| mean, 4 mm/h | 0.372 | 0.529 | 0.623 | 0.710 | 0.811 | 0.859 |
| mean, 8 mm/h | 0.234 | 0.358 | 0.448 | 0.551 | 0.676 | 0.720 |
| member, 0.5 mm/h | 0.614 | 0.729 | 0.800 | 0.861 | 0.931 | 0.966 |
| member, 1 mm/h | 0.531 | 0.663 | 0.747 | 0.823 | 0.912 | 0.956 |
| member, 2 mm/h | 0.413 | 0.560 | 0.658 | 0.750 | 0.866 | 0.930 |
| member, 4 mm/h | 0.291 | 0.444 | 0.554 | 0.664 | 0.809 | 0.890 |
| member, 8 mm/h | 0.178 | 0.299 | 0.408 | 0.542 | 0.713 | 0.793 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.045 | 1.174 | 1.209 | 1.156 | 0.984 | 1.108 | 1.010 |
| model_mean | 0.834 | 0.415 | 0.312 | 0.256 | 0.206 | 0.242 | 0.215 |
| advection | 0.975 | 1.123 | 1.062 | 0.855 | 0.465 | 0.746 | 0.547 |
| persistence | 0.907 | 0.962 | 1.010 | 0.994 | 0.928 | 0.975 | 0.943 |
| _obs share of variance_ | 89.1% | 6.0% | 3.0% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 32.8 |
| model_member | 22.8 |
| advection | 21.9 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
