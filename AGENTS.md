# AGENTS.md

This file is for AI coding agents and automated contributors working in this repository. Read it before editing code.

## Project purpose

This is research code for wave-optics diffraction through microlensing fields. The numerical core is C++; Python is used for validation, plotting, and Fourier-domain analysis.

The repository originated as research software and still contains legacy assumptions, commented experiments, native binary formats, and some scripts with external hard-coded data paths. Prefer small, testable changes over broad refactors.

## Current maintained workflow

The actively maintained path is:

```text
Example.cpp
  -> MainDiffraction(...) in Micro_field_adaptive.cpp
  -> microlens mass/position generation
  -> adaptive time-delay binaries
  -> scripts/inspect_minimum.py
  -> scripts/fourier_minimum.py
```

Use this path as the default unless the user explicitly asks about a different original analysis script.

## Environment

Use the repository environment rather than the system Python directly:

```bash
nix-shell
uv sync
```

Build with:

```bash
bash Example.sh
```

`Example.sh` uses C++17 because `Example.cpp` uses `std::filesystem`.

Python version is pinned at the project level to 3.11. Nix provides the interpreter and native runtime libraries; `uv` manages Python dependencies.

Do not replace the Nix + uv setup with Conda, Poetry, pip-only instructions, or another environment manager unless explicitly requested.

## Important files

- `Example.cpp`
  - Supported CLI entry point.
  - Creates output directories.
  - Configures deterministic seed.
  - Calls `MainDiffraction`.

- `Example.sh`
  - Single C++ build command.
  - Keep C++17 unless filesystem usage is removed intentionally.

- `Micro_field_adaptive.cpp`
  - Main adaptive algorithm.
  - Very large legacy research file.
  - Avoid unrelated formatting or large mechanical rewrites.

- `GetPsi_micro_field.cpp`
  - Potential, adaptive-grid, and time-delay calculations.
  - Contains the field-size logic controlled by `PrecisionFactor`.

- `SampleMethod/RejectAndAcceptSample.cpp`
  - Original random mass sampler.
  - Retained for upstream compatibility.

- `ReproducibleRandom.cpp` / `ReproducibleRandom.h`
  - Deterministic mass and coordinate generation for the maintained example workflow.
  - The current CLI seed is set by `SetSimulationSeed`.
  - Keep mass and position RNG streams independent.

- `scripts/simulation_config.py`
  - Shared Python physical parameters and filename convention.
  - Reuse this rather than re-hard-coding parameters in new helper scripts.

- `scripts/inspect_minimum.py`
  - Minimum-image binary validation and time-domain plot.

- `scripts/fourier_minimum.py`
  - Minimum-image Fourier transform, amplification, and phase.

- `TotalSgnFourier.py`
  - Original research script.
  - Contains external dataset paths and should not be treated as a clean standalone CLI.

## Supported simulation CLI

The maintained executable accepts:

```text
--kappa
--gamma
--kappa-star
--lens-z
--source-z
--threads
--precision-factor
--field-id
--seed
```

Current defaults in `Example.cpp` are:

```text
kappa            = 0.45
gamma            = 0.45
kappa-star       = 0.03
lens-z           = 0.5
source-z         = 1.0
threads          = 8
precision-factor = 10
field-id         = 15
seed             = 12345
```

Do not add a physical parameter only to C++ or only to Python. If a new physical parameter affects file lookup or analysis, update the shared parameter flow consistently.

## Reproducibility rules

For comparisons:

1. Keep the physical parameters fixed.
2. Keep `--seed` fixed.
3. Use a different `--field-id` for each run to avoid overwrites.
4. Record runtime and the printed simulation configuration.

Same physical parameters + same seed should reproduce the sampled lens masses and coordinates. Different seeds should change the realization.

The mass and coordinate RNG streams should remain separate. Do not make coordinate generation depend on how many rejection-sampling draws the mass sampler happened to consume.

## Field ID is not physics

`field-id` only identifies output directories such as:

```text
MicroField_10/
ResultMinimum_10/
Freq_Time_Domain_Result_10/
```

Do not use it as a random seed or physical parameter.

## Filename convention

Python uses `scripts/simulation_config.py` to construct the suffix:

```text
{kappa:.2f}_{gamma:.2f}_{kappa_star:.2f}_{lens_z:.2f}_{source_z:.2f}.bin
```

Example:

```text
0.45_0.45_0.03_0.50_1.00.bin
```

C++ output filenames must stay compatible with that convention.

Important limitation: parameters are encoded to only two decimal places. Do not run sweeps that differ only beyond two decimal places without first redesigning the naming scheme.

## Binary format assumptions

Current helper scripts target the Linux/x86-64 workflow used during development.

- `AveMassAndNum_*.bin`
  - 3 native C++ `double` values.
  - average lens mass
  - number of lenses
  - L2 grid length

- `TimeLength_*.bin`
  - 1 native C++ `long`.
  - on x86-64 Linux this is 8 bytes and is read as `numpy.int64`.

- `adptive_Area_*.bin`
  - `TimeLength` native C++ doubles.

