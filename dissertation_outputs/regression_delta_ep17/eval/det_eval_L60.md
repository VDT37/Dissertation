# Deterministic scorecard: `regression` (`val` split, lead 60)

_13281 of 13281 crops (full), anchor `zA`, target `delta`. Regression epoch 2 (val MSE 0.302064760786772). FSS from 403 crops, PSD from 200. git `88f2c9b`._

`codec_advection` is the codec FLOOR (the advection field pushed through the same encode-decode round trip the learned mean pays) and `codec_oracle` is the codec CEILING (decode of the encoded truth). A latent method has to be judged between them before it is judged against raw advection.

## GATE-D

- Verdict: **PASS** (MAE_mmh of regression_mean vs codec_advection).
- Margin against the codec floor: +0.0959 mm/h (positive = the learned mean beats the round-tripped advection field, i.e. mu_r learned something that survives to pixels).
- Margin against RAW advection: +0.0938 mm/h. This is the pixel-space headline, and it is a different question from the gate.
- Codec round-trip penalty on advection alone: +0.0021 mm/h.
- Fraction of the achievable codec span (floor to ceiling) recovered: 0.339.

## Pixel error (lower is better)

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| MAE (mm/h) | 0.2294 | 0.3252 | 0.0428 | 0.3231 | 0.3824 |
| RMSE (mm/h) | 0.8993 | 1.1425 | 0.1939 | 1.1404 | 1.2835 |
| bias (mm/h) | -0.1172 | -0.0139 | +0.0071 | -0.0191 | -0.0010 |

## CSI by threshold (higher is better)

| mm/h | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| 0.5 | 0.4567 | 0.4049 | 0.9171 | 0.4040 | 0.3074 |
| 1 | 0.3873 | 0.3226 | 0.8872 | 0.3212 | 0.2373 |
| 2 | 0.2779 | 0.2089 | 0.8379 | 0.2071 | 0.1525 |
| 4 | 0.1670 | 0.1069 | 0.7769 | 0.1054 | 0.0887 |
| 8 | 0.0803 | 0.0406 | 0.7377 | 0.0398 | 0.0485 |

## Detection at 1 mm/h

| metric | regression_mean | codec_advection | codec_oracle | advection | persistence |
|---|---|---|---|---|---|
| POD | 0.4586 | 0.4818 | 0.9510 | 0.4768 | 0.3827 |
| FAR | 0.2865 | 0.5060 | 0.0702 | 0.5039 | 0.6156 |
| freq_bias | 0.6427 | 0.9753 | 1.0228 | 0.9611 | 0.9957 |

## FSS (neighbourhood scales, km)

| field, threshold | 1 km | 5 km | 11 km | 21 km | 51 km | 101 km |
|---|---|---|---|---|---|---|
| regression_mean, 1 mm/h | 0.570 | 0.667 | 0.730 | 0.790 | 0.864 | 0.904 |
| regression_mean, 8 mm/h | 0.193 | 0.276 | 0.329 | 0.412 | 0.552 | 0.631 |
| codec_advection, 1 mm/h | 0.493 | 0.613 | 0.696 | 0.772 | 0.868 | 0.923 |
| codec_advection, 8 mm/h | 0.095 | 0.184 | 0.280 | 0.399 | 0.576 | 0.684 |
| codec_oracle, 1 mm/h | 0.941 | 0.997 | 0.999 | 1.000 | 1.000 | 1.000 |
| codec_oracle, 8 mm/h | 0.859 | 0.986 | 0.994 | 0.996 | 0.997 | 0.997 |
| advection, 1 mm/h | 0.491 | 0.612 | 0.696 | 0.772 | 0.867 | 0.923 |
| advection, 8 mm/h | 0.093 | 0.181 | 0.276 | 0.395 | 0.571 | 0.682 |
| persistence, 1 mm/h | 0.401 | 0.499 | 0.571 | 0.651 | 0.781 | 0.870 |
| persistence, 8 mm/h | 0.125 | 0.166 | 0.203 | 0.275 | 0.434 | 0.599 |

## Power spectrum by band (200 clean crops)

Forecast band power divided by observed band power, 1.0 = matched. Bands partition the resolved spectrum. Both 2-8 km estimators are given because they disagree materially; the band power ratio is the headline (`docs/designs/Metrics_Catalogue.md`).

| field | gt_32km | 16_32km | 8_16km | 4_8km | 2_4km | 2-8 km band power | 2-8 km mean-of-ratios |
|---|---|---|---|---|---|---|---|
| regression_mean | 0.796 | 0.182 | 0.115 | 0.077 | 0.072 | 0.076 | 0.074 |
| codec_advection | 1.048 | 1.186 | 1.057 | 0.843 | 0.440 | 0.732 | 0.524 |
| codec_oracle | 1.061 | 1.058 | 1.045 | 1.002 | 0.887 | 0.970 | 0.904 |
| advection | 1.014 | 1.160 | 1.046 | 0.851 | 0.480 | 0.749 | 0.559 |
| persistence | 0.926 | 0.980 | 0.983 | 0.994 | 0.943 | 0.980 | 0.953 |
| _obs share of variance_ | 89.0% | 6.0% | 3.2% | 1.3% | 0.5% | | |

## Wet-area fraction (>= 0.1 mm/h)

| field | % |
|---|---|
| obs | 23.1 |
| regression_mean | 17.2 |
| codec_advection | 21.6 |
| codec_oracle | 23.0 |
| advection | 21.6 |
| persistence | 22.9 |
