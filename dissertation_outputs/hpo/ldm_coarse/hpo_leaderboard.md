# HPO study: ldm_coarse (ldm arm)

Generated from `/home/users/dv321/dissertation_outputs/hpo/ldm_coarse`. Search code at git `6f64654`, study created 2026-08-10T19:58:53.

Stage 1 coarse screen, one factor at a time around the ml_v2 incumbent, plus two small cartesian blocks where an interaction is expected on physical grounds.

## What was searched

- sampler: `grid`
- objective (maximised): `composite` = `(1.0 - crps / crps_adv) - 0.25 * abs(psd_ratio_2_8km - psd_ceiling)`
- admissibility gate: `mae_vs_adv` = `mae <= 1.01 * mae_adv`
- fidelity ladder: `r0` (60000 rows x 3 epochs), `r1` (150000 rows x 4 epochs), `r2` (613892 rows x 6 epochs)
- successive halving with eta = 3, seed pinned at 0 on every trial so comparisons are paired
- planned cost: 15.63 A100-hours
- the same configurations trained to completion at full fidelity would be 702 A100-hours, so the multi-fidelity search costs 2.2 percent of the naive grid

## Baselines

Every trial below is scored against both baselines the brief requires, on the identical validation crops. The advection column is the pysteps baseline: dense Lucas-Kanade optical flow plus Germann-Zawadzki extrapolation, computed once in `build_advection_prior.py` and never learned.

| rung | crops | persistence MAE | advection MAE | climatology MAE | persistence CSI@1 | advection CSI@1 |
|---|---|---|---|---|---|---|
| r0 | 96 | 0.3477 | 0.2797 | 0.4874 | 0.3087 | 0.4277 |
| r1 | 96 | 0.3479 | 0.2702 | 0.5012 | 0.3025 | 0.4220 |
| r2 | 128 | 0.3437 | 0.2669 | 0.4598 | 0.2724 | 0.4035 |

The advection row is an integrity check, not a result: the trainer computes its own advection control on these same crops and the two must agree to float noise. Disagreement means the crop sets diverged and no paired comparison in this study is valid.

## Leaderboard

Ordered by fidelity rung first (deepest rung, and therefore the most evidence, at the top), then by the objective, with trials that failed the admissibility gate sorted last within their rung but kept visible. The ordering is deliberately not a single global sort on the objective: a configuration that scored well once on the cheapest rung has far less behind it than one that survived to the expensive rung, and letting the two compete directly is the same error as quoting a 16-crop diagnostic as a result.

