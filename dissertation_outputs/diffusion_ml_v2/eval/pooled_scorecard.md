# Pooled multi-lead scorecard (4 leads: 15, 30, 45, 60)

_53124 crops pooled from 4 per-lead scorecards, split `val`, 8 members, 25 steps, batch 16, seed 0. Source git `88f2c9b`, codec `39141af7c41d`._

Pooling is exact throughout: pixel errors recombine through `n_pixels`, CSI and its relatives from summed contingency counts, FSS as `1 - sum(num)/sum(den)`, CRPS and spread through their pixel counts, PSD through `n_psd`. No ratio was averaged.

## Pixel error

| metric | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| MAE (mm/h) | 0.2280 | 0.2796 | 0.2656 | 0.3396 |
| RMSE (mm/h) | 0.8134 | 1.0697 | 1.0177 | 1.2120 |
| bias (mm/h) | +0.0041 | +0.0041 | -0.0164 | -0.0010 |

## CSI by threshold

| mm/h | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| 0.5 | 0.5575 | 0.4882 | 0.5041 | 0.3752 |
| 1 | 0.4920 | 0.4068 | 0.4197 | 0.3002 |
| 2 | 0.3774 | 0.2960 | 0.2978 | 0.2054 |
| 4 | 0.2468 | 0.1869 | 0.1744 | 0.1260 |
| 8 | 0.1368 | 0.1019 | 0.0861 | 0.0708 |

## Probabilistic (pooled)

- Fair CRPS: **0.1418** mm/h over 3,424,690,008.0 pixels. A deterministic forecast's CRPS is its MAE, so compare against advection 0.2656.
- Spread / RMSE: 0.9132 (spread 0.7428, ens-mean RMSE 0.8134).
- Outlier rate: 0.2658 vs ideal 0.2222.
- Rank-histogram flatness (RMSE from flat): 0.04573.

## FSS (pooled as 1 - sum(num)/sum(den))

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| advection, 1 mm/h | 0.593 | 0.727 | 0.802 | 0.861 | 0.926 | 0.959 |
| advection, 8 mm/h | 0.189 | 0.357 | 0.492 | 0.612 | 0.754 | 0.829 |
| model_m0, 1 mm/h | 0.583 | 0.720 | 0.797 | 0.861 | 0.932 | 0.965 |
| model_m0, 8 mm/h | 0.235 | 0.397 | 0.521 | 0.648 | 0.792 | 0.850 |
| model_mean, 1 mm/h | 0.663 | 0.783 | 0.843 | 0.890 | 0.940 | 0.964 |
| model_mean, 8 mm/h | 0.304 | 0.467 | 0.568 | 0.664 | 0.764 | 0.798 |
| persistence, 1 mm/h | 0.471 | 0.585 | 0.667 | 0.753 | 0.869 | 0.929 |
| persistence, 8 mm/h | 0.167 | 0.240 | 0.315 | 0.434 | 0.636 | 0.768 |

## Per-lead inputs

| lead | crops | MAE model_mean | MAE model_member | MAE advection | MAE persistence |
|---|---|---|---|---|---|
| 15 | 13281 | 0.1673 | 0.2115 | 0.1931 | 0.2808 |
| 30 | 13281 | 0.2170 | 0.2684 | 0.2529 | 0.3332 |
| 45 | 13281 | 0.2509 | 0.3055 | 0.2934 | 0.3622 |
| 60 | 13281 | 0.2768 | 0.3329 | 0.3231 | 0.3824 |
