# Deterministic scorecard: `advection` (`val` split, lead 60)

_512 of 13281 crops (stride), anchor `zA`, target `None`. Regression epoch None (val MSE None). FSS from 512 crops, PSD from 200. git `88f2c9b`._

`codec_advection` is the codec FLOOR (the advection field pushed through the same encode-decode round trip the learned mean pays) and `codec_oracle` is the codec CEILING (decode of the encoded truth). A latent method has to be judged between them before it is judged against raw advection.

## GATE-D

- Verdict: **PASS** (MAE_mmh of regression_mean vs codec_advection).
- Margin against the codec floor: +0.0022 mm/h (positive = the learned mean beats the round-tripped advection field, i.e. mu_r learned something that survives to pixels).
- Margin against RAW advection: +0.0000 mm/h. This is the pixel-space headline, and it is a different question from the gate.
- Codec round-trip penalty on advection alone: +0.0022 mm/h.
- Fraction of the achievable codec span (floor to ceiling) recovered: 0.008.

## Pixel error (lower is better)

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.3350 | 0.3372 | 0.0448 | 0.3350 | 0.3909 |
| RMSE (mm/h) | 1.1385 | 1.1415 | 0.1953 | 1.1385 | 1.2749 |
| bias (mm/h) | -0.0235 | -0.0181 | +0.0077 | -0.0235 | -0.0072 |

## CSI by threshold (higher is better)

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.4186 | 0.4196 | 0.9196 | 0.4186 | 0.3258 |
| 1 | 0.3325 | 0.3340 | 0.8904 | 0.3325 | 0.2539 |
| 2 | 0.2078 | 0.2096 | 0.8380 | 0.2078 | 0.1623 |
| 4 | 0.1063 | 0.1077 | 0.7762 | 0.1063 | 0.0965 |
| 8 | 0.0427 | 0.0437 | 0.7409 | 0.0427 | 0.0598 |

## Detection at 1 mm/h

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| POD | 0.4863 | 0.4915 | 0.9526 | 0.4863 | 0.3990 |
| FAR | 0.4876 | 0.4896 | 0.0683 | 0.4876 | 0.5889 |
| freq_bias | 0.9489 | 0.9629 | 1.0224 | 0.9489 | 0.9704 |

## FSS (neighbourhood scales, km)

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| regression_mean, 1 mm/h | 0.498 | 0.619 | 0.701 | 0.777 | 0.870 | 0.924 |
| regression_mean, 8 mm/h | 0.082 | 0.177 | 0.276 | 0.389 | 0.569 | 0.701 |
| codec_advection, 1 mm/h | 0.500 | 0.620 | 0.702 | 0.777 | 0.871 | 0.925 |
| codec_advection, 8 mm/h | 0.084 | 0.179 | 0.278 | 0.391 | 0.568 | 0.696 |
| codec_oracle, 1 mm/h | 0.942 | 0.997 | 0.999 | 1.000 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.851 | 0.984 | 0.993 | 0.995 | 0.996 | 0.997 |
| advection, 1 mm/h | 0.498 | 0.619 | 0.701 | 0.777 | 0.870 | 0.924 |
| advection, 8 mm/h | 0.082 | 0.177 | 0.276 | 0.389 | 0.569 | 0.701 |
| persistence, 1 mm/h | 0.405 | 0.501 | 0.570 | 0.645 | 0.771 | 0.862 |
| persistence, 8 mm/h | 0.113 | 0.171 | 0.230 | 0.315 | 0.475 | 0.626 |

## Power spectrum by band (200 clean crops)

Forecast band power divided by observed band power, 1.0 = matched. Bands partition the resolved spectrum. Both 2-8 km estimators are given because they disagree materially; the band power ratio is the headline (`docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| regression_mean | 1.026 | 0.884 | 0.787 | 0.664 | 0.426 | 0.603 | 0.470 |
| codec_advection | 1.060 | 0.908 | 0.803 | 0.664 | 0.397 | 0.595 | 0.447 |
| codec_oracle | 1.061 | 1.060 | 1.046 | 1.009 | 0.896 | 0.980 | 0.910 |
| advection | 1.026 | 0.884 | 0.787 | 0.664 | 0.426 | 0.603 | 0.470 |
| persistence | 1.063 | 0.961 | 0.948 | 0.933 | 0.973 | 0.944 | 0.960 |
| _obs share of variance_ | 88.7% | 6.1% | 3.3% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 24.0 |
| regression_mean | 22.3 |
| codec_advection | 22.3 |
| codec_oracle | 23.9 |
| advection | 22.3 |
| persistence | 23.3 |
