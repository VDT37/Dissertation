# Physics-Informed Residual Diffusion for UK Precipitation Nowcasting

MSc research project, University of Exeter (COMM514), by Dharan Teja Vipparla. Supervisors: Dr Jawad Fayaz (internal), Dr Andrew Creswick (external).

I built a rainfall nowcaster for the next 15 to 60 minutes on UK radar by training diffusion models. Instead of learning the whole forecast, the diffusion models only learn what a classical physics-based motion forecast (pysteps advection) gets wrong, and add that correction on top.

## How it works

The pipeline has three stages, described in the report as Figure 2.

1. **Advection prior.** `pysteps` (`dense_lucaskanade` motion estimation + `semilagrangian` extrapolation) turns the last 4 radar frames into a forecast `A` at +15/+30/+45/+60 minutes. No learning involved, this is pure physics and is recomputed identically at inference time.
2. **Codec (VAE).** A variational autoencoder compresses each 256x256 rainfall field into a 4x64x64 latent (fourfold spatial compression), so the diffusion model doesn't have to run at full resolution. It's trained on both the observed field `y` and the advection field `A`, with a rain-intensity-weighted L1 loss, a small KL term, and a patch discriminator (no perceptual loss, since there's no pretrained perceptual network for radar). Epoch 17 of 25 was selected as the frozen codec.
3. **Diffusion stage: two arms.**
   - **Arm A (direct residual diffusion):** an EDM-style latent diffusion model (Karras et al., 2022) learns the residual `delta = z_y - z_A` directly, conditioned on the 4 input frames and the advection latent.
   - **Arm B (CorrDiff-style):** a frozen regression U-Net first predicts the conditional mean of the residual (`mu_r`), then a second diffusion model learns only what's left (`r' = delta - mu_r`), following Mardani et al.'s CorrDiff.

Sampling uses the deterministic Heun sampler (25 steps), 8 independent noise seeds give an 8-member ensemble. Three outputs are reported everywhere: the ensemble mean, a single member, and (Arm B only) the frozen regression mean on its own.

## Data

Met Office UK 1 km radar rainfall composite, ODIM HDF5, pulled from the public AWS Open Data bucket (`met-office-radar-obs-data`). Grid is 2175x1725 px at 1 km spacing, sampled every 15 minutes. Record used: 2024-11-21 to 2026-08-09.

Fields are tiled into 256x256 km crops (with a 384x384 context window for advection, centre-cropped after). Of 42 candidate tile positions, 12 pass a quality filter (>=90% in radar range, >=5% wet at 0.1 mm/h). That gives 260,492 unique crops, 613,892 training samples and 53,124 validation samples across the 4 leads. Test is the whole of 2026, held out and scored once (93,738 crops). All modelling happens in a log-reflectivity domain (dBR), not raw mm/h.

## Key results

Validation split, pooled over all four leads (+15, +30, +45 and +60 min together, 53,124 crops in total; report Tables 2 and 3, per-lead breakdown in Appendix E):

| Method                         | MAE (mm/h) | CSI@1 mm/h | CSI@8 mm/h | Fair CRPS |
| ------------------------------ | ---------- | ---------- | ---------- | --------- |
| Persistence                    | 0.3396     | 0.3002     | 0.0708     | n/a       |
| Advection (pysteps)            | 0.2656     | 0.4197     | 0.0861     | n/a       |
| Regression mean (frozen stage) | 0.1955     | 0.4956     | 0.1434     | n/a       |
| Arm A ensemble mean            | 0.2314     | 0.4864     | 0.1329     | 0.1427    |
| Arm B ensemble mean            | 0.2241     | 0.5028     | 0.1439     | 0.1386    |

Arm B beats Arm A on every accuracy column, with the margin growing with rain rate (2.8% at 0.5 mm/h up to 8.2% at 8 mm/h on validation). On the held-out 2026 test year (scored at +60 minutes only) the ranking holds and strengthens: Arm B beats advection by 14.4% on MAE and 46.5% on CSI@8mm/h, and its margin over Arm A widens to 17.8% at the heavy-rain threshold.

The catch: averaging the ensemble costs spatial resolution. A single ensemble member is skilful (FSS-useful) down to a 21 km neighbourhood at heavy rain and +60 minutes, but the ensemble mean needs 51 km, the same as the advection baseline. So the mean is the better point forecast, but a single member is the more realistic field. Neither output alone tells the whole story, both are reported everywhere in the project.

No result exceeds the codec's own ceiling (the observation put through the encoder-decoder round trip): MAE 0.0428 mm/h, 2-8 km spectral power ratio ~0.903. Anything sharper than that is synthesised noise, not recovered structure.

## Repo layout

- `Code/1 - Advection stage/`: `build_prior.py` (downloads radar, runs pysteps, builds crop cache), `evaluate_prior.py`, `fss.py`, `residuals.py`, `plot_domain.py`, `clean_cache.py`.
- `Code/2 - VAE Stage/`: `pack_fields.py` (packs y/A into memmaps), `train_vae.py` (current codec), `train_vae_v1.py` (superseded, checkerboard-artefact version), `pack_latents.py`, `compare_vae.py`.
- `Code/3 - Diffusion stage/`: `pack_mu.py`, `train_regression.py` (frozen conditional-mean stage), `train_ldm.py` (Arm A), `train_corrdiff.py` (Arm B), `sample.py`, `evaluate.py`, `evaluate_mean.py`, `select_ckpt.py`, `pool_leads.py`, `ridge_gate.py` (cheap linear lower-bound check), `plot_case.py`, `plot_fss.py`, and the HPO tooling (`hpo_search.py`, `hpo_spaces.py`, `hpo_report.py`, `hpo_baselines.py`).
- `dissertation_outputs/`: all run artefacts: `Advection/`, `vae_v1/`, `vae_v2/`, `regression*/`, `diffusion/` (early single-lead run), `diffusion_ml/` and `diffusion_ml_v2/` (Arm A, multi-lead), `diffusion_corrdiff_v1/` (Arm B), `hpo/`, `checkpoint_selection.md` (the precommitted checkpoint-selection rule reproduced from training logs).
- `Notes on Research papers/`: reading notes (DDPMs, DGMR, NowcastNet, CorrDiff, DiffCast, SATCast, PreDiff, pysteps, etc.).
- `environment.yml`, and the report PDFs (`COMM514 Final_report 750078836.pdf` is the one to read).

## Getting started

The conda env (`environment.yml`) only covers the CPU-only advection stage. PyTorch for the GPU stages is installed separately.

```
conda env create -f environment.yml
conda activate nowcast
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

Run order, stage by stage (check each script's `--help` for the full flag list, these are the defaults):

```
python "Code/1 - Advection stage/build_prior.py"
python "Code/2 - VAE Stage/pack_fields.py"
python "Code/2 - VAE Stage/train_vae.py"
python "Code/2 - VAE Stage/pack_latents.py"
python "Code/3 - Diffusion stage/train_ldm.py"
python "Code/3 - Diffusion stage/train_regression.py"
python "Code/3 - Diffusion stage/pack_mu.py"
python "Code/3 - Diffusion stage/train_corrdiff.py"
python "Code/3 - Diffusion stage/select_ckpt.py"
python "Code/3 - Diffusion stage/sample.py"
python "Code/3 - Diffusion stage/evaluate.py"
python "Code/3 - Diffusion stage/pool_leads.py"
```

`build_prior.py` is CPU-only and is the only stage that touches the network (downloads radar from the AWS Open Data bucket). Everything after `pack_latents.py` needs a GPU. Most scripts cache their output and skip work that is already done, so rerunning after a crash is usually fine.

## Limitations (from the report)

- The held-out 2026 test evidence exists at +60 minutes only. The lead-time trend (skill growing with lead) is a validation-only claim.
- The checkpoint-selection rule's tiebreak used a 16-crop in-training diagnostic that understates member spectral power by 15-32%, and Arm B's checkpoint choice is sensitive to the tie tolerance (a slightly looser tolerance picks a different epoch).
- Both trained arms over-sharpen slightly: member spectral power sits at 103-119% of the measured codec ceiling, meaning some of that "sharpness" is synthesised noise, not recovered structure.
- No comparison against a trained learned deterministic backbone (e.g. DGMR) was run, only against the published numbers.
