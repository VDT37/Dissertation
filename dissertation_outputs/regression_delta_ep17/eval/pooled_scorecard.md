# Pooled multi-lead scorecard (4 leads: 15, 30, 45, 60)

_53124 crops pooled from 4 per-lead scorecards, split `val`, None members, None steps, batch 32, seed 0. Source git `aeda1f4`, codec `39141af7c41d`._

Pooling is exact throughout: pixel errors recombine through `n_pixels`, CSI and its relatives from summed contingency counts, FSS as `1 - sum(num)/sum(den)`, CRPS and spread through their pixel counts, PSD through `n_psd`. No ratio was averaged.

## Pixel error

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.1955 | 0.2672 | 0.0428 | 0.2656 | 0.3396 |
| RMSE (mm/h) | 0.8099 | 1.0184 | 0.1940 | 1.0177 | 1.2120 |
| bias (mm/h) | -0.0796 | -0.0113 | +0.0071 | -0.0164 | -0.0010 |

## CSI by threshold

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.5643 | 0.5052 | 0.9172 | 0.5041 | 0.3752 |
| 1 | 0.4956 | 0.4212 | 0.8872 | 0.4197 | 0.3002 |
| 2 | 0.3844 | 0.2998 | 0.8379 | 0.2978 | 0.2054 |
| 4 | 0.2568 | 0.1763 | 0.7769 | 0.1744 | 0.1260 |
| 8 | 0.1434 | 0.0874 | 0.7378 | 0.0861 | 0.0708 |

## FSS (pooled as 1 - sum(num)/sum(den))

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| advection, 1 mm/h | 0.593 | 0.727 | 0.802 | 0.861 | 0.926 | 0.959 |
| advection, 8 mm/h | 0.189 | 0.357 | 0.492 | 0.612 | 0.754 | 0.829 |
| codec_advection, 1 mm/h | 0.595 | 0.727 | 0.802 | 0.862 | 0.927 | 0.960 |
| codec_advection, 8 mm/h | 0.191 | 0.359 | 0.494 | 0.615 | 0.755 | 0.829 |
| codec_oracle, 1 mm/h | 0.941 | 0.997 | 0.999 | 1.000 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.855 | 0.986 | 0.994 | 0.996 | 0.997 | 0.997 |
| persistence, 1 mm/h | 0.471 | 0.585 | 0.667 | 0.753 | 0.869 | 0.929 |
| persistence, 8 mm/h | 0.167 | 0.240 | 0.315 | 0.434 | 0.636 | 0.768 |
| regression_mean, 1 mm/h | 0.667 | 0.773 | 0.830 | 0.876 | 0.926 | 0.950 |
| regression_mean, 8 mm/h | 0.301 | 0.449 | 0.534 | 0.620 | 0.733 | 0.796 |

## Per-lead inputs

| lead | crops | MAE regression_mean | MAE codec_advection | MAE codec_oracle | MAE advection | MAE persistence |
|---|---|---|---|---|---|---|
| 15 | 13281 | 0.1516 | 0.1940 | 0.0428 | 0.1931 | 0.2808 |
| 30 | 13281 | 0.1886 | 0.2542 | 0.0428 | 0.2529 | 0.3332 |
| 45 | 13281 | 0.2124 | 0.2952 | 0.0428 | 0.2934 | 0.3622 |
| 60 | 13281 | 0.2294 | 0.3252 | 0.0428 | 0.3231 | 0.3824 |
