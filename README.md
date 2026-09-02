# Microlensing Wave Effect

Research software for wave-optics diffraction through microlensing fields, including the component-decomposition method and adaptive hierarchical algorithm described in the associated papers.

This repository keeps the numerical implementation separate from entry points, analysis helpers, legacy research scripts, and generated outputs. The reorganization is intentionally structural: scientific formulas, numerical algorithms, random streams, binary formats, and solver control flow are not changed.

## Repository layout

```text
app/                    supported C++ command-line entry point
include/                C++ headers and bundled spline header
src/                    maintained C++ numerical implementation
legacy/cpp/             original C++ implementations kept for reference
legacy/python/          original research-analysis scripts
scripts/                maintained Python validation/analysis helpers
SampleMethod/           runtime remnant mass-function data
CMakeLists.txt           supported C++ build
pyproject.toml           Python environment/dependencies
shell.nix                Nix development environment
```

Generated simulation directories are intentionally excluded from version control.

## Environment

The maintained development workflow uses GCC/G++, C++17, Python 3.11, `uv`, and Nix.

```bash
nix-shell
uv sync
```

## Build

```bash
cmake -S . -B build
cmake --build build -j
```

The executable is:

```bash
./build/microlensing
```

Show options with:

```bash
./build/microlensing --help
```

The CMake target keeps the historical `-O3 -g` compilation flags and C++17 standard used by the previous build script.

## Run a simulation

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

`field-id` identifies output directories and is not a physical parameter or random seed.

The maintained executable creates output directories such as:

```text
MicroField_10/
ResultMinimum_10/
ResultSaddle_10/
ResultMaximum_10/
Freq_Time_Domain_Result_10/
```

## Maintained analysis workflow

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

Compute minimum-image Fourier-domain amplification and phase:

```bash
uv run python scripts/fourier_minimum.py \
  --kappa 0.45 \
  --gamma 0.45 \
  --kappa-star 0.03 \
  --lens-z 0.5 \
  --source-z 1.0 \
  --field-id 10
```

Shared physical parameters and filename conventions live in `scripts/simulation_config.py`.

## Reproducibility

For numerical comparisons:

1. Keep physical parameters fixed.
2. Keep `--seed` fixed.
3. Use distinct `--field-id` values to avoid overwrites.
4. Compare generated lens mass and coordinate files directly.

The maintained RNG implementation keeps mass and coordinate streams independent. The repository reorganization does not modify that implementation.

## Binary-format assumptions

The current helper scripts target the Linux/x86-64 development workflow. Existing native binary layouts are preserved; this cleanup does not version or reinterpret them.

## Legacy code

Files under `legacy/` are retained as research/reference material and are not part of the supported build. Some original Python scripts contain external dataset paths and should be reviewed before use.

## Citation

If you find this work useful, please cite the associated microlensing wave-effect papers:

- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field: A new algorithm and supplementary study*, Sci. China Phys. Mech. Astron. 66, 239511 (2023), arXiv:2208.13566.
- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field II: an adaptive hierarchical tree algorithm and population study* (2024), arXiv:2409.06747.