| # | trial | rung | changed from incumbent | objective | gate | MAE | MAE/adv | MAE/pers | CRPSS vs adv | CRPSS vs pers | CSI@1 | CSI@8 | PSD 2-8km | val loss | GPU-h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | trial_015_r2 | r2 | batch=32 | 0.34300 | pass | 0.2399 | 0.899 | 0.698 | 0.3785 | 0.5172 | 0.4483 | 0.0723 | 1.045 | 0.34308 | - |
| 2 | trial_017_r2 | r2 | batch=32, lr=0.0002 | 0.32512 | pass | 0.2399 | 0.899 | 0.698 | 0.3792 | 0.5178 | 0.4483 | 0.0753 | 1.119 | 0.33961 | - |
| 3 | trial_017_r1 | r1 | batch=32, lr=0.0002 | 0.27223 | pass | 0.2579 | 0.955 | 0.741 | 0.3167 | 0.4693 | 0.4538 | 0.1239 | 0.725 | 0.35546 | - |
| 4 | trial_015_r1 | r1 | batch=32 | 0.25708 | pass | 0.2585 | 0.957 | 0.743 | 0.3126 | 0.4661 | 0.4526 | 0.1188 | 0.681 | 0.36148 | - |
| 5 | trial_002_r1 | r1 | width=192 | 0.23164 | pass | 0.2592 | 0.959 | 0.745 | 0.3110 | 0.4649 | 0.4509 | 0.1132 | 0.585 | 0.36279 | - |
| 6 | trial_010_r1 | r1 | p_mean=-0.81 | 0.22272 | pass | 0.2590 | 0.958 | 0.744 | 0.3129 | 0.4663 | 0.4532 | 0.1084 | 0.542 | 0.35237 | - |
| 7 | trial_012_r1 | r1 | batch=32, lr=5e-05 | 0.21175 | pass | 0.2604 | 0.964 | 0.749 | 0.3039 | 0.4594 | 0.4496 | 0.0990 | 0.534 | 0.37053 | - |
| 8 | trial_008_r1 | r1 | weight_decay=0.01 | 0.20355 | pass | 0.2592 | 0.959 | 0.745 | 0.3040 | 0.4595 | 0.4466 | 0.0956 | 0.501 | 0.37024 | - |
| 9 | trial_013_r1 | r1 | lr=5e-05 | 0.18711 | pass | 0.2613 | 0.967 | 0.751 | 0.2981 | 0.4548 | 0.4462 | 0.0826 | 0.459 | 0.38254 | - |
| 10 | trial_016_r1 | r1 | batch=128 | 0.18527 | pass | 0.2571 | 0.951 | 0.739 | 0.2973 | 0.4542 | 0.4487 | 0.0881 | 0.455 | 0.38400 | - |
| 11 | trial_002_r0 | r0 | width=192 | 0.26005 | pass | 0.2769 | 0.990 | 0.796 | 0.3098 | 0.4447 | 0.4485 | 0.0498 | 0.704 | 0.39833 | - |
| 12 | trial_017_r0 | r0 | batch=32, lr=0.0002 | 0.25315 | pass | 0.2702 | 0.966 | 0.777 | 0.3245 | 0.4565 | 0.4463 | 0.0486 | 0.618 | 0.37251 | - |
| 13 | trial_016_r0 | r0 | batch=128 | 0.24456 | pass | 0.2814 | 1.006 | 0.809 | 0.2649 | 0.4086 | 0.4372 | 0.0492 | 0.822 | 0.58031 | - |
| 14 | trial_015_r0 | r0 | batch=32 | 0.24116 | pass | 0.2705 | 0.967 | 0.778 | 0.3218 | 0.4544 | 0.4463 | 0.0436 | 0.581 | 0.38396 | - |
| 15 | trial_013_r0 | r0 | lr=5e-05 | 0.23947 | pass | 0.2776 | 0.993 | 0.799 | 0.3021 | 0.4386 | 0.4401 | 0.0431 | 0.652 | 0.44302 | - |
| 16 | trial_012_r0 | r0 | batch=32, lr=5e-05 | 0.23485 | pass | 0.2735 | 0.978 | 0.787 | 0.3181 | 0.4514 | 0.4420 | 0.0400 | 0.570 | 0.40079 | - |
| 17 | trial_010_r0 | r0 | p_mean=-0.81 | 0.23308 | pass | 0.2609 | 0.933 | 0.750 | 0.3243 | 0.4564 | 0.4469 | 0.0341 | 0.538 | 0.39409 | - |
| 18 | trial_008_r0 | r0 | weight_decay=0.01 | 0.23190 | pass | 0.2652 | 0.948 | 0.763 | 0.3163 | 0.4499 | 0.4473 | 0.0373 | 0.566 | 0.41551 | - |
| 19 | trial_000_r0 | r0 | (incumbent) | 0.23131 | pass | 0.2654 | 0.949 | 0.763 | 0.3163 | 0.4500 | 0.4457 | 0.0355 | 0.563 | 0.41561 | - |
| 20 | trial_003_r0 | r0 | mults=1,2,2,4 | 0.22755 | pass | 0.2654 | 0.949 | 0.763 | 0.3132 | 0.4475 | 0.4496 | 0.0418 | 0.560 | 0.41468 | - |
| 21 | trial_011_r0 | r0 | p_std=1.6 | 0.22640 | pass | 0.2578 | 0.922 | 0.741 | 0.3266 | 0.4583 | 0.4524 | 0.0388 | 0.502 | 0.44871 | - |
| 22 | trial_007_r0 | r0 | weight_decay=0.0001 | 0.22512 | pass | 0.2621 | 0.937 | 0.754 | 0.3185 | 0.4518 | 0.4471 | 0.0362 | 0.529 | 0.41582 | - |
| 23 | trial_021_r0 | r0 | cond_drop=0.2 | 0.22176 | pass | 0.2641 | 0.944 | 0.760 | 0.3137 | 0.4479 | 0.4485 | 0.0390 | 0.535 | 0.41765 | - |
| 24 | trial_019_r0 | r0 | batch=128, lr=0.0002 | 0.22151 | pass | 0.2637 | 0.943 | 0.758 | 0.2840 | 0.4240 | 0.4478 | 0.0450 | 0.653 | 0.55678 | - |
| 25 | trial_022_r0 | r0 | cond_drop=0.0, cond_mode=a-only | 0.21985 | pass | 0.2669 | 0.954 | 0.768 | 0.3095 | 0.4445 | 0.4355 | 0.0256 | 0.545 | 0.40311 | - |
| 26 | trial_001_r0 | r0 | width=96 | 0.21973 | pass | 0.2647 | 0.946 | 0.761 | 0.3099 | 0.4448 | 0.4475 | 0.0470 | 0.542 | 0.42634 | - |
| 27 | trial_023_r0 | r0 | cond_mode=a-only | 0.21941 | pass | 0.2721 | 0.973 | 0.783 | 0.3062 | 0.4418 | 0.4356 | 0.0268 | 0.556 | 0.40424 | - |
| 28 | trial_009_r0 | r0 | p_mean=-1.6 | 0.21720 | pass | 0.2663 | 0.952 | 0.766 | 0.3064 | 0.4420 | 0.4468 | 0.0350 | 0.546 | 0.44432 | - |
| 29 | trial_018_r0 | r0 | lr=0.0002 | 0.21691 | pass | 0.2522 | 0.902 | 0.725 | 0.3262 | 0.4579 | 0.4523 | 0.0403 | 0.466 | 0.39732 | - |
| 30 | trial_024_r0 | r0 | cond_drop=0.2, cond_mode=a-only | 0.20974 | pass | 0.2695 | 0.964 | 0.775 | 0.3046 | 0.4405 | 0.4411 | 0.0304 | 0.524 | 0.40547 | - |

