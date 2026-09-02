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
outputs/                generated final one-shot results (git-ignored)
CMakeLists.txt           supported C++ build
pyproject.toml           Python environment/dependencies
shell.nix                Nix development environment
```

Generated simulation directories and `outputs/` are intentionally excluded from version control.

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
6. plots the full macro+microlensing amplification and macro-only amplification on the same frequency axis,
7. keeps only the four documented final products under `outputs/`,
8. removes the solver intermediate directories by default after all final products are safely rendered.

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

Intermediate cleanup is enabled by default. Use `--no-remove-intermediate` when you need to retain `MicroField_<field-id>/` and the three `Result*_<field-id>/` directories for debugging, reproducibility checks, or lower-level analysis. The explicit Boolean pair is `--remove-intermediate` / `--no-remove-intermediate`.

### Automatic image classification

Define the two macro Jacobian eigenvalues

```text
lambda_r = 1 - kappa + gamma
lambda_t = 1 - kappa - gamma
```

The one-shot runner selects:

| Image | Condition | Analysis helper | Smooth positive-frequency macro factor |
| --- | --- | --- | --- |
| Minimum (Type I) | `lambda_r > 0`, `lambda_t > 0` | `scripts/fourier_minimum.py` | `+sqrt(|mu|)` |
| Saddle (Type II) | `lambda_r > 0`, `lambda_t < 0` | `scripts/fourier_saddle.py` | `-i sqrt(|mu|)` |
| Maximum (Type III) | `lambda_r < 0`, `lambda_t < 0` | `scripts/fourier_maximum.py` | `-sqrt(|mu|)` |

Here the code's amplitude convention is

```text
sqrt(|mu|) = sqrt(abs(1 / ((1-kappa)^2 - gamma^2)))
```

so the macro-only **magnitude** plotted for all three image types is the same frequency-independent `sqrt(|mu|)`. The complex signs/phases are the Morse phases and matter for the phase output, not for the macro-only magnitude curve.

The Type-II derivation in Shan et al. chooses `lambda_r > 0`, `lambda_t < 0` without loss of generality. The current C++ saddle branch implements that orientation explicitly, so the opposite orientation is detected but rejected rather than silently rotating/relabeling the numerical problem.

## Branch-specific Fourier treatment

The frequency-domain helpers implement the Component Decomposition (CD) structure from Shan et al. (2022): compute the finite numerical time-domain response, subtract the analytic smooth component, transform the residual, then restore the analytic smooth macro contribution.

### Minimum / Type I

The maintained minimum treatment is unchanged. Its smooth time-domain component is constant for positive time, and the restored positive-frequency macro term is `+sqrt(|mu|)`, matching Eq. (19) of Shan et al. (2022).

The current maintained implementation also uses an empirical three-fifths cut and a one-sided Hann taper on the **residual** before the explicit frequency integration. Those are practical implementation details inherited from the repository code; the paper's ideal CD derivation relies on the residual approaching zero at the statistical boundary and does not require apodizing the full time-domain signal.

### Saddle / Type II

The saddle helper ports the active Type-II finite-boundary equations into a standalone workflow:

1. read `ResultSaddle_<field-id>/` and `X1020New_*`,
2. construct `dA/dt`,
3. avoid an exact `t=0` sample because the analytic smooth saddle contains `log(|t|)`,
4. retain the middle three-fifths of the numerical time curve,
5. subtract the finite-field analytic smooth response corresponding to the two hyperbolic regions,
6. explicitly Fourier-transform the residual,
7. restore `-i sqrt(|mu|)` for the positive-frequency grid.

This is the positive-frequency form of Eq. (32), where the paper gives `-i Sgn(omega) sqrt(mu)`.

### Maximum / Type III

Type III is implemented directly from Sec. 2.5 and Eq. (36) of Shan et al. (2022), rather than through an additional time-reversal identity:

1. read the existing `ResultMaximum_<field-id>/` output,
2. identify the final nonzero maximum response and choose that maximum delay as `t=0`,
3. retain the corresponding final three-fifths of the time series, mirroring the maintained Type-I practical truncation,
4. subtract the constant smooth Type-III time-domain component on `t < 0` (half weight at the `t=0` endpoint),
5. apply the mirrored one-sided residual taper used by the maintained Type-I helper,
6. explicitly Fourier-transform the residual in the original negative-time coordinate,
7. restore the analytic Type-III macro term `-sqrt(|mu|)`.

This follows the paper's statement that Type III uses the same CD method as Type I, with the infinite-time side reversed and the smooth frequency-domain contribution changing from `+sqrt(mu)` to `-sqrt(mu)`.

The maximum branch should still receive a representative scientific smoke/convergence test before being treated as a golden validated path, especially because the repository previously lacked a maintained standalone Type-III post-processing helper.

## Outputs

A completed one-shot run leaves exactly four final files in a dedicated output tree:

```text
outputs/
└── Freq_Time_Domain_Result_<field-id>/
    ├── run_parameters.json
    ├── amplification_comparison.csv
    ├── <image-type>_amplification_comparison.png
    └── stellar_field_realization.png
