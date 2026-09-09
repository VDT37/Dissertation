# Pooled multi-lead scorecard (4 leads: 15, 30, 45, 60)

_53124 crops pooled from 4 per-lead scorecards, split `val`, 8 members, 25 steps, batch 16, seed 0. Source git `ae67b1d`, codec `39141af7c41d`._

Pooling is exact throughout: pixel errors recombine through `n_pixels`, CSI and its relatives from summed contingency counts, FSS as `1 - sum(num)/sum(den)`, CRPS and spread through their pixel counts, PSD through `n_psd`. No ratio was averaged.

## Pixel error

| metric | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| MAE (mm/h) | 0.2223 | 0.2730 | 0.2656 | 0.3396 |
| RMSE (mm/h) | 0.8069 | 1.0732 | 1.0177 | 1.2120 |
| bias (mm/h) | +0.0016 | +0.0016 | -0.0164 | -0.0010 |

## CSI by threshold

| mm/h | model_mean | model_member | advection | persistence |
|---|---|---|---|---|
| 0.5 | 0.5677 | 0.4998 | 0.5041 | 0.3752 |
| 1 | 0.5026 | 0.4181 | 0.4197 | 0.3002 |
| 2 | 0.3876 | 0.3045 | 0.2978 | 0.2054 |
| 4 | 0.2537 | 0.1910 | 0.1744 | 0.1260 |
| 8 | 0.1402 | 0.1028 | 0.0861 | 0.0708 |

## Probabilistic (pooled)

- Fair CRPS: **0.1389** mm/h over 3,424,690,008.0 pixels. A deterministic forecast's CRPS is its MAE, so compare against advection 0.2656.
- Spread / RMSE: 0.9374 (spread 0.7564, ens-mean RMSE 0.8069).
- Outlier rate: 0.2681 vs ideal 0.2222.
- Rank-histogram flatness (RMSE from flat): 0.04600.

## FSS (pooled as 1 - sum(num)/sum(den))

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| advection, 1 mm/h | 0.593 | 0.727 | 0.802 | 0.861 | 0.926 | 0.959 |
| advection, 8 mm/h | 0.189 | 0.357 | 0.492 | 0.612 | 0.754 | 0.829 |
| model_m0, 1 mm/h | 0.594 | 0.734 | 0.813 | 0.876 | 0.942 | 0.972 |
| model_m0, 8 mm/h | 0.230 | 0.394 | 0.521 | 0.651 | 0.801 | 0.868 |
| model_mean, 1 mm/h | 0.673 | 0.794 | 0.854 | 0.899 | 0.946 | 0.969 |
| model_mean, 8 mm/h | 0.304 | 0.467 | 0.566 | 0.660 | 0.762 | 0.802 |
| persistence, 1 mm/h | 0.471 | 0.585 | 0.667 | 0.753 | 0.869 | 0.929 |
| persistence, 8 mm/h | 0.167 | 0.240 | 0.315 | 0.434 | 0.636 | 0.768 |

## Per-lead inputs

| lead | crops | MAE model_mean | MAE model_member | MAE advection | MAE persistence |
|---|---|---|---|---|---|
| 15 | 13281 | 0.1653 | 0.2105 | 0.1931 | 0.2808 |
| 30 | 13281 | 0.2120 | 0.2632 | 0.2529 | 0.3332 |
| 45 | 13281 | 0.2441 | 0.2973 | 0.2934 | 0.3622 |
| 60 | 13281 | 0.2676 | 0.3211 | 0.3231 | 0.3824 |
