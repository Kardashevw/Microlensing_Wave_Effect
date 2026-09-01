# Microlensing Wave Effect

This repository contains code for calculating wave-optics diffraction through microlensing fields. The implementation includes the component-decomposition method and the adaptive hierarchical algorithm described in the associated papers.

This fork also adds a reproducible local workflow for building, running, and inspecting simulations on Linux/Nix systems.

## Repository overview

- `Micro_field_adaptive.cpp` — main adaptive microlensing-field calculation.
- `GetPsi_micro_field.cpp` — microlensing potential, time-delay, and adaptive-grid routines.
- `SampleMethod/RejectAndAcceptSample.cpp` — original stellar/remnant mass-function sampling implementation.
- `ReproducibleRandom.cpp` / `ReproducibleRandom.h` — deterministic random sampling used by the current example workflow.
- `Example.cpp` — command-line entry point for a single simulation.
- `Example.sh` — C++ build command.
- `scripts/inspect_minimum.py` — validates and plots minimum-image binary output.
- `scripts/fourier_minimum.py` — computes the minimum-image frequency-domain amplification and phase.
- `scripts/simulation_config.py` — shared Python parameter and filename configuration.
- `TotalSgnFourier.py` and other original Python scripts — research-analysis scripts from the upstream project; some still contain paths to external datasets and are not standalone.

## Environment

The maintained development workflow uses:

- GCC / G++
- C++17
- Python 3.11
- `uv` for Python dependencies
- Nix for compiler/runtime dependencies

Enter the development shell and install the Python environment:

```bash
nix-shell
uv sync
```

Check that the main Python dependencies import correctly:

```bash
uv run python -c "import numpy, scipy, matplotlib, tqdm, pandas, seaborn, astropy, mpmath; print('Python environment OK')"
```

> `shell.nix` currently imports `<nixpkgs>` and is therefore not fully pinned. For exact long-term environment reproducibility, migrate to a Nix flake with `flake.lock`.

## Build

Inside `nix-shell`:

```bash
bash Example.sh
```

The resulting executable is `./Example`.

Show available simulation options:

```bash
./Example --help
```

## Running a simulation

A small minimum-image smoke test can be run with:

```bash
time ./Example \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --threads 8 \
  --precision-factor 10 \
  --field-id 10 \
  --seed 12345 \
  |& tee run-p10.log
```

The command-line options are:

| Option | Meaning | Current default |
| --- | --- | ---: |
| `--kappa` | Macro convergence | `0.45` |
| `--gamma` | Macro shear | `0.45` |
| `--kappa-star` | Stellar microlens convergence | `0.03` |
| `--lens-z` | Lens redshift | `0.5` |
| `--source-z` | Source redshift | `1.0` |
| `--threads` | C++ worker threads | `8` |
| `--precision-factor` | Field-size / time-window precision control | `10` |
| `--field-id` | Run/output-directory identifier | `15` |
| `--seed` | Deterministic random seed | `12345` |

`field-id` is an output identifier; it is not a physical parameter. The executable creates the required output directories automatically.

## Reproducible random fields

The current example workflow uses deterministic random sampling. Running the same physical parameters with the same `--seed` produces the same sampled lens masses and coordinates.

For example, run the same case with two different field IDs:

```bash
./Example --kappa 0.45 --gamma 0.45 --kappa-star 0.03 \
  --lens-z 0.5 --source-z 1.0 --threads 8 \
  --precision-factor 10 --field-id 101 --seed 12345

./Example --kappa 0.45 --gamma 0.45 --kappa-star 0.03 \
  --lens-z 0.5 --source-z 1.0 --threads 8 \
  --precision-factor 10 --field-id 102 --seed 12345
```

Then compare the generated lens inputs:

```bash
sha256sum \
  MicroField_101/Lens_Mass_0.45_0.45_0.03_0.50_1.00.bin \
  MicroField_102/Lens_Mass_0.45_0.45_0.03_0.50_1.00.bin

sha256sum \
  MicroField_101/MicroLensCoorXY_0.45_0.45_0.03_0.50_1.00.bin \
  MicroField_102/MicroLensCoorXY_0.45_0.45_0.03_0.50_1.00.bin
```

Each pair should have matching hashes. Changing the seed should change the realization.

## Output layout

For `--field-id 10`, the main output directories are:

```text
MicroField_10/
ResultMinimum_10/
ResultSaddle_10/
ResultMaximum_10/
Freq_Time_Domain_Result_10/
```

For the minimum-image example with

```text
kappa       = 0.45
 gamma      = 0.45
 kappa-star = 0.03
 lens-z     = 0.50
 source-z   = 1.00
```

important files include:

