# AGENTS.md

Guidance for automated contributors working in this research repository.

## Non-negotiable scientific constraint

Treat the numerical implementation as research code, not application code. Do not change scientific formulas, constants, iteration order, tolerances, random-stream semantics, binary layouts, or floating-point expressions unless the task explicitly asks for a scientific/numerical change.

Prefer structural, isolated, testable edits. Avoid broad formatting passes over the large numerical source files.

## Maintained workflow

```text
app/microlensing.cpp
  -> MainDiffraction(...) in src/Micro_field_adaptive.cpp
  -> potential/adaptive-grid calculations in src/GetPsi_micro_field.cpp
  -> deterministic sampling in src/ReproducibleRandom.cpp
  -> generated binary outputs
  -> scripts/inspect_minimum.py
  -> scripts/fourier_minimum.py
```

`legacy/` is reference material and is not part of the supported build.

## Build and environment

```bash
nix-shell
uv sync
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
```

C++17 and the historical `-O3 -g` flags are intentional.

## Important paths

- `app/microlensing.cpp`: supported CLI entry point.
- `src/Micro_field_adaptive.cpp`: main adaptive algorithm; avoid unrelated edits.
- `src/GetPsi_micro_field.cpp`: potential, adaptive-grid, and time-delay calculations; avoid unrelated edits.
- `src/ReproducibleRandom.cpp`: deterministic sampling used by the maintained workflow.
- `include/`: headers required by the maintained C++ build.
- `SampleMethod/Remnant_MF.csv`: runtime remnant mass-function data expected by the current sampler.
- `scripts/simulation_config.py`: shared Python physical parameters and filename convention.
- `scripts/inspect_minimum.py`: minimum-image binary validation/time-domain helper.
- `scripts/fourier_minimum.py`: minimum-image Fourier helper.

## Reproducibility rules

Same physical parameters plus the same seed should reproduce sampled lens masses and coordinates. Keep mass and coordinate RNG streams independent. `field-id` is only an output-directory identifier.

Generated output names encode physical parameters to two decimal places. Do not silently change this convention.

## Validation after C++ changes

```bash
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
```

For a smoke run, use fixed physical parameters and seed, then inspect with the maintained Python scripts. For reproducibility checks, run the same physical case and seed with two field IDs and compare corresponding `Lens_Mass_*.bin` and `MicroLensCoorXY_*.bin` files with `cmp` or hashes.

## Git workflow

Use a short-lived branch for nontrivial work. Do not force-update `main`. Keep generated results out of source control.
