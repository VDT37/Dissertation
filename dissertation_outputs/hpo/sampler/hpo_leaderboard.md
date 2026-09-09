# HPO study: inference_grid (inference arm)

Generated from `/home/users/dv321/dissertation_outputs/hpo/sampler`. Search code at git `ae67b1d`, study created 2026-08-10T20:00:43.

Stage 4 sampler sweep on a frozen checkpoint. One factor at a time around the production sampler setting.

## What was searched

- sampler: `grid`
- objective (maximised): `infer_composite` = `(1.0 - crps_fair / mae_adv) - 0.50 * abs(spread_rmse_ratio - spread_rmse_ideal)`
- admissibility gate: `none` = `True`
- fidelity ladder: `r0` (3000 rows x 0 epochs)
- successive halving with eta = 3, seed pinned at 0 on every trial so comparisons are paired
- planned cost: 9.02 A100-hours

## Baselines

Every trial below is scored against both baselines the brief requires, on the identical validation crops. The advection column is the pysteps baseline: dense Lucas-Kanade optical flow plus Germann-Zawadzki extrapolation, computed once in `build_advection_prior.py` and never learned.

No baselines file was found in this study directory or beside it, so the per-rung baseline table is omitted. The persistence and advection COLUMNS in the leaderboard below are unaffected: those come from each trial's own record, not from this file. Run `hpo_baselines.py` and re-run the report to restore the table.

## Leaderboard

Ordered by fidelity rung first (deepest rung, and therefore the most evidence, at the top), then by the objective, with trials that failed the admissibility gate sorted last within their rung but kept visible. The ordering is deliberately not a single global sort on the objective: a configuration that scored well once on the cheapest rung has far less behind it than one that survived to the expensive rung, and letting the two compete directly is the same error as quoting a 16-crop diagnostic as a result.

| # | trial | rung | changed from incumbent | objective | gate | MAE | MAE/adv | MAE/pers | CRPSS vs adv | CRPSS vs pers | CSI@1 | CSI@8 | PSD 2-8km | val loss | GPU-h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | trial_001_r0 | r0 | steps=18 | 0.47615 | pass | 0.2779 | 0.860 | 0.733 | 0.4769 | 0.5541 | 0.4043 | 0.0791 | 0.986 | - | - |
| 2 | trial_003_r0 | r0 | members=4 | 0.46506 | pass | 0.2862 | 0.886 | 0.755 | 0.4766 | 0.5538 | 0.3840 | 0.0799 | 0.894 | - | - |
| 3 | trial_000_r0 | r0 | (incumbent) | 0.46318 | pass | 0.2754 | 0.853 | 0.727 | 0.4767 | 0.5539 | 0.4058 | 0.0798 | 0.894 | - | - |
| 4 | trial_004_r0 | r0 | members=16 | 0.46118 | pass | 0.2691 | 0.833 | 0.710 | 0.4765 | 0.5538 | 0.4197 | 0.0791 | 0.894 | - | - |
| 5 | trial_007_r0 | r0 | churn=10.0 | 0.46064 | pass | 0.2819 | 0.873 | 0.744 | 0.4787 | 0.5556 | 0.4057 | 0.0790 | 1.170 | - | 0.60 |
| 6 | trial_008_r0 | r0 | churn=40.0 | 0.45989 | pass | 0.2820 | 0.873 | 0.744 | 0.4787 | 0.5556 | 0.4057 | 0.0790 | 1.173 | - | 0.60 |
| 7 | trial_002_r0 | r0 | steps=50 | 0.45108 | pass | 0.2732 | 0.846 | 0.721 | 0.4766 | 0.5539 | 0.4067 | 0.0800 | 0.828 | - | - |
| 8 | trial_005_r0 | r0 | guidance=1.25 | 0.42959 | pass | 0.2701 | 0.836 | 0.713 | 0.4740 | 0.5516 | 0.4031 | 0.0762 | 0.889 | - | 1.10 |
| 9 | trial_006_r0 | r0 | guidance=1.5 | 0.39538 | pass | 0.2719 | 0.842 | 0.718 | 0.4578 | 0.5379 | 0.3927 | 0.0707 | 0.936 | - | 1.10 |

## One-factor-at-a-time effects

Change in the objective from moving one parameter away from the incumbent, everything else held. Sorted by absolute effect, which is the order in which these parameters deserve GPU hours.

| parameter | brief's name | value | incumbent | objective | delta | rung |
|---|---|---|---|---|---|---|
| `guidance` | classifier-free guidance weight | 1.5 | 1.0 | 0.39538 | -0.06780 | r0 |
| `guidance` | classifier-free guidance weight | 1.25 | 1.0 | 0.42959 | -0.03359 | r0 |
| `steps` | number of diffusion steps | 18 | 25 | 0.47615 | 0.01296 | r0 |
| `steps` | number of diffusion steps | 50 | 25 | 0.45108 | -0.01210 | r0 |
| `churn` | noise schedule (sampler stochasticity S_churn) | 40.0 | 0.0 | 0.45989 | -0.00329 | r0 |
| `churn` | noise schedule (sampler stochasticity S_churn) | 10.0 | 0.0 | 0.46064 | -0.00255 | r0 |
| `members` | ensemble size | 16 | 8 | 0.46118 | -0.00200 | r0 |
| `members` | ensemble size | 4 | 8 | 0.46506 | 0.00187 | r0 |

## Fidelity transfer

Multi-fidelity search assumes the cheap rung orders configurations the way the expensive rung would. That assumption is measured here rather than asserted.

Only one rung has scored trials, so there is nothing to correlate yet.

## How to read this

- A rung result is a ranking statistic, not a result. Nothing in this table may be quoted as a model score. The winner is confirmed by a full-fidelity run and a full-split evaluation through `evaluate_diffusion.py`, and only those numbers go in the results chapter.
- The objective is deliberately not the validation EDM loss. Across three runs in this project, validation loss and small-scale power move in opposite directions, so ranking on loss selects the smoothest model the search produced. CRPS is used instead because it is strictly proper: it cannot be gamed by smoothing, which flatters MAE through the double-penalty effect, nor by sharpening, which flatters PSD.
- The gate encodes `LDM.md` section 6 criterion (a): matching the advection prior on deterministic accuracy is a precondition for a configuration to be considered at all, not something to be traded away for a better CRPS.