(5 further rows in `ranking.json`; nothing was dropped, the table is truncated for reading only.)

## One-factor-at-a-time effects

Change in the objective from moving one parameter away from the incumbent, everything else held. Sorted by absolute effect, which is the order in which these parameters deserve GPU hours.

| parameter | brief's name | value | incumbent | objective | delta | rung |
|---|---|---|---|---|---|---|
| `dropout` | dropout | 0.1 | 0.0 | 0.19966 | -0.03165 | r0 |
| `attn` | UNet attention resolutions | 16,32 | 16 | 0.20111 | -0.03021 | r0 |
| `width` | UNet width | 192 | 128 | 0.26005 | 0.02873 | r0 |
| `dropout` | dropout | 0.05 | 0.0 | 0.20409 | -0.02723 | r0 |
| `p_mean` | noise schedule (EDM log-sigma mean) | -1.6 | -1.2 | 0.21720 | -0.01412 | r0 |
| `width` | UNet width | 96 | 128 | 0.21973 | -0.01159 | r0 |
| `weight_decay` | weight decay | 0.0001 | 0.0 | 0.22512 | -0.00620 | r0 |
| `p_std` | noise schedule (EDM log-sigma std) | 1.6 | 1.2 | 0.22640 | -0.00492 | r0 |
| `mults` | UNet depth | 1,2,2,4 | 1,2,4 | 0.22755 | -0.00376 | r0 |
| `p_mean` | noise schedule (EDM log-sigma mean) | -0.81 | -1.2 | 0.23308 | 0.00176 | r0 |
| `weight_decay` | weight decay | 0.01 | 0.0 | 0.23190 | 0.00058 | r0 |

1 of 11 cells moved the objective by less than 0.001. Report those as measured null results rather than as tuning wins; a flat axis is information about the model, and this project has already been bitten once by reporting an optimum from a curve that was flat to the eighth decimal (the ridge-gate alpha scan).

## Fidelity transfer

Multi-fidelity search assumes the cheap rung orders configurations the way the expensive rung would. That assumption is measured here rather than asserted.

| from | to | trials in both | Spearman rho | reading |
|---|---|---|---|---|
| r0 | r1 | 8 | 0.381 | weak transfer: treat the screen's ordering as provisional and confirm more candidates |
| r1 | r2 | 2 | - | too few trials promoted to estimate a rank correlation |

## How to read this

- A rung result is a ranking statistic, not a result. Nothing in this table may be quoted as a model score. The winner is confirmed by a full-fidelity run and a full-split evaluation through `evaluate_diffusion.py`, and only those numbers go in the results chapter.
- The objective is deliberately not the validation EDM loss. Across three runs in this project, validation loss and small-scale power move in opposite directions, so ranking on loss selects the smoothest model the search produced. CRPS is used instead because it is strictly proper: it cannot be gamed by smoothing, which flatters MAE through the double-penalty effect, nor by sharpening, which flatters PSD.
- The gate encodes `LDM.md` section 6 criterion (a): matching the advection prior on deterministic accuracy is a precondition for a configuration to be considered at all, not something to be traded away for a better CRPS.
