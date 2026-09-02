# AGENTS.md

Guidance for automated contributors working in this research repository.

## Non-negotiable scientific constraint

Treat the numerical implementation as research code, not application code. Do not change scientific formulas, constants, iteration order, tolerances, random-stream semantics, binary layouts, or floating-point expressions unless the task explicitly asks for a scientific/numerical change.

Prefer structural, isolated, testable edits. Avoid broad formatting passes over the large numerical source files.

## Maintained workflow

The preferred user-facing path is:

```text
scripts/run_pipeline.py
  -> CMake build
  -> app/microlensing.cpp
  -> MainDiffraction(...) in src/Micro_field_adaptive.cpp
  -> potential/adaptive-grid calculations in src/GetPsi_micro_field.cpp
  -> deterministic sampling in src/ReproducibleRandom.cpp
  -> generated binary outputs
  -> scripts/fourier_minimum.py
  -> full vs macro-only amplification comparison
```

The one-shot runner owns parameter forwarding. A physical/numerical parameter entered by the user must be passed unchanged to the C++ and Python stages that consume it.

`scripts/inspect_minimum.py` remains a manual validation helper. `legacy/` is reference material and is not part of the supported build.

## Build and environment

```bash
nix-shell
uv sync
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
uv run python scripts/run_pipeline.py --help
```

C++17 and the historical `-O3 -g` flags are intentional.

## Important paths

- `scripts/run_pipeline.py`: preferred one-shot build/simulate/analyze entry point.
- `app/microlensing.cpp`: supported C++ CLI entry point.
- `src/Micro_field_adaptive.cpp`: main adaptive algorithm; avoid unrelated edits.
- `src/GetPsi_micro_field.cpp`: potential, adaptive-grid, and time-delay calculations; avoid unrelated edits.
- `src/ReproducibleRandom.cpp`: deterministic sampling used by the maintained workflow.
- `include/`: headers required by the maintained C++ build.
- `SampleMethod/Remnant_MF.csv`: runtime remnant mass-function data expected by the current sampler.
- `scripts/simulation_config.py`: shared Python physical parameters and filename convention.
- `scripts/inspect_minimum.py`: minimum-image binary validation/time-domain helper.
- `scripts/fourier_minimum.py`: minimum-image Fourier helper and amplification comparison output.

## Amplification output

For the maintained minimum-image Fourier calculation, preserve the existing transform, smooth-component subtraction/reconstruction, truncation, and windowing logic.

The full amplification is the existing numerical `abs(Ff)`. The macro-only amplitude plotted for comparison is

```text
sqrt(abs(1 / ((1 - kappa)^2 - gamma^2)))
```

Do not replace the existing numerical transform with a different FFT/integration implementation merely to simplify the workflow.

The comparison outputs are written under `Freq_Time_Domain_Result_<field-id>/`, including:

```text
minimum_amplification_comparison.png
amplification_comparison.csv
```

## Reproducibility rules

Same physical parameters plus the same seed should reproduce sampled lens masses and coordinates. Keep mass and coordinate RNG streams independent. `field-id` is only an output-directory identifier.

Generated output names encode physical parameters to two decimal places. Do not silently change this convention.

## Validation after workflow changes

At minimum:

```bash
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
python -m py_compile scripts/run_pipeline.py scripts/fourier_minimum.py
uv run python scripts/run_pipeline.py --help
```

For a scientific smoke run, use fixed physical parameters and seed. For reproducibility checks, run the same physical case and seed with two field IDs and compare corresponding `Lens_Mass_*.bin` and `MicroLensCoorXY_*.bin` files with `cmp` or hashes.

## Git workflow

Use a short-lived branch for nontrivial work. Do not force-update `main`. Keep generated results out of source control.
