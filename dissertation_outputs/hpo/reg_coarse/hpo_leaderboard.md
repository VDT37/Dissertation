# HPO study: regression_coarse (regression arm)

Generated from `/home/users/dv321/dissertation_outputs/hpo/reg_coarse`. Search code at git `ae67b1d`, study created 2026-08-10T20:08:53.

Screen for the deterministic conditional-mean network that feeds the CorrDiff arm. No noise schedule here: this net is trained under a plain regression loss, so the searchable set is optimisation and capacity only.

## What was searched

- sampler: `grid`
- objective (maximised): `val_ev` = `val_ev`
- admissibility gate: `gate_c` = `val_ev >= 0.10`
- fidelity ladder: `r0` (60000 rows x 2 epochs), `r1` (200000 rows x 3 epochs)
- successive halving with eta = 3, seed pinned at 0 on every trial so comparisons are paired
- planned cost: 2.62 A100-hours
- the same configurations trained to completion at full fidelity would be 265 A100-hours, so the multi-fidelity search costs 1.0 percent of the naive grid

## Baselines

Every trial below is scored against both baselines the brief requires, on the identical validation crops. The advection column is the pysteps baseline: dense Lucas-Kanade optical flow plus Germann-Zawadzki extrapolation, computed once in `build_advection_prior.py` and never learned.

| rung | crops | persistence MAE | advection MAE | climatology MAE | persistence CSI@1 | advection CSI@1 |
|---|---|---|---|---|---|---|
| r0 | 96 | 0.3477 | 0.2797 | 0.4874 | 0.3087 | 0.4277 |
| r1 | 96 | 0.3179 | 0.2443 | 0.4556 | 0.2977 | 0.4274 |

The advection row is an integrity check, not a result: the trainer computes its own advection control on these same crops and the two must agree to float noise. Disagreement means the crop sets diverged and no paired comparison in this study is valid.

## Leaderboard

Ordered by fidelity rung first (deepest rung, and therefore the most evidence, at the top), then by the objective, with trials that failed the admissibility gate sorted last within their rung but kept visible. The ordering is deliberately not a single global sort on the objective: a configuration that scored well once on the cheapest rung has far less behind it than one that survived to the expensive rung, and letting the two compete directly is the same error as quoting a 16-crop diagnostic as a result.

| # | trial | rung | changed from incumbent | objective | gate | MAE | MAE/adv | MAE/pers | CRPSS vs adv | CRPSS vs pers | CSI@1 | CSI@8 | PSD 2-8km | val loss | GPU-h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | trial_005_r1 | r1 | width=192 | 0.44959 | pass | 0.1888 | 0.773 | 0.543 | - | - | 0.4868 | 0.0859 | 0.090 | - | 0.95 |
| 2 | trial_002_r1 | r1 | lr=0.0002 | 0.44850 | pass | 0.1900 | 0.778 | 0.546 | - | - | 0.4846 | 0.0878 | 0.085 | - | 0.59 |
| 3 | trial_003_r1 | r1 | lr=0.0004 | 0.44079 | pass | 0.1913 | 0.783 | 0.550 | - | - | 0.4805 | 0.0794 | 0.069 | - | 0.59 |
| 4 | trial_002_r0 | r0 | lr=0.0002 | 0.38511 | pass | 0.2175 | 0.778 | 0.626 | - | - | 0.4629 | 0.0584 | 0.047 | - | 0.18 |
| 5 | trial_003_r0 | r0 | lr=0.0004 | 0.38417 | pass | 0.2175 | 0.778 | 0.626 | - | - | 0.4635 | 0.0604 | 0.046 | - | 0.18 |
| 6 | trial_005_r0 | r0 | width=192 | 0.38360 | pass | 0.2199 | 0.786 | 0.633 | - | - | 0.4667 | 0.0642 | 0.052 | - | 0.25 |
| 7 | trial_007_r0 | r0 | weight_decay=0.01 | 0.37949 | pass | 0.2170 | 0.776 | 0.624 | - | - | 0.4602 | 0.0542 | 0.053 | - | 0.15 |
| 8 | trial_000_r0 | r0 | (incumbent) | 0.37934 | pass | 0.2171 | 0.776 | 0.624 | - | - | 0.4617 | 0.0542 | 0.054 | - | - |
| 9 | trial_006_r0 | r0 | weight_decay=0.0001 | 0.37864 | pass | 0.2172 | 0.776 | 0.625 | - | - | 0.4606 | 0.0548 | 0.053 | - | 0.18 |
| 10 | trial_008_r0 | r0 | dropout=0.05 | 0.37406 | pass | 0.2187 | 0.782 | 0.629 | - | - | 0.4659 | 0.0520 | 0.055 | - | 0.17 |
| 11 | trial_004_r0 | r0 | width=96 | 0.36866 | pass | 0.2194 | 0.784 | 0.631 | - | - | 0.4558 | 0.0526 | 0.065 | - | 0.15 |
| 12 | trial_001_r0 | r0 | lr=5e-05 | 0.36421 | pass | 0.2174 | 0.777 | 0.625 | - | - | 0.4602 | 0.0518 | 0.070 | - | - |

## One-factor-at-a-time effects

Change in the objective from moving one parameter away from the incumbent, everything else held. Sorted by absolute effect, which is the order in which these parameters deserve GPU hours.

| parameter | brief's name | value | incumbent | objective | delta | rung |
|---|---|---|---|---|---|---|
| `lr` | learning rate | 5e-05 | 0.0001 | 0.36421 | -0.01513 | r0 |
| `width` | UNet width | 96 | 128 | 0.36866 | -0.01068 | r0 |
| `lr` | learning rate | 0.0002 | 0.0001 | 0.38511 | 0.00577 | r0 |
| `dropout` | dropout | 0.05 | 0.0 | 0.37406 | -0.00528 | r0 |
| `lr` | learning rate | 0.0004 | 0.0001 | 0.38417 | 0.00483 | r0 |
| `width` | UNet width | 192 | 128 | 0.38360 | 0.00426 | r0 |
| `weight_decay` | weight decay | 0.0001 | 0.0 | 0.37864 | -0.00070 | r0 |
| `weight_decay` | weight decay | 0.01 | 0.0 | 0.37949 | 0.00015 | r0 |

2 of 8 cells moved the objective by less than 0.001. Report those as measured null results rather than as tuning wins; a flat axis is information about the model, and this project has already been bitten once by reporting an optimum from a curve that was flat to the eighth decimal (the ridge-gate alpha scan).

## Fidelity transfer

Multi-fidelity search assumes the cheap rung orders configurations the way the expensive rung would. That assumption is measured here rather than asserted.

| from | to | trials in both | Spearman rho | reading |
|---|---|---|---|---|
| r0 | r1 | 3 | -0.500 | weak transfer: treat the screen's ordering as provisional and confirm more candidates |

## How to read this

- A rung result is a ranking statistic, not a result. Nothing in this table may be quoted as a model score. The winner is confirmed by a full-fidelity run and a full-split evaluation through `evaluate_diffusion.py`, and only those numbers go in the results chapter.
- The objective is deliberately not the validation EDM loss. Across three runs in this project, validation loss and small-scale power move in opposite directions, so ranking on loss selects the smoothest model the search produced. CRPS is used instead because it is strictly proper: it cannot be gamed by smoothing, which flatters MAE through the double-penalty effect, nor by sharpening, which flatters PSD.
- The gate encodes `LDM.md` section 6 criterion (a): matching the advection prior on deterministic accuracy is a precondition for a configuration to be considered at all, not something to be traded away for a better CRPS.
