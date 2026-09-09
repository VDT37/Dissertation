# Pooled multi-lead scorecard (4 leads: 15, 30, 45, 60)

_53124 crops pooled from 4 per-lead scorecards, split `val`, 8 members, 25 steps, batch 16, seed 0. Source git `ae67b1d`, codec `39141af7c41d`._

Pooling is exact throughout: pixel errors recombine through `n_pixels`, CSI and its relatives from summed contingency counts, FSS as `1 - sum(num)/sum(den)`, CRPS and spread through their pixel counts, PSD through `n_psd`. No ratio was averaged.

## Pixel error

| metric | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| MAE (mm/h) | 0.2241 | 0.2757 | 0.2656 | 0.3396 |
| RMSE (mm/h) | 0.8067 | 1.0766 | 1.0177 | 1.2120 |
| bias (mm/h) | +0.0064 | +0.0064 | -0.0164 | -0.0010 |

## CSI by threshold

| mm/h | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| 0.5 | 0.5664 | 0.4984 | 0.5041 | 0.3752 |
| 1 | 0.5028 | 0.4175 | 0.4197 | 0.3002 |
| 2 | 0.3894 | 0.3050 | 0.2978 | 0.2054 |
| 4 | 0.2565 | 0.1921 | 0.1744 | 0.1260 |
| 8 | 0.1439 | 0.1043 | 0.0861 | 0.0708 |

## Probabilistic (pooled)

- Fair CRPS: **0.1386** mm/h over 3,424,690,008.0 pixels. A deterministic forecast's CRPS is its MAE, so compare against advection 0.2656.
- Spread / RMSE: 0.9449 (spread 0.7622, ens-mean RMSE 0.8067).
- Outlier rate: 0.2630 vs ideal 0.2222.
- Rank-histogram flatness (RMSE from flat): 0.04440.

## FSS (pooled as 1 - sum(num)/sum(den))

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| advection, 1 mm/h | 0.593 | 0.727 | 0.802 | 0.861 | 0.926 | 0.959 |
| advection, 8 mm/h | 0.189 | 0.357 | 0.492 | 0.612 | 0.754 | 0.829 |
| model_m0, 1 mm/h | 0.594 | 0.733 | 0.810 | 0.873 | 0.940 | 0.972 |
| model_m0, 8 mm/h | 0.233 | 0.395 | 0.519 | 0.646 | 0.794 | 0.860 |
| model_mean, 1 mm/h | 0.673 | 0.793 | 0.853 | 0.898 | 0.945 | 0.968 |
| model_mean, 8 mm/h | 0.311 | 0.477 | 0.578 | 0.673 | 0.777 | 0.815 |
| persistence, 1 mm/h | 0.471 | 0.585 | 0.667 | 0.753 | 0.869 | 0.929 |
| persistence, 8 mm/h | 0.167 | 0.240 | 0.315 | 0.434 | 0.636 | 0.768 |

## Per-lead inputs

| lead | crops | MAE model_mean | MAE model_member | MAE advection | MAE persistence |
|---|---|---|---|---|---|
| 15 | 13281 | 0.1655 | 0.2104 | 0.1931 | 0.2808 |
| 30 | 13281 | 0.2136 | 0.2654 | 0.2529 | 0.3332 |
| 45 | 13281 | 0.2466 | 0.3009 | 0.2934 | 0.3622 |
| 60 | 13281 | 0.2709 | 0.3261 | 0.3231 | 0.3824 |
