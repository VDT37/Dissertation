# Pooled multi-lead scorecard (4 leads: 15, 30, 45, 60)

_53124 crops pooled from 4 per-lead scorecards, split `val`, 8 members, 25 steps, batch 16, seed 0. Source git `ae67b1d`, codec `39141af7c41d`._

Pooling is exact throughout: pixel errors recombine through `n_pixels`, CSI and its relatives from summed contingency counts, FSS as `1 - sum(num)/sum(den)`, CRPS and spread through their pixel counts, PSD through `n_psd`. No ratio was averaged.

## Pixel error

| metric | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| MAE (mm/h) | 0.2314 | 0.2848 | 0.2656 | 0.3396 |
| RMSE (mm/h) | 0.8191 | 1.0921 | 1.0177 | 1.2120 |
| bias (mm/h) | +0.0056 | +0.0056 | -0.0164 | -0.0010 |

## CSI by threshold

| mm/h | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| 0.5 | 0.5509 | 0.4811 | 0.5041 | 0.3752 |
| 1 | 0.4864 | 0.3992 | 0.4197 | 0.3002 |
| 2 | 0.3719 | 0.2888 | 0.2978 | 0.2054 |
| 4 | 0.2422 | 0.1811 | 0.1744 | 0.1260 |
| 8 | 0.1329 | 0.0979 | 0.0861 | 0.0708 |

## Probabilistic (pooled)

- Fair CRPS: **0.1427** mm/h over 3,424,690,008.0 pixels. A deterministic forecast's CRPS is its MAE, so compare against advection 0.2656.
- Spread / RMSE: 0.9426 (spread 0.7721, ens-mean RMSE 0.8191).
- Outlier rate: 0.2600 vs ideal 0.2222.
- Rank-histogram flatness (RMSE from flat): 0.04634.

## FSS (pooled as 1 - sum(num)/sum(den))

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| advection, 1 mm/h | 0.593 | 0.727 | 0.802 | 0.861 | 0.926 | 0.959 |
| advection, 8 mm/h | 0.189 | 0.357 | 0.492 | 0.612 | 0.754 | 0.829 |
| model_m0, 1 mm/h | 0.574 | 0.711 | 0.789 | 0.854 | 0.927 | 0.962 |
| model_m0, 8 mm/h | 0.224 | 0.381 | 0.502 | 0.628 | 0.780 | 0.846 |
| model_mean, 1 mm/h | 0.657 | 0.778 | 0.838 | 0.886 | 0.937 | 0.961 |
| model_mean, 8 mm/h | 0.293 | 0.453 | 0.554 | 0.648 | 0.748 | 0.784 |
| persistence, 1 mm/h | 0.471 | 0.585 | 0.667 | 0.753 | 0.869 | 0.929 |
| persistence, 8 mm/h | 0.167 | 0.240 | 0.315 | 0.434 | 0.636 | 0.768 |

## Per-lead inputs

| lead | crops | MAE model_mean | MAE model_member | MAE advection | MAE persistence |
|---|---|---|---|---|---|
| 15 | 13281 | 0.1689 | 0.2146 | 0.1931 | 0.2808 |
| 30 | 13281 | 0.2196 | 0.2729 | 0.2529 | 0.3332 |
| 45 | 13281 | 0.2550 | 0.3116 | 0.2934 | 0.3622 |
| 60 | 13281 | 0.2823 | 0.3400 | 0.3231 | 0.3824 |
