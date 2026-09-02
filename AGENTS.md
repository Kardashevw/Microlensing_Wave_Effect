# AGENTS.md

Guidance for automated contributors working in this research repository.

## Non-negotiable scientific constraint

Treat the numerical implementation as research code, not application code. Do not change scientific formulas, constants, iteration order, tolerances, random-stream semantics, binary layouts, or floating-point expressions unless the task explicitly asks for a scientific/numerical change.

Prefer structural, isolated, testable edits. Avoid broad formatting passes over the large numerical source files.

## Maintained workflow

The preferred user-facing path is:

```text
scripts/run_pipeline.py
  -> classify image from kappa/gamma
  -> CMake build
  -> app/microlensing.cpp
  -> MainDiffraction(...) in src/Micro_field_adaptive.cpp
  -> generated branch-specific binary output
  -> scripts/fourier_minimum.py | fourier_saddle.py | fourier_maximum.py
  -> full vs macro-only amplification comparison
```

The one-shot runner owns parameter forwarding. A physical/numerical parameter entered by the user must be passed unchanged to the C++ and Python stages that consume it.

`legacy/` is reference material and is not part of the supported build.

## Image classification

Use the macro Jacobian eigenvalues

```text
lambda_r = 1 - kappa + gamma
lambda_t = 1 - kappa - gamma
```

- minimum: both positive
- saddle: opposite signs
- maximum: both negative
- critical: either exactly zero; reject

The current C++ saddle branch only supports `lambda_r > 0` and `lambda_t < 0`. Do not silently rotate/relabel the opposite saddle orientation because that would require a C++ numerical change.

For positive frequency, the smooth macro complex factors are

```text
minimum  +sqrt(|mu|)
saddle   -i sqrt(|mu|)
maximum  -sqrt(|mu|)
```

with

```text
sqrt(|mu|) = sqrt(abs(1 / ((1-kappa)^2 - gamma^2)))
```

The macro-only magnitude plotted in every branch is therefore the same `sqrt(|mu|)`.

## Branch analysis rules

- `scripts/fourier_minimum.py`: preserve the existing maintained transform, smooth subtraction/reconstruction, three-fifths cut, and taper.
- `scripts/fourier_saddle.py`: preserve the active saddle equations from `legacy/python/TotalSgnFourier.py`, including the finite-field analytic saddle subtraction and explicit transform; restore the `-i sqrt(|mu|)` smooth term.
- `scripts/fourier_maximum.py`: the legacy Python code had no standalone maximum helper. The maintained extension reverses time around the final nonzero response, uses the minimum-form residual treatment in reversed time, then maps back with `F_max = -conjugate(F_reversed)` with the maximum as phase origin. Do not change this convention casually; it encodes the maximum Morse phase.

The maximum branch needs a representative scientific smoke/convergence test before being treated as a golden validated analysis path.

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
- `scripts/image_type.py`: image classification and macro Morse-phase conventions.
- `scripts/fourier_minimum.py`: minimum Fourier helper.
- `scripts/fourier_saddle.py`: saddle Fourier helper.
- `scripts/fourier_maximum.py`: maximum Fourier helper.
- `app/microlensing.cpp`: supported C++ CLI entry point.
- `src/Micro_field_adaptive.cpp`: main adaptive algorithm; avoid unrelated edits.
- `src/GetPsi_micro_field.cpp`: potential, adaptive-grid, and time-delay calculations; avoid unrelated edits.
- `src/ReproducibleRandom.cpp`: deterministic sampling used by the maintained workflow.
- `include/`: headers required by the maintained C++ build.
- `SampleMethod/Remnant_MF.csv`: runtime remnant mass-function data expected by the current sampler.
- `scripts/simulation_config.py`: shared Python physical parameters and filename convention.
- `scripts/inspect_minimum.py`: minimum-image binary validation/time-domain helper.

## Reproducibility rules

Same physical parameters plus the same seed should reproduce sampled lens masses and coordinates. Keep mass and coordinate RNG streams independent. `field-id` is only an output-directory identifier.

Generated output names encode physical parameters to two decimal places. Do not silently change this convention.

## Validation after workflow changes

At minimum:

```bash
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
python -m py_compile scripts/run_pipeline.py scripts/image_type.py scripts/simulation_config.py scripts/fourier_minimum.py scripts/fourier_saddle.py scripts/fourier_maximum.py
python -m unittest discover -s tests
uv run python scripts/run_pipeline.py --help
```

For scientific smoke runs, keep physical parameters and seed fixed. For reproducibility checks, use distinct field IDs and compare corresponding `Lens_Mass_*.bin` and `MicroLensCoorXY_*.bin` files directly.

## Git workflow

Use a short-lived branch for nontrivial work. Do not force-update `main`. Keep generated results out of source control.
