# Microlensing Wave Effect

Research software for wave-optics diffraction through microlensing fields, including the component-decomposition method and adaptive hierarchical algorithm described in the associated papers.

This repository keeps the numerical C++ implementation separate from entry points, analysis helpers, legacy research scripts, and generated outputs. Workflow changes should not alter the C++ scientific formulas, numerical algorithms, random streams, binary formats, or solver control flow unless that is explicitly intended.

## Repository layout

```text
app/                    supported C++ command-line entry point
include/                C++ headers and bundled spline header
src/                    maintained C++ numerical implementation
legacy/cpp/             original C++ implementations kept for reference
legacy/python/          original research-analysis scripts
scripts/                maintained Python workflow/analysis helpers
tests/                  lightweight workflow/convention tests
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

Use `scripts/run_pipeline.py`. Enter the simulation and frequency parameters once; the runner then:

1. classifies the macro image from `kappa` and `gamma`,
2. configures and incrementally builds the existing C++ solver,
3. runs the microlensing simulation,
4. reads the matching minimum/saddle/maximum binary output,
5. applies the appropriate Fourier treatment,
6. plots the full macro+microlensing amplification and macro-only amplification on the same frequency axis.

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

After the first build, add `--skip-build` to reuse `build/microlensing`.

### Automatic image classification

Define the two macro Jacobian eigenvalues

```text
lambda_r = 1 - kappa + gamma
lambda_t = 1 - kappa - gamma
```

The one-shot runner selects:

| Image | Condition | Analysis helper | Smooth positive-frequency macro factor |
| --- | --- | --- | --- |
| Minimum | `lambda_r > 0`, `lambda_t > 0` | `scripts/fourier_minimum.py` | `+sqrt(|mu|)` |
| Saddle | `lambda_r > 0`, `lambda_t < 0` | `scripts/fourier_saddle.py` | `-i sqrt(|mu|)` |
| Maximum | `lambda_r < 0`, `lambda_t < 0` | `scripts/fourier_maximum.py` | `-sqrt(|mu|)` |

Here the code's amplitude convention is

```text
sqrt(|mu|) = sqrt(abs(1 / ((1-kappa)^2 - gamma^2)))
```

so the macro-only **magnitude** plotted for all three image types is the same frequency-independent `sqrt(|mu|)`. The complex signs/phases in the table are the Morse phases and matter for the phase output, not for the macro-only magnitude curve.

Critical cases with either eigenvalue exactly zero are rejected. The current C++ saddle branch internally assumes `lambda_r > 0` and `lambda_t < 0`; the opposite saddle orientation is detected but rejected rather than silently reinterpreted, because supporting it would require changing the C++ numerical branch.

## Branch-specific Fourier treatment

### Minimum

The maintained minimum treatment is unchanged. It uses the existing leading nonzero response, time-origin shift, three-fifths cut, smooth constant subtraction, one-sided Hann taper, explicit frequency loop, and restoration of the smooth `+sqrt(|mu|)` term.

### Saddle

The saddle helper ports the active saddle equations from `legacy/python/TotalSgnFourier.py` into a standalone workflow:

1. read `ResultSaddle_<field-id>/` and `X1020New_*`,
2. construct `dA/dt`,
3. avoid an exact `t=0` sample because the analytic smooth saddle contains `log(|t|)`,
4. retain the middle three-fifths of the time curve,
5. subtract the finite-field analytic saddle response used by the original code,
6. explicitly Fourier-transform the residual,
7. restore the smooth saddle term `-i sqrt(|mu|)`.

This keeps the original active saddle subtraction and transform convention rather than replacing it with an FFT or a new approximation.

### Maximum

The C++ solver already writes a distinct `ResultMaximum_<field-id>/` dataset, but the legacy Python code did not contain a standalone maximum Fourier routine. The maintained extension uses time-reversal symmetry without modifying the solver:

1. form `dA/dt` from the maximum output,
2. retain data through the final nonzero maximum response,
3. define reversed time `tau = T_max - T`,
4. in `tau`, apply the same smooth constant subtraction, three-fifths cut, taper, and explicit transform convention as the minimum branch,
5. map the reversed complex factor back with

```text
F_max(f) = -conjugate(F_reversed(f))
```

when `T_max` is chosen as the phase origin.

The conjugation comes from `T -> T_max - tau`; the minus sign restores the maximum-image Morse phase. A time-origin change only multiplies the complex factor by a unit phase and therefore does not alter the plotted amplification magnitude.

This maximum implementation has lightweight convention tests, but unlike the minimum branch it does not yet have a historical golden scientific smoke dataset in this repository. Before using maximum results for production science, run a representative maximum case and check its low-frequency macro limit and convergence with `precision-factor`.

## Outputs

The final comparison data is always

```text
Freq_Time_Domain_Result_<field-id>/amplification_comparison.csv
```

with columns

```text
frequency_hz
full_amplification
macro_only_amplification
full_over_macro
phase_rad
```

The final comparison plot is branch-specific:

```text
minimum_amplification_comparison.png
saddle_amplification_comparison.png
maximum_amplification_comparison.png
```

Each plot shows

```text
Macro + microlensing: |F(f)|
Macro only:            sqrt(abs(1 / ((1-kappa)^2 - gamma^2)))
```

against frequency.

## Manual lower-level workflow

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

Run a branch-specific Fourier helper on existing output:

```bash
uv run python scripts/fourier_minimum.py  ...
uv run python scripts/fourier_saddle.py   ...
uv run python scripts/fourier_maximum.py  ...
```

The helpers accept the same physical parameters, `field-id`, `--f-min`, `--f-max`, and `--df` arguments as the one-shot workflow.

Shared physical parameters and filename conventions live in `scripts/simulation_config.py`. `scripts/inspect_minimum.py` remains the maintained minimum-image binary inspection helper.

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
