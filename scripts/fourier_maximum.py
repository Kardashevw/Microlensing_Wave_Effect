import argparse

import matplotlib.pyplot as plt
import numpy as np

from image_type import ImageType, classify_image, macro_amplitude, macro_complex_factor
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
        description="Fourier analysis of a maximum-image simulation."
    )
    add_simulation_args(parser)
    parser.add_argument("--f-min", type=float, default=0.1)
    parser.add_argument("--f-max", type=float, default=2000.0)
    parser.add_argument("--df", type=float, default=1.0)
    args = parser.parse_args()
    config = config_from_args(args)

    if classify_image(config.kappa, config.gamma) is not ImageType.MAXIMUM:
        parser.error("The supplied kappa/gamma values do not describe a maximum image.")
    if args.f_min <= 0.0:
        parser.error("--f-min must be > 0")
    if args.f_max <= args.f_min:
        parser.error("--f-max must be greater than --f-min")
    if args.df <= 0.0:
        parser.error("--df must be > 0")

    suffix = config.suffix
    micro_dir = config.micro_dir
    result_dir = config.maximum_dir
    output_dir = config.frequency_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = np.fromfile(
        micro_dir / f"AveMassAndNum_{suffix}",
        dtype=np.float64,
    )
    if metadata.size != 3:
        raise RuntimeError(f"Expected 3 metadata values, got {metadata.size}")
    average_mass, n_lenses, l2_length = metadata

    n_samples = read_time_length(result_dir / f"TimeLength_max_{suffix}")
    area = np.fromfile(
        result_dir / f"adptive_Area_max_{suffix}",
        dtype=np.float64,
    )
    time = np.fromfile(
        result_dir / f"adptive_Time_max_{suffix}",
        dtype=np.float64,
    )
    if area.size != n_samples or time.size != n_samples:
        raise RuntimeError("Maximum binary file lengths are inconsistent")
    if n_samples < 3:
        raise RuntimeError("Not enough maximum time samples")

    mu = macro_amplitude(config.kappa, config.gamma)
    coeff = 4.0 * G * average_mass * M_SUN * (1.0 + config.lens_z) / C**3
    constant = 2.0 * np.pi * mu / coeff
    cw = coeff / (2.0 * np.pi)
    macro_factor = macro_complex_factor(ImageType.MAXIMUM, mu)

    dt_array = np.diff(time)
    if not np.allclose(dt_array, dt_array[0]):
        raise RuntimeError("Maximum time grid is not uniform")
    dt = dt_array[0]
    if dt <= 0.0:
        raise RuntimeError("Maximum time grid must increase")

    ft_raw = area[:-1] / dt_array
    time_raw = time[:-1]
    nonzero = np.flatnonzero(ft_raw > 0.0)
    if nonzero.size == 0:
        raise RuntimeError("No positive maximum-image area-rate samples found")

    # The C++ maximum branch pads the high-time side.  Keep data through the
    # final nonzero response, then reverse about that endpoint.  In tau =
    # T_max - T the smooth maximum has the same positive constant dA/dtau as a
    # smooth minimum, so the existing minimum residual treatment can be used
    # without changing the solver output or its sampling.
    end = nonzero[-1] + 1
    ft_reversed = ft_raw[:end][::-1].copy()
    time_kept = time_raw[:end]
    time_reversed = time_kept[-1] - time_kept[::-1]

    length = len(time_reversed)
    cut = 3 * length // 5
    time_reversed = time_reversed[:cut].copy()
    ft_reversed = ft_reversed[:cut].copy()
    if time_reversed.size < 2:
        raise RuntimeError("Maximum reversed three-fifths cut left too few samples")

    ft_reversed[1:] -= constant
    ft_reversed[0] -= constant / 2.0

    length = len(ft_reversed)
    window_length = 2 * length // 5
    if window_length > 1:
        window = np.hanning(window_length)
        tail_start = 4 * length // 5
        tail_length = length - tail_start
        if tail_length > 0:
            ft_reversed[tail_start:] *= window[-tail_length:]

    np.savetxt(
        output_dir / "maximum_reversed_time.csv",
        time_reversed,
        delimiter=",",
    )
    np.savetxt(
        output_dir / "maximum_reversed_ft_residual.csv",
        ft_reversed,
        delimiter=",",
    )

    plt.figure(figsize=(9, 5))
    plt.plot(time_reversed, ft_reversed)
    plt.axhline(0.0, linestyle="--")
    plt.xlabel(r"Reversed time from maximum $\tau$ [s]")
    plt.ylabel(r"$F(\tau)-F_{\rm smooth}(\tau)$")
    plt.title("Maximum microlensing reversed time-domain residual")
    plt.tight_layout()
    plt.savefig(output_dir / "maximum_time_residual.png", dpi=200)
    plt.close()

    freq = np.arange(args.f_min, args.f_max, args.df)
    if freq.size == 0:
        raise RuntimeError("Frequency grid is empty")
    omega = 2.0 * np.pi * freq
    f_real = np.empty(freq.size)
    f_imag = np.empty(freq.size)

    for i, w in enumerate(omega):
        f_real[i] = np.sum(ft_reversed * np.cos(w * time_reversed)) * dt
        f_imag[i] = np.sum(ft_reversed * np.sin(w * time_reversed)) * dt

    integral_reversed = f_real + 1j * f_imag
    minimum_form_factor = integral_reversed * omega / 1j * cw
    minimum_form_factor += mu

    # For T = T_max - tau and real F(tau), the original positive-frequency
    # response is the negative complex conjugate of the reversed positive
    # quadratic response when T_max is chosen as phase origin.  This restores
    # the maximum Morse phase: smooth F = -sqrt(|mu|).
    full_factor = -np.conjugate(minimum_form_factor)

    amplification = np.abs(full_factor)
    phase = np.angle(full_factor)
    macro_only = np.full_like(amplification, mu)
    normalized = amplification / mu

    np.savetxt(output_dir / "frequency.csv", freq, delimiter=",")
    np.savetxt(output_dir / "maximum_amplification.csv", amplification, delimiter=",")
    np.savetxt(output_dir / "macro_only_amplification.csv", macro_only, delimiter=",")
    np.savetxt(output_dir / "maximum_amplification_normalized.csv", normalized, delimiter=",")
    np.savetxt(output_dir / "maximum_phase.csv", phase, delimiter=",")
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
    plt.title("Maximum: full and macro-only amplification")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "maximum_amplification_comparison.png", dpi=200)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.semilogx(freq, phase)
    plt.axhline(np.angle(macro_factor), linestyle="--", label="Macro-only Morse phase")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Phase [rad]")
    plt.title("Maximum microlensing phase")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "maximum_phase.png", dpi=200)
    plt.close()

    print(f"Image type        : {ImageType.MAXIMUM.value}")
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