```text
MicroField_10/AveMassAndNum_0.45_0.45_0.03_0.50_1.00.bin
ResultMinimum_10/TimeLength_min_0.45_0.45_0.03_0.50_1.00.bin
ResultMinimum_10/adptive_Area_min_0.45_0.45_0.03_0.50_1.00.bin
ResultMinimum_10/adptive_Time_min_0.45_0.45_0.03_0.50_1.00.bin
```

The binary format used by the current Linux/x86-64 workflow is:

- `AveMassAndNum_*.bin`: three C++ `double` values: average lens mass, total number of lenses, and L2 grid length.
- `TimeLength_*.bin`: one native C++ `long` value. On x86-64 Linux this is 8 bytes and is read as `numpy.int64` by the helper scripts.
- `adptive_Area_*.bin`: `TimeLength` C++ `double` values.
- `adptive_Time_*.bin`: `TimeLength` C++ `double` values.

## Validate a minimum-image run

Use the shared physical parameters and matching field ID:

```bash
uv run python scripts/inspect_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

The script checks binary lengths, finite values, monotonic time samples, and constructs the time-domain response `dA/dt`. It writes its plot under `Freq_Time_Domain_Result_<field-id>/`.

## Fourier-domain analysis

Run:

```bash
uv run python scripts/fourier_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

Optional frequency-grid arguments are:

```text
--f-min   default 0.1 Hz
--f-max   default 2000 Hz
--df      default 1 Hz
```

The script reports:

- macro magnification amplitude
- physical time coefficient
- time step
- retained time-domain duration
- characteristic frequency resolution, approximately `1 / duration`
- Nyquist frequency, `1 / (2 dt)`
- amplification range
- phase range
- low-frequency `|F| / mu` sanity check

It writes CSV and PNG outputs under `Freq_Time_Domain_Result_<field-id>/`.

## Current validation status

A small smoke case with

```text
kappa = 0.45
gamma = 0.45
kappa-star = 0.03
lens-z = 0.5
source-z = 1.0
precision-factor = 10
```

has successfully completed the full pipeline:

```text
C++ build
  -> microlens sampling
  -> adaptive minimum-image simulation
  -> binary validation
  -> time-domain response
  -> Fourier-domain amplification and phase
```

This small case is intended for software validation, not scientific convergence. In one tested realization the retained time window was below 1 ms, so low-frequency structure was not well resolved even though the numerical transform passed its low-frequency macro-limit sanity check.

## Convergence testing

When comparing numerical settings, keep the physical parameters and random seed fixed and use different field IDs to avoid overwriting output. A useful next comparison is:

```text
P10: --precision-factor 10 --seed 12345
P20: --precision-factor 20 --seed 12345
```

Compare at least:

- lens count
- L2 grid length
- nonzero area-sample count
- retained time duration
- characteristic frequency resolution
- Nyquist frequency
- amplification curve
- phase curve
- runtime

Increasing `precision-factor` can change the field boundary and therefore the number of stars, so P10 and P20 are deterministic runs but not necessarily identical nested finite lens fields.

## Important notes

- Do not run the original `TotalSgnFourier.py` as a standalone workflow without reviewing it first; it contains paths to external project datasets.
- Generated output filenames encode physical parameters to two decimal places. Avoid parameter sweeps that differ only beyond two decimal places unless the naming scheme is updated.
- Keep different experiments in different `field-id` directories to prevent accidental overwrites.
- The minimum-image helper scripts currently support the minimum branch only.
- Read `AGENTS.md` before making automated or AI-assisted changes to the repository.

## Citation

If you find this work useful in your research, please cite:

```bibtex
@article{Shan:2022xfx,
    author = "Shan, Xikai and Li, Guoliang and Chen, Xuechun and Zheng, Wenwen and Zhao, Wen",
    title = "{Wave effect of gravitational waves intersected with a microlens field: A new algorithm and supplementary study}",
    eprint = "2208.13566",
    archivePrefix = "arXiv",
    primaryClass = "astro-ph.CO",
    doi = "10.1007/s11433-022-1985-3",
    journal = "Sci. China Phys. Mech. Astron.",
    volume = "66",
    number = "3",
    pages = "239511",
    year = "2023"
}
```

```bibtex
@misc{shan2024waveeffectgravitationalwaves,
    title = {Wave effect of gravitational waves intersected with a microlens field II: an adaptive hierarchical tree algorithm and population study},
    author = {Xikai Shan and Guoliang Li and Xuechun Chen and Wen Zhao and Bin Hu and Shude Mao},
    year = {2024},
    eprint = {2409.06747},
    archivePrefix = {arXiv},
    primaryClass = {astro-ph.IM},
    url = {https://arxiv.org/abs/2409.06747}
}
```
