# Microlensing Wave Effect

Research software for wave-optics diffraction through microlensing fields, including the component-decomposition method and adaptive hierarchical algorithm described in the associated papers.

This repository keeps the numerical implementation separate from entry points, analysis helpers, legacy research scripts, and generated outputs. Structural and workflow changes are intended not to alter scientific formulas, numerical algorithms, random streams, binary formats, or solver control flow.

## Repository layout

```text
app/                    supported C++ command-line entry point
include/                C++ headers and bundled spline header
src/                    maintained C++ numerical implementation
legacy/cpp/             original C++ implementations kept for reference
legacy/python/          original research-analysis scripts
scripts/                maintained Python workflow/analysis helpers
SampleMethod/           runtime remnant mass-function data
CMakeLists.txt           supported C++ build
pyproject.toml           Python environment/dependencies
shell.nix                Nix development environment
```

Generated simulation directories are intentionally excluded from version control.

## Environment

The maintained development workflow uses GCC/G++, C++17, Python 3.11, `uv`, CMake, GNU Make, and Nix.

```bash
nix-shell
uv sync
```

## Recommended one-shot workflow

For the maintained minimum-image branch, the preferred interface is `scripts/run_pipeline.py`. Enter the simulation and frequency parameters once; the script then:

1. configures and incrementally builds the C++ executable with CMake,
2. runs the microlensing simulation,
3. reads the generated adaptive time-delay output,
4. performs the existing minimum-image Fourier calculation,
5. plots the full macro+microlensing amplification and the macro-only amplification on the same frequency axis.

Example:

```bash
uv run python scripts/run_pipeline.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --threads 8 \
  --precision-factor 10 \
  --field-id 10 \
  --seed 12345 \
  --f-min 0.1 \
  --f-max 2000 \
  --df 1
```

All arguments have the same defaults shown above except `field-id`, whose existing default is `15`. After the first build, `--skip-build` can be used to reuse `build/microlensing`.

The maintained Fourier helper currently targets minimum images, so the one-shot workflow requires

```text
1 - kappa + gamma > 0
1 - kappa - gamma > 0
```

The final comparison plot is written to:

```text
Freq_Time_Domain_Result_<field-id>/minimum_amplification_comparison.png
```

and plots

```text
Macro + microlensing: |F(f)|
Macro only:            sqrt(|1 / ((1-kappa)^2 - gamma^2)|)
```

on the same frequency axis. The macro-only amplitude is frequency independent in this maintained minimum-image treatment.

The combined numerical output is:

```text
Freq_Time_Domain_Result_<field-id>/amplification_comparison.csv
```

with columns:

```text
frequency_hz
full_amplification
macro_only_amplification
full_over_macro
phase_rad
```

The analysis also keeps the separate time-domain residual, phase output, absolute amplification CSV, macro-only CSV, and normalized amplification CSV for diagnostics.

## Manual lower-level workflow

The individual stages remain available for debugging and validation.

Build:

```bash
cmake -S . -B build
cmake --build build -j
```

Run the C++ simulation directly:

```bash
./build/microlensing \
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

Validate a minimum-image run:

```bash
uv run python scripts/inspect_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

Run only the Fourier analysis on an existing simulation:

```bash
uv run python scripts/fourier_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10 \
  --f-min 0.1 \
  --f-max 2000 \
  --df 1
```

Shared physical parameters and filename conventions live in `scripts/simulation_config.py`.

## Output directories

`field-id` identifies output directories and is not a physical parameter or random seed. A run creates directories such as:

```text
MicroField_10/
ResultMinimum_10/
ResultSaddle_10/
ResultMaximum_10/
Freq_Time_Domain_Result_10/
```

## Reproducibility

For numerical comparisons:

1. Keep physical parameters fixed.
2. Keep `--seed` fixed.
3. Use distinct `--field-id` values to avoid overwrites.
4. Compare generated lens mass and coordinate files directly.

The maintained RNG implementation keeps mass and coordinate streams independent. Workflow changes do not modify that implementation.

Generated output filenames encode physical parameters to two decimal places. Avoid sweeps that differ only beyond two decimal places unless the naming scheme is deliberately redesigned.

## Binary-format assumptions

The current helper scripts target the Linux/x86-64 development workflow. Existing native binary layouts are preserved; the workflow does not version or reinterpret them.

## Legacy code

Files under `legacy/` are retained as research/reference material and are not part of the supported build. Some original Python scripts contain external dataset paths and should be reviewed before use.

## Citation

If you find this work useful, please cite the associated microlensing wave-effect papers:

- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field: A new algorithm and supplementary study*, Sci. China Phys. Mech. Astron. 66, 239511 (2023), arXiv:2208.13566.
- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field II: an adaptive hierarchical tree algorithm and population study* (2024), arXiv:2409.06747.