```

`amplification_comparison.csv` contains

```text
frequency_hz
full_amplification
macro_only_amplification
full_over_macro
phase_rad
```

The comparison plot shows

```text
Macro + microlensing: |F(f)|
Macro only:            sqrt(abs(1 / ((1-kappa)^2 - gamma^2)))
```

against frequency. `run_parameters.json` records the user-facing run inputs, including whether intermediate cleanup was enabled.

See `docs/output_products.md` for the final-output and cleanup contract.

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

The helpers accept the same physical parameters, `field-id`, `--f-min`, `--f-max`, and `--df` arguments as the one-shot workflow. Their frequency-domain products are written under `outputs/Freq_Time_Domain_Result_<field-id>/` through the shared simulation configuration. Manual lower-level execution does not invoke the one-shot intermediate-directory cleanup.

Shared physical parameters and filename conventions live in `scripts/simulation_config.py`. `scripts/inspect_minimum.py` remains the maintained minimum-image binary inspection helper.

## Output directories and cleanup

`field-id` identifies output directories and is not a physical parameter or random seed. During a run the numerical solver creates root-level intermediate directories such as:

```text
MicroField_10/
ResultMinimum_10/
ResultSaddle_10/
ResultMaximum_10/
```

The one-shot pipeline needs those directories through Fourier analysis and stellar-field rendering. After successful final rendering, it removes all four by default, including the binary files inside them. Pass `--no-remove-intermediate` to keep them.

Final deliverables are retained separately under:

```text
outputs/Freq_Time_Domain_Result_10/
```

## Reproducibility

For numerical comparisons that require the generated lens masses/coordinates:

1. Keep physical parameters fixed.
2. Keep `--seed` fixed.
3. Use distinct `--field-id` values to avoid overwrites.
4. Add `--no-remove-intermediate` so the generated binary files remain available.
5. Compare corresponding `Lens_Mass_*.bin` and `MicroLensCoorXY_*.bin` files directly.

The maintained RNG implementation keeps mass and coordinate streams independent. Workflow changes do not modify that implementation.

Generated binary filenames encode physical parameters to two decimal places. Avoid sweeps that differ only beyond two decimal places unless the naming scheme is deliberately redesigned.

## Binary-format assumptions

The current helper scripts target the Linux/x86-64 development workflow. Existing native binary layouts are preserved; the workflow does not version or reinterpret them.

## Legacy code

Files under `legacy/` are retained as research/reference material and are not part of the supported build. Some original Python scripts contain external dataset paths and should be reviewed before use.

## Citation

If you find this work useful, please cite the associated microlensing wave-effect papers:

- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field: A new algorithm and supplementary study*, Sci. China Phys. Mech. Astron. 66, 239511 (2023), arXiv:2208.13566.
- X. Shan et al., *Wave effect of gravitational waves intersected with a microlens field II: an adaptive hierarchical tree algorithm and population study* (2024), arXiv:2409.06747.