- `adptive_Time_*.bin`
  - `TimeLength` native C++ doubles.

If cross-platform portability becomes a goal, replace native C++ types in the on-disk format with explicitly sized types and version the format. Do not silently change the binary layout because existing files would become ambiguous.

## Minimum-image branch

With the standard smoke parameters:

```text
kappa = 0.45
gamma = 0.45
```

we have:

```text
1 - kappa + gamma > 0
1 - kappa - gamma > 0
```

so the maintained smoke test exercises the minimum-image branch.

The current Python helper scripts are minimum-image helpers. Do not claim they validate saddle/maximum branches unless those paths are explicitly implemented and tested.

## Fourier-analysis notes

`scripts/fourier_minimum.py` follows the minimum-image logic of the original `TotalSgnFourier.py` but is designed to work on a single standalone simulation.

It should continue to report:

```text
Raw F(t) samples
Time step dt
Samples after cut
Time duration
Characteristic df = 1 / duration
Nyquist frequency = 1 / (2 dt)
Frequency range
|F| range
Phase range
Low-frequency |F| / mu
```

The low-frequency `|F| / mu` value is a useful implementation sanity check, but it is not by itself evidence of scientific convergence.

Do not fully vectorize the Fourier transform into a giant `frequency x time` array without checking memory usage. The current explicit frequency loop is intentionally memory-safe for moderate runs.

## Smoke-test history

A known successful small run used:

```text
kappa            = 0.45
gamma            = 0.45
kappa-star       = 0.03
lens-z           = 0.5
source-z         = 1.0
precision-factor = 10
```

A previous successful realization produced approximately:

```text
NStar            = 98
L2 grid length   = 201
TimeLength       = 101448
nonzero area bins = 1448
dt               = 1e-6 s
```

A Fourier smoke run retained about `8.67e-4 s`, corresponding to a characteristic frequency resolution around `1153 Hz`. These values are historical smoke-test observations, not golden scientific outputs. Seeded runs may differ from older pre-seed runs.

## Known legacy issues and pitfalls

- `TotalSgnFourier.py` and several other original scripts contain paths to external projects such as `../Paper4_CE_Modify/...`.
- The original remnant sampler once used a hard-coded absolute path. The maintained workflow expects `SampleMethod/Remnant_MF.csv` from the repository.
- `PrecisionFactor` may be internally adjusted by field-boundary logic in `Preparation4CreatPhiKappaStar`; check printed `NOW SNR` when interpreting a run.
- Increasing `PrecisionFactor` can significantly increase field size, star count, grid size, runtime, and memory use.
- The code uses native binary writes. Never edit them as text.
- Large generated output directories should not be committed.
- Avoid broad cleanup of commented legacy research code unless specifically requested.

## Validation commands

After C++ changes:

```bash
nix-shell
bash Example.sh
./Example --help
```

A small run:

```bash
./Example \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --threads 8 \
  --precision-factor 10 \
  --field-id 10 \
  --seed 12345
```

Inspect:

```bash
uv run python scripts/inspect_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

Fourier analysis:

```bash
uv run python scripts/fourier_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

## Reproducibility test

Run the same case with two field IDs and the same seed, then compare:

```bash
sha256sum MicroField_101/Lens_Mass_*.bin MicroField_102/Lens_Mass_*.bin
sha256sum MicroField_101/MicroLensCoorXY_*.bin MicroField_102/MicroLensCoorXY_*.bin
```

For a stricter comparison, use `cmp` on corresponding files.

If masses or coordinates differ for identical physical parameters and seed, treat that as a regression.

## Next planned engineering task

The next useful feature is a convergence-comparison helper, tentatively:

```text
scripts/compare_runs.py
```

It should compare a P10 and P20 run made with the same physical parameters and seed but separate field IDs.

Recommended initial pair:

```text
P10: precision-factor 10, seed 12345
P20: precision-factor 20, seed 12345
```

It should report or plot at least:

- number of lenses
- L2 grid length
- total time-delay curve length
- nonzero area samples
- retained time duration
- characteristic frequency resolution
- Nyquist frequency
- normalized amplification curves
- phase curves
- difference metrics over the common frequency grid
- wall-clock runtime if logs are provided

Important: changing `PrecisionFactor` changes the field boundary and potentially `NStar`, so P10/P20 are deterministic comparisons but not guaranteed to be perfectly nested realizations.

## Coding guidelines

- Prefer small commits with one purpose.
- Preserve scientific formulas unless the task explicitly concerns them.
- Add validation around file I/O and parameter parsing rather than silently accepting bad inputs.
- Reuse `scripts/simulation_config.py` for new minimum-image Python tools.
- Keep generated results out of source control.
- Do not remove original citation information.
- Update `README.md` and this file when the supported workflow changes materially.

## Git workflow for AI agents

Prefer a short-lived branch for nontrivial changes, for example:

```text
chatgpt/<topic>
```

Build/test before merging. Do not force-update `main` unless the user explicitly requests it. Fast-forward merges are acceptable when the feature branch is directly ahead of `main` and the user has approved the change.
