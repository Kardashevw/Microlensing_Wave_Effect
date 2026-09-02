import argparse

import matplotlib.pyplot as plt
import numpy as np

from image_type import (
    ImageType,
    classify_image,
    macro_amplitude,
    macro_complex_factor,
    saddle_orientation_supported,
)
from simulation_config import add_simulation_args, config_from_args


M_SUN = 1.9884099e30
G = 6.6743e-11
C = 2.9979246e8


def read_time_length(path) -> int:
    values = np.fromfile(path, dtype=np.int64, count=1)
    if values.size != 1:
        raise RuntimeError(f"Expected one time-length value in {path}")
    return int(values[0])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fourier analysis of a saddle-image simulation."
    )
    add_simulation_args(parser)
    parser.add_argument("--f-min", type=float, default=0.1)
    parser.add_argument("--f-max", type=float, default=2000.0)
    parser.add_argument("--df", type=float, default=1.0)
    args = parser.parse_args()
    config = config_from_args(args)

    if classify_image(config.kappa, config.gamma) is not ImageType.SADDLE:
        parser.error("The supplied kappa/gamma values do not describe a saddle image.")
    if not saddle_orientation_supported(config.kappa, config.gamma):
        parser.error(
            "The current C++ saddle solver assumes 1-kappa+gamma > 0 and "
            "1-kappa-gamma < 0. The opposite saddle orientation is not "
            "supported without changing the C++ numerical branch."
        )
    if args.f_min <= 0.0:
        parser.error("--f-min must be > 0")
    if args.f_max <= args.f_min:
        parser.error("--f-max must be greater than --f-min")
    if args.df <= 0.0:
        parser.error("--df must be > 0")

    suffix = config.suffix
    micro_dir = config.micro_dir
    result_dir = config.saddle_dir
    output_dir = config.frequency_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = np.fromfile(
        micro_dir / f"AveMassAndNum_{suffix}",
        dtype=np.float64,
    )
    if metadata.size != 3:
        raise RuntimeError(f"Expected 3 metadata values, got {metadata.size}")
    average_mass, n_lenses, l2_length = metadata

    n_samples = read_time_length(result_dir / f"TimeLength_sad_{suffix}")
    area = np.fromfile(
        result_dir / f"adptive_Area_sad_{suffix}",
        dtype=np.float64,
    )
    time = np.fromfile(
        result_dir / f"adptive_Time_sad_{suffix}",
        dtype=np.float64,
    )
    x1020 = np.fromfile(
        result_dir / f"X1020New_{suffix}",
        dtype=np.float64,
    )

    if area.size != n_samples or time.size != n_samples:
        raise RuntimeError("Saddle binary file lengths are inconsistent")
    if x1020.size != 2:
        raise RuntimeError(f"Expected two saddle boundary values, got {x1020.size}")
    if n_samples < 3:
        raise RuntimeError("Not enough saddle time samples")

    mu = macro_amplitude(config.kappa, config.gamma)
    coeff = 4.0 * G * average_mass * M_SUN * (1.0 + config.lens_z) / C**3
    cw = coeff / (2.0 * np.pi)
    macro_factor = macro_complex_factor(ImageType.SADDLE, mu)

    dt_array = np.diff(time)
    if not np.allclose(dt_array, dt_array[0]):
        raise RuntimeError("Saddle time grid is not uniform")
    dt = dt_array[0]
    if dt <= 0.0:
        raise RuntimeError("Saddle time grid must increase")

    ft_raw = area[:-1] / dt_array
    time_raw = time[:-1]

    # Legacy saddle theory contains log(|t|), so exactly t=0 is shifted to
    # interval midpoints exactly as in the original reusable Saddle() helper.
    if np.any(time_raw == 0.0):
        time_raw = (time_raw[1:] + time_raw[:-1]) / 2.0
        ft_raw = ft_raw[:-1]

    length = len(time_raw)
    lower = length // 5
    upper = length * 4 // 5
    time_new = time_raw[lower:upper].copy()
    ft_raw = ft_raw[lower:upper].copy()
    if time_new.size < 2:
        raise RuntimeError("Saddle middle-three-fifths cut left too few samples")

    x10, x20 = x1020
    radial = 1.0 - config.kappa + config.gamma
    tangential_abs = config.kappa + config.gamma - 1.0
    axis_a = np.sqrt(1.0 / coeff / radial)
    axis_b = np.sqrt(1.0 / coeff / tangential_abs)

    negative = time_new < 0.0
    nonnegative = ~negative
    theory_negative = -2.0 * mu / coeff * (
        np.log(2.0)
        + 2.0 * np.log(axis_a)
        + np.log(np.abs(time_new[negative]))
        - 2.0
        * np.log(
            x10
            + np.sqrt(
                2.0 * axis_a**2 * np.abs(time_new[negative]) + x10**2
            )
        )
    )
    theory_nonnegative = -2.0 * mu / coeff * (
        np.log(2.0)
        + 2.0 * np.log(axis_b)
        + np.log(np.abs(time_new[nonnegative]))
        - 2.0
        * np.log(
            x20
            + np.sqrt(
                2.0 * axis_b**2 * np.abs(time_new[nonnegative]) + x20**2
            )
        )
    )
    ft_theory = np.concatenate((theory_negative, theory_nonnegative))
    if ft_theory.size != ft_raw.size:
        raise RuntimeError("Saddle analytic subtraction length mismatch")

    ft_residual = ft_raw - ft_theory

    np.savetxt(output_dir / "saddle_time.csv", time_new, delimiter=",")
    np.savetxt(output_dir / "saddle_ft_theory.csv", ft_theory, delimiter=",")
    np.savetxt(output_dir / "saddle_ft_residual.csv", ft_residual, delimiter=",")

    plt.figure(figsize=(9, 5))
    plt.plot(time_new, ft_residual)
    plt.axhline(0.0, linestyle="--")
    plt.xlabel("Time [s]")
    plt.ylabel(r"$F(t)-F_{\rm smooth}(t)$")
    plt.title("Saddle microlensing time-domain residual")
    plt.tight_layout()
    plt.savefig(output_dir / "saddle_time_residual.png", dpi=200)
    plt.close()

    freq = np.arange(args.f_min, args.f_max, args.df)
    if freq.size == 0:
        raise RuntimeError("Frequency grid is empty")
    omega = 2.0 * np.pi * freq
    f_real = np.empty(freq.size)
    f_imag = np.empty(freq.size)

    for i, w in enumerate(omega):
        f_real[i] = np.sum(ft_residual * np.cos(w * time_new)) * dt
        f_imag[i] = np.sum(ft_residual * np.sin(w * time_new)) * dt

    integral = f_real + 1j * f_imag
    full_factor = integral * omega / 1j * cw
    full_factor += macro_factor

    amplification = np.abs(full_factor)
    phase = np.angle(full_factor)
    macro_only = np.full_like(amplification, mu)
    normalized = amplification / mu

    np.savetxt(output_dir / "frequency.csv", freq, delimiter=",")
    np.savetxt(output_dir / "saddle_amplification.csv", amplification, delimiter=",")
    np.savetxt(output_dir / "macro_only_amplification.csv", macro_only, delimiter=",")
    np.savetxt(output_dir / "saddle_amplification_normalized.csv", normalized, delimiter=",")
    np.savetxt(output_dir / "saddle_phase.csv", phase, delimiter=",")
    np.savetxt(
        output_dir / "amplification_comparison.csv",
        np.column_stack((freq, amplification, macro_only, normalized, phase)),
        delimiter=",",
        header=(
            "frequency_hz,full_amplification,macro_only_amplification,"
            "full_over_macro,phase_rad"
        ),
        comments="",
    )

    plt.figure(figsize=(9, 5))
    plt.semilogx(freq, amplification, label="Macro + microlensing")
    plt.semilogx(freq, macro_only, linestyle="--", label="Macro only")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel(r"Amplification factor $|F(f)|$")
    plt.title("Saddle: full and macro-only amplification")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "saddle_amplification_comparison.png", dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.semilogx(freq, phase)
    plt.axhline(-np.pi / 2.0, linestyle="--", label="Macro-only Morse phase")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Phase [rad]")
    plt.title("Saddle microlensing phase")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "saddle_phase.png", dpi=200)
    plt.close()

    print(f"Image type        : {ImageType.SADDLE.value}")
    print(f"Average mass      : {average_mass:.10f} Msun")
    print(f"Lens count        : {n_lenses:.0f}")
    print(f"L2 grid length    : {l2_length:.0f}")
    print(f"Macro |F|         : {mu:.10f}")
    print(f"Macro complex F   : {macro_factor}")
    print(f"Frequency bins    : {freq.size}")
    print(f"|F| range         : {amplification.min():.6g} -> {amplification.max():.6g}")
    print("Low-f |F|/macro  :", normalized[0])
    print(f"Results written to {output_dir}/")


if __name__ == "__main__":
    main()
