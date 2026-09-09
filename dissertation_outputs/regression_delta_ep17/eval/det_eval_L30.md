# Deterministic scorecard: `regression` (`val` split, lead 30)

_13281 of 13281 crops (full), anchor `zA`, target `delta`. Regression epoch 2 (val MSE 0.302064760786772). FSS from 403 crops, PSD from 200. git `88f2c9b`._

`codec_advection` is the codec FLOOR (the advection field pushed through the same encode-decode round trip the learned mean pays) and `codec_oracle` is the codec CEILING (decode of the encoded truth). A latent method has to be judged between them before it is judged against raw advection.

## GATE-D

- Verdict: **PASS** (MAE_mmh of regression_mean vs codec_advection).
- Margin against the codec floor: +0.0656 mm/h (positive = the learned mean beats the round-tripped advection field, i.e. mu_r learned something that survives to pixels).
- Margin against RAW advection: +0.0642 mm/h. This is the pixel-space headline, and it is a different question from the gate.
- Codec round-trip penalty on advection alone: +0.0014 mm/h.
- Fraction of the achievable codec span (floor to ceiling) recovered: 0.310.

## Pixel error (lower is better)

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.1886 | 0.2542 | 0.0428 | 0.2529 | 0.3332 |
| RMSE (mm/h) | 0.7892 | 0.9919 | 0.1940 | 0.9918 | 1.2027 |
| bias (mm/h) | -0.0686 | -0.0102 | +0.0071 | -0.0153 | -0.0011 |

## CSI by threshold (higher is better)

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.5927 | 0.5331 | 0.9172 | 0.5319 | 0.3881 |
| 1 | 0.5226 | 0.4478 | 0.8872 | 0.4461 | 0.3111 |
| 2 | 0.4084 | 0.3221 | 0.8378 | 0.3199 | 0.2127 |
| 4 | 0.2704 | 0.1885 | 0.7769 | 0.1864 | 0.1291 |
| 8 | 0.1441 | 0.0895 | 0.7378 | 0.0881 | 0.0719 |

## Detection at 1 mm/h

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| POD | 0.6255 | 0.6146 | 0.9509 | 0.6087 | 0.4736 |
| FAR | 0.2396 | 0.3774 | 0.0703 | 0.3745 | 0.5245 |
| freq_bias | 0.8226 | 0.9872 | 1.0228 | 0.9730 | 0.9962 |

## FSS (neighbourhood scales, km)

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| regression_mean, 1 mm/h | 0.690 | 0.800 | 0.860 | 0.905 | 0.949 | 0.968 |
| regression_mean, 8 mm/h | 0.300 | 0.451 | 0.546 | 0.643 | 0.757 | 0.816 |
| codec_advection, 1 mm/h | 0.620 | 0.759 | 0.835 | 0.891 | 0.948 | 0.974 |
| codec_advection, 8 mm/h | 0.189 | 0.372 | 0.532 | 0.667 | 0.814 | 0.880 |
| codec_oracle, 1 mm/h | 0.941 | 0.997 | 0.999 | 0.999 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.850 | 0.984 | 0.993 | 0.996 | 0.997 | 0.997 |
| advection, 1 mm/h | 0.618 | 0.758 | 0.834 | 0.891 | 0.948 | 0.974 |
| advection, 8 mm/h | 0.186 | 0.370 | 0.530 | 0.666 | 0.815 | 0.882 |
| persistence, 1 mm/h | 0.481 | 0.598 | 0.682 | 0.774 | 0.898 | 0.951 |
| persistence, 8 mm/h | 0.164 | 0.233 | 0.302 | 0.430 | 0.682 | 0.820 |

## Power spectrum by band (200 clean crops)

Forecast band power divided by observed band power, 1.0 = matched. Bands partition the resolved spectrum. Both 2-8 km estimators are given because they disagree materially; the band power ratio is the headline (`docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| regression_mean | 0.943 | 0.410 | 0.205 | 0.107 | 0.101 | 0.105 | 0.102 |
| codec_advection | 0.992 | 1.060 | 0.966 | 0.766 | 0.407 | 0.668 | 0.479 |
| codec_oracle | 1.063 | 1.059 | 1.043 | 1.003 | 0.877 | 0.968 | 0.895 |
| advection | 0.960 | 1.036 | 0.954 | 0.775 | 0.444 | 0.684 | 0.511 |
| persistence | 0.952 | 1.002 | 0.991 | 0.969 | 0.934 | 0.959 | 0.938 |
| _obs share of variance_ | 88.8% | 6.0% | 3.2% | 1.4% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.0 |
| regression_mean | 19.9 |
| codec_advection | 22.1 |
| codec_oracle | 23.0 |
| advection | 22.1 |
| persistence | 22.9 |
