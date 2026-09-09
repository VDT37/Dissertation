# Diffusion nowcast scorecard (`val` split)

_13281 crops, 8-member ensembles, 25 Heun steps, guidance 1.0. Checkpoint epoch 25 (val loss 0.3324181713280408). FSS from 403 crops, PSD from 200._

`model_mean` is the ensemble mean; `model_member` is the average skill of a single member. Averaging damps peaks, so the mean scores better on MAE/RMSE and worse at high thresholds. Both are reported, see `docs/Diffusion_Run1_Results.md`.

## Pixel error (lower is better)

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| MAE (mm/h) | 0.382 | 0.323 | **0.282** | 0.340 |
| RMSE (mm/h) | 1.283 | 1.140 | **0.905** | 1.202 |
| bias (mm/h) | -0.001 | -0.019 | +0.004 | +0.004 |

## CSI by threshold (higher is better)

| mm/h | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| 0.5 | 0.307 | 0.404 | 0.459 | 0.387 |
| 1 | 0.237 | 0.321 | 0.391 | 0.308 |
| 2 | 0.153 | 0.207 | 0.272 | 0.208 |
| 4 | 0.089 | 0.105 | 0.153 | 0.120 |
| 8 | 0.048 | 0.040 | 0.069 | 0.058 |

## Detection at 1 mm/h

| metric | persistence | advection | model (mean) | model (member) |
|---|---|---|---|---|
| POD | 0.383 | 0.477 | 0.577 | 0.472 |
| FAR | 0.616 | 0.504 | 0.452 | 0.531 |
| freq_bias | 0.996 | 0.961 | 1.052 | 1.005 |

## Probabilistic (the ensemble's reason to exist)

- **CRPS (fair)**: 0.1718 mm/h. A deterministic forecast's CRPS equals its MAE, so compare against advection 0.323 and persistence 0.382.
- **Spread / RMSE**: 0.935 (spread 0.846, ens-mean RMSE 0.905). Near 1 is well dispersed, below 1 is over-confident.
- **Outlier rate**: 0.284 vs ideal 0.222.
- **Rank-histogram flatness** (RMSE from flat): 0.0627, 0 is perfectly flat.

## FSS (model mean vs a single member)

| threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| mean, 0.5 mm/h | 0.635 | 0.736 | 0.794 | 0.844 | 0.904 | 0.936 |
| mean, 1 mm/h | 0.570 | 0.687 | 0.755 | 0.816 | 0.891 | 0.932 |
| mean, 2 mm/h | 0.450 | 0.585 | 0.668 | 0.745 | 0.843 | 0.896 |
| mean, 4 mm/h | 0.315 | 0.451 | 0.537 | 0.624 | 0.738 | 0.799 |
| mean, 8 mm/h | 0.196 | 0.288 | 0.358 | 0.446 | 0.548 | 0.578 |
| member, 0.5 mm/h | 0.566 | 0.673 | 0.744 | 0.811 | 0.896 | 0.945 |
| member, 1 mm/h | 0.480 | 0.601 | 0.684 | 0.764 | 0.868 | 0.928 |
| member, 2 mm/h | 0.361 | 0.492 | 0.585 | 0.679 | 0.811 | 0.893 |
| member, 4 mm/h | 0.247 | 0.379 | 0.479 | 0.587 | 0.745 | 0.846 |
| member, 8 mm/h | 0.152 | 0.249 | 0.346 | 0.480 | 0.676 | 0.769 |

## Power spectrum by band (200 clean crops)

Ratio of forecast band power to observed band power, 1.0 = matched. Bands partition the resolved spectrum, so `obs share` sums to 1. The 2-8 km headline is the union of the last two columns; both estimators are given because they disagree materially (see `docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| model_member | 1.077 | 1.222 | 1.214 | 1.178 | 0.981 | 1.124 | 1.017 |
| model_mean | 0.791 | 0.347 | 0.272 | 0.240 | 0.193 | 0.227 | 0.202 |
| advection | 1.014 | 1.160 | 1.046 | 0.851 | 0.480 | 0.749 | 0.559 |
| persistence | 0.926 | 0.980 | 0.983 | 0.994 | 0.943 | 0.980 | 0.953 |
| _obs share of variance_ | 89.0% | 6.0% | 3.2% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| model_mean | 35.0 |
| model_member | 22.7 |
| advection | 21.6 |
| persistence | 22.9 |

See `diffusion_eval.png` for the histogram, PSD, CSI, reliability, rank histogram and spread panels.
