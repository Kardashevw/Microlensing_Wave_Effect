# AGENTS.md

Guidance for automated contributors working in this research repository.

## Non-negotiable scientific constraint

Treat the numerical implementation as research code, not application code. Do not change scientific formulas, constants, iteration order, tolerances, random-stream semantics, binary layouts, or floating-point expressions unless the task explicitly asks for a scientific/numerical change.

Prefer structural, isolated, testable edits. Avoid broad formatting passes over the large numerical source files.

For Markdown documentation, write mathematical expressions with `$...$` for inline math and `$$...$$` for display math. Do not put equations in backticks or fenced `text` blocks when they are intended to render as mathematics.

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
  -> final rendering/output curation
  -> outputs/Freq_Time_Domain_Result_<field-id>/
  -> remove solver intermediate directories by default
```

The one-shot runner owns parameter forwarding. A physical/numerical parameter entered by the user must be passed unchanged to the C++ and Python stages that consume it.

Final one-shot products live under `outputs/`. During calculation the C++ solver still uses root-level `MicroField_<field-id>/` and `ResultMinimum/Saddle/Maximum_<field-id>/` directories. The one-shot pipeline removes those intermediate directories after successful final rendering by default. Use `--no-remove-intermediate` when a task needs the raw binary products for debugging, reproducibility checks, convergence studies, or lower-level analysis.

`legacy/` is reference material and is not part of the supported build.

## Image classification and paper conventions

Use the macro Jacobian eigenvalues

$$
\lambda_r = 1 - \kappa + \gamma,
\qquad
\lambda_t = 1 - \kappa - \gamma.
$$

- minimum / Type I: $\lambda_r>0$ and $\lambda_t>0$
- saddle / Type II: the eigenvalues have opposite signs
- maximum / Type III: $\lambda_r<0$ and $\lambda_t<0$
- critical: either eigenvalue is exactly zero; reject

Shan et al. (2022) derives Type II using $\lambda_r>0$ and $\lambda_t<0$ without loss of generality. The current C++ saddle branch implements that orientation explicitly. Do not silently rotate/relabel the opposite saddle orientation because that would require changing the C++ numerical branch.

For positive frequency, the Component Decomposition smooth macro factors are

$$
\begin{aligned}
\text{minimum:}\quad &+\sqrt{|\mu|} &&\text{(Type I, Eq. 19)},\\
\text{saddle:}\quad &-i\sqrt{|\mu|} &&\text{(Type II, Eq. 32 for }\omega>0\text{)},\\
\text{maximum:}\quad &-\sqrt{|\mu|} &&\text{(Type III, Eq. 36)}.
\end{aligned}
$$

with

$$
\sqrt{|\mu|}
=
\sqrt{\left|\frac{1}{(1-\kappa)^2-\gamma^2}\right|}.
$$

The macro-only magnitude plotted in every branch is therefore the same $\sqrt{|\mu|}$.

## Branch analysis rules

- `scripts/fourier_minimum.py`: preserve the existing maintained Type-I transform, smooth subtraction/reconstruction, three-fifths cut, and residual taper. The taper is an implementation detail; the ideal paper CD derivation relies on the residual approaching zero at the statistical boundary.
- `scripts/fourier_saddle.py`: preserve the Type-II finite-field analytic expressions corresponding to Eqs. (22), (24), and (32): subtract the finite smooth hyperbolic response and restore $-i\sqrt{|\mu|}$ on the positive-frequency grid.
- `scripts/fourier_maximum.py`: implement Type III directly as described in Sec. 2.5 / Eq. (36): choose the maximum delay as $t=0$, work on the negative-time side, subtract the constant smooth response there, transform the residual, and restore $-\sqrt{|\mu|}$. Mirror the maintained Type-I practical truncation/taper on the opposite time edge rather than introducing a separate time-reversal formulation.

The maximum branch still needs a representative scientific smoke/convergence test before being treated as a golden validated analysis path.

The 2024 TAAH paper changes how the time-domain area distribution is computed, but its final frequency-domain step explicitly calls the earlier Component Decomposition algorithm. Do not replace the CD post-processing with a different Fourier prescription merely because the C++ time-domain solver is newer.

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

- `scripts/run_pipeline.py`: preferred one-shot build/simulate/analyze/cleanup entry point.
- `scripts/output_contract.py`: exact four-file final-output whitelist.
- `scripts/render_outputs.py`: final parameter-rich rendering and frequency-output curation.
- `scripts/image_type.py`: image classification and macro Morse-phase conventions.
- `scripts/fourier_minimum.py`: minimum / Type-I Fourier helper.
- `scripts/fourier_saddle.py`: saddle / Type-II Fourier helper.
- `scripts/fourier_maximum.py`: maximum / Type-III Fourier helper.
- `app/microlensing.cpp`: supported C++ CLI entry point.
- `src/Micro_field_adaptive.cpp`: main adaptive algorithm; avoid unrelated edits.
- `src/GetPsi_micro_field.cpp`: potential, adaptive-grid, and time-delay calculations; avoid unrelated edits.
- `src/ReproducibleRandom.cpp`: deterministic sampling used by the maintained workflow.
- `include/`: headers required by the maintained C++ build.
- `SampleMethod/Remnant_MF.csv`: runtime remnant mass-function data expected by the current sampler.
- `scripts/simulation_config.py`: shared Python physical parameters, output root, and filename convention.
- `scripts/inspect_minimum.py`: minimum-image binary validation/time-domain helper.
- `outputs/`: git-ignored final one-shot products.

## Reproducibility rules

Same physical parameters plus the same seed should reproduce sampled lens masses and coordinates. Keep mass and coordinate RNG streams independent. `field-id` is only an output-directory identifier.

When raw masses/coordinates are needed for comparison, pass `--no-remove-intermediate`; default one-shot cleanup deletes those solver directories only after final rendering succeeds.

Generated binary output names encode physical parameters to two decimal places. Do not silently change this convention.

## Validation after workflow changes

At minimum:

```bash
cmake -S . -B build
cmake --build build -j
./build/microlensing --help
python -m py_compile scripts/run_pipeline.py scripts/output_contract.py scripts/render_outputs.py scripts/image_type.py scripts/simulation_config.py scripts/fourier_minimum.py scripts/fourier_saddle.py scripts/fourier_maximum.py
python -m unittest discover -s tests
uv run python scripts/run_pipeline.py --help
```

For scientific smoke runs, keep physical parameters and seed fixed. For reproducibility checks involving raw binaries, use distinct field IDs, pass `--no-remove-intermediate`, and compare corresponding `Lens_Mass_*.bin` and `MicroLensCoorXY_*.bin` files directly.

## Git workflow

Use a short-lived branch for nontrivial work. Do not force-update `main`. Keep generated results out of source control.
