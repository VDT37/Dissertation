# Deterministic scorecard: `regression` (`val` split, lead 15)

_13281 of 13281 crops (full), anchor `none`, target `z_y`. Regression epoch 2 (val MSE 0.3168317846307041). FSS from 403 crops, PSD from 200. git `88f2c9b`._

`codec_advection` is the codec FLOOR (the advection field pushed through the same encode-decode round trip the learned mean pays) and `codec_oracle` is the codec CEILING (decode of the encoded truth). A latent method has to be judged between them before it is judged against raw advection.

## GATE-D

- Verdict: **PASS** (MAE_mmh of regression_mean vs codec_advection).
- Margin against the codec floor: +0.0396 mm/h (positive = the learned mean beats the round-tripped advection field, i.e. mu_r learned something that survives to pixels).
- Margin against RAW advection: +0.0387 mm/h. This is the pixel-space headline, and it is a different question from the gate.
- Codec round-trip penalty on advection alone: +0.0009 mm/h.
- Fraction of the achievable codec span (floor to ceiling) recovered: 0.262.

## Pixel error (lower is better)

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.1544 | 0.1940 | 0.0428 | 0.1931 | 0.2808 |
| RMSE (mm/h) | 0.6916 | 0.8299 | 0.1940 | 0.8312 | 1.1030 |
| bias (mm/h) | -0.0405 | -0.0099 | +0.0071 | -0.0150 | -0.0006 |

## CSI by threshold (higher is better)

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.6840 | 0.6424 | 0.9173 | 0.6411 | 0.4759 |
| 1 | 0.6176 | 0.5607 | 0.8872 | 0.5590 | 0.3965 |
| 2 | 0.5074 | 0.4348 | 0.8379 | 0.4326 | 0.2896 |
| 4 | 0.3677 | 0.2867 | 0.7770 | 0.2840 | 0.1874 |
| 8 | 0.2307 | 0.1702 | 0.7378 | 0.1681 | 0.1069 |

## Detection at 1 mm/h

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| POD | 0.7302 | 0.7143 | 0.9509 | 0.7078 | 0.5672 |
| FAR | 0.1999 | 0.2772 | 0.0703 | 0.2733 | 0.4316 |
| freq_bias | 0.9127 | 0.9882 | 1.0228 | 0.9740 | 0.9979 |

## FSS (neighbourhood scales, km)

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| regression_mean, 1 mm/h | 0.762 | 0.877 | 0.925 | 0.955 | 0.979 | 0.987 |
| regression_mean, 8 mm/h | 0.430 | 0.642 | 0.751 | 0.830 | 0.905 | 0.936 |
| codec_advection, 1 mm/h | 0.718 | 0.859 | 0.917 | 0.953 | 0.981 | 0.991 |
| codec_advection, 8 mm/h | 0.339 | 0.604 | 0.758 | 0.850 | 0.925 | 0.953 |
| codec_oracle, 1 mm/h | 0.940 | 0.997 | 0.999 | 1.000 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.858 | 0.986 | 0.994 | 0.997 | 0.998 | 0.998 |
| advection, 1 mm/h | 0.717 | 0.859 | 0.917 | 0.953 | 0.981 | 0.991 |
| advection, 8 mm/h | 0.337 | 0.603 | 0.756 | 0.848 | 0.923 | 0.952 |
| persistence, 1 mm/h | 0.570 | 0.707 | 0.802 | 0.888 | 0.962 | 0.984 |
| persistence, 8 mm/h | 0.234 | 0.360 | 0.496 | 0.674 | 0.873 | 0.933 |

## Power spectrum by band (200 clean crops)

Forecast band power divided by observed band power, 1.0 = matched. Bands partition the resolved spectrum. Both 2-8 km estimators are given because they disagree materially; the band power ratio is the headline (`docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| regression_mean | 0.990 | 0.584 | 0.321 | 0.139 | 0.135 | 0.138 | 0.136 |
| codec_advection | 0.986 | 0.946 | 0.889 | 0.722 | 0.393 | 0.633 | 0.459 |
| codec_oracle | 1.063 | 1.058 | 1.042 | 1.002 | 0.888 | 0.971 | 0.904 |
| advection | 0.955 | 0.923 | 0.876 | 0.729 | 0.425 | 0.647 | 0.487 |
| persistence | 0.986 | 0.977 | 0.991 | 0.985 | 0.959 | 0.978 | 0.962 |
| _obs share of variance_ | 88.3% | 6.4% | 3.3% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| regression_mean | 21.3 |
| codec_advection | 22.2 |
| codec_oracle | 22.9 |
| advection | 22.3 |
| persistence | 22.9 |
