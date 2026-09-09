# Deterministic scorecard: `regression` (`val` split, lead 45)

_13281 of 13281 crops (full), anchor `zA`, target `delta`. Regression epoch 2 (val MSE 0.302064760786772). FSS from 403 crops, PSD from 200. git `88f2c9b`._

`codec_advection` is the codec FLOOR (the advection field pushed through the same encode-decode round trip the learned mean pays) and `codec_oracle` is the codec CEILING (decode of the encoded truth). A latent method has to be judged between them before it is judged against raw advection.

## GATE-D

- Verdict: **PASS** (MAE_mmh of regression_mean vs codec_advection).
- Margin against the codec floor: +0.0827 mm/h (positive = the learned mean beats the round-tripped advection field, i.e. mu_r learned something that survives to pixels).
- Margin against RAW advection: +0.0809 mm/h. This is the pixel-space headline, and it is a different question from the gate.
- Codec round-trip penalty on advection alone: +0.0018 mm/h.
- Fraction of the achievable codec span (floor to ceiling) recovered: 0.328.

## Pixel error (lower is better)

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.2124 | 0.2952 | 0.0428 | 0.2934 | 0.3622 |
| RMSE (mm/h) | 0.8540 | 1.0820 | 0.1941 | 1.0807 | 1.2511 |
| bias (mm/h) | -0.0954 | -0.0111 | +0.0071 | -0.0162 | -0.0012 |

## CSI by threshold (higher is better)

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.5168 | 0.4599 | 0.9171 | 0.4589 | 0.3407 |
| 1 | 0.4464 | 0.3752 | 0.8872 | 0.3737 | 0.2669 |
| 2 | 0.3334 | 0.2550 | 0.8378 | 0.2530 | 0.1755 |
| 4 | 0.2081 | 0.1388 | 0.7769 | 0.1371 | 0.1039 |
| 8 | 0.1036 | 0.0576 | 0.7378 | 0.0566 | 0.0576 |

## Detection at 1 mm/h

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| POD | 0.5327 | 0.5414 | 0.9509 | 0.5360 | 0.4204 |
| FAR | 0.2661 | 0.4500 | 0.0702 | 0.4476 | 0.5777 |
| freq_bias | 0.7258 | 0.9844 | 1.0228 | 0.9702 | 0.9953 |

## FSS (neighbourhood scales, km)

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| regression_mean, 1 mm/h | 0.625 | 0.728 | 0.792 | 0.846 | 0.908 | 0.938 |
| regression_mean, 8 mm/h | 0.234 | 0.346 | 0.424 | 0.522 | 0.667 | 0.753 |
| codec_advection, 1 mm/h | 0.549 | 0.679 | 0.762 | 0.831 | 0.910 | 0.952 |
| codec_advection, 8 mm/h | 0.132 | 0.259 | 0.384 | 0.518 | 0.690 | 0.783 |
| codec_oracle, 1 mm/h | 0.941 | 0.997 | 0.999 | 1.000 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.854 | 0.985 | 0.994 | 0.996 | 0.997 | 0.997 |
| advection, 1 mm/h | 0.548 | 0.679 | 0.762 | 0.831 | 0.910 | 0.951 |
| advection, 8 mm/h | 0.130 | 0.256 | 0.381 | 0.516 | 0.689 | 0.785 |
| persistence, 1 mm/h | 0.434 | 0.540 | 0.617 | 0.703 | 0.836 | 0.912 |
| persistence, 8 mm/h | 0.142 | 0.196 | 0.249 | 0.346 | 0.543 | 0.707 |

## Power spectrum by band (200 clean crops)

Forecast band power divided by observed band power, 1.0 = matched. Bands partition the resolved spectrum. Both 2-8 km estimators are given because they disagree materially; the band power ratio is the headline (`docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| regression_mean | 0.848 | 0.262 | 0.147 | 0.091 | 0.085 | 0.089 | 0.087 |
| codec_advection | 1.007 | 1.148 | 1.076 | 0.850 | 0.434 | 0.734 | 0.519 |
| codec_oracle | 1.061 | 1.058 | 1.046 | 0.998 | 0.893 | 0.969 | 0.908 |
| advection | 0.975 | 1.123 | 1.062 | 0.855 | 0.465 | 0.746 | 0.547 |
| persistence | 0.907 | 0.962 | 1.010 | 0.994 | 0.928 | 0.975 | 0.943 |
| _obs share of variance_ | 89.1% | 6.0% | 3.0% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| regression_mean | 18.5 |
| codec_advection | 21.9 |
| codec_oracle | 23.0 |
| advection | 21.9 |
| persistence | 22.9 |
