import argparse

import matplotlib.pyplot as plt
import numpy as np

from simulation_config import (
    add_simulation_args,
    config_from_args,
)

parser = argparse.ArgumentParser(
    description="Fourier analysis of a minimum-image simulation."
)

add_simulation_args(parser)
parser.add_argument("--f-min", type=float, default=0.1)
parser.add_argument("--f-max", type=float, default=2000.0)
parser.add_argument("--df", type=float, default=1.0)

args = parser.parse_args()
config = config_from_args(args)

KAPPA = config.kappa
GAMMA = config.gamma
KAPPA_STAR = config.kappa_star
LENS_Z = config.lens_z

M_SUN = 1.9884099e30
G = 6.6743e-11
C = 2.9979246e8

suffix = config.suffix
micro_dir = config.micro_dir
result_dir = config.minimum_dir
output_dir = config.frequency_dir
output_dir.mkdir(parents=True, exist_ok=True)

metadata = np.fromfile(
    micro_dir / f"AveMassAndNum_{suffix}",
    dtype=np.float64,
)
if metadata.size != 3:
    raise RuntimeError(f"Expected 3 metadata values, got {metadata.size}")

average_mass, n_lenses, l2_length = metadata

n_samples = int(
    np.fromfile(
        result_dir / f"TimeLength_min_{suffix}",
        dtype=np.int64,
        count=1,
    )[0]
)
area = np.fromfile(
    result_dir / f"adptive_Area_min_{suffix}",
    dtype=np.float64,
)
time = np.fromfile(
    result_dir / f"adptive_Time_min_{suffix}",
    dtype=np.float64,
)
if area.size != n_samples or time.size != n_samples:
    raise RuntimeError("Binary file lengths are inconsistent")

mu = np.sqrt(abs(1.0 / ((1.0 - KAPPA) ** 2 - GAMMA**2)))
coeff = 4.0 * G * average_mass * M_SUN * (1.0 + LENS_Z) / C**3
constant = 2.0 * np.pi * mu / coeff
cw = coeff / (2.0 * np.pi)

print(f"Average mass : {average_mass:.10f} Msun")
print(f"Macro |F|    : {mu:.10f}")
print(f"coeff        : {coeff:.10e} s")
print(f"constant     : {constant:.10e}")
print(f"cw           : {cw:.10e}")

nonzero = np.flatnonzero(area > 0)
if nonzero.size == 0:
    raise RuntimeError("No positive area values found")

start = nonzero[0]
area = area[start:]
time = time[start:]

dt_array = np.diff(time)
if not np.allclose(dt_array, dt_array[0]):
    raise RuntimeError("Time grid is not uniform")

dt = dt_array[0]
ft = area[:-1] / dt_array
t = time[:-1]
t = t - t[0]

print(f"Raw F(t) samples : {ft.size}")
print(f"dt               : {dt:.10e} s")

length = len(t)
cut = 3 * length // 5
t = t[:cut].copy()
ft = ft[:cut].copy()

duration = t[-1] - t[0]
if duration <= 0:
    raise RuntimeError("Invalid time-domain duration")

characteristic_df = 1.0 / duration
nyquist_frequency = 1.0 / (2.0 * dt)

print(f"Samples after cut : {len(t)}")
print(f"Time duration     : {duration:.10e} s")
print(f"Characteristic df : {characteristic_df:.3f} Hz")
print(f"Nyquist frequency : {nyquist_frequency:.3f} Hz")

ft[1:] -= constant
ft[0] -= constant / 2.0

length = len(ft)
window_length = 2 * length // 5
if window_length > 1:
    window = np.hanning(window_length)
    tail_start = 4 * length // 5
    tail_length = length - tail_start
    if tail_length > 0:
        ft[tail_start:] *= window[-tail_length:]

np.savetxt(output_dir / "minimum_time.csv", t, delimiter=",")
np.savetxt(output_dir / "minimum_ft.csv", ft, delimiter=",")

plt.figure(figsize=(9, 5))
plt.plot(t, ft)
plt.axhline(0, linestyle="--")
plt.xlabel("Time [s]")
plt.ylabel(r"$F(t)-F_{\rm smooth}(t)$")
plt.title("Microlensing time-domain residual")
plt.tight_layout()
plt.savefig(output_dir / "minimum_time_residual.png", dpi=200)
plt.close()

freq = np.arange(args.f_min, args.f_max, args.df)
omega = 2.0 * np.pi * freq
f_real = np.empty(freq.size)
f_imag = np.empty(freq.size)

for i, w in enumerate(omega):
    f_real[i] = np.sum(ft * np.cos(w * t)) * dt
    f_imag[i] = np.sum(ft * np.sin(w * t)) * dt

integral = f_real + 1j * f_imag
Ff = integral * omega / 1j * cw
Ff += constant * cw

amplification = np.abs(Ff)
phase = np.angle(Ff)
macro_amplification = np.full_like(amplification, mu)
normalized_amplification = amplification / mu

print()
print(f"Frequency bins : {freq.size}")
print(f"Frequency range: {freq[0]} -> {freq[-1]} Hz")
print(f"|F| range      : {amplification.min():.6g} -> {amplification.max():.6g}")
print(f"Phase range    : {phase.min():.6g} -> {phase.max():.6g} rad")
print()
print("Low-frequency |F| / macro |F|:", normalized_amplification[0])

np.savetxt(output_dir / "frequency.csv", freq, delimiter=",")
np.savetxt(output_dir / "minimum_amplification.csv", amplification, delimiter=",")
np.savetxt(
    output_dir / "macro_only_amplification.csv",
    macro_amplification,
    delimiter=",",
)
np.savetxt(
    output_dir / "minimum_amplification_normalized.csv",
    normalized_amplification,
    delimiter=",",
)
np.savetxt(output_dir / "minimum_phase.csv", phase, delimiter=",")
np.savetxt(
    output_dir / "amplification_comparison.csv",
    np.column_stack(
        (
            freq,
            amplification,
            macro_amplification,
            normalized_amplification,
            phase,
        )
    ),
    delimiter=",",
    header=(
        "frequency_hz,full_amplification,macro_only_amplification,"
        "full_over_macro,phase_rad"
    ),
    comments="",
)

plt.figure(figsize=(9, 5))
plt.semilogx(freq, amplification, label="Macro + microlensing")
plt.semilogx(freq, macro_amplification, linestyle="--", label="Macro only")
plt.xlabel("Frequency [Hz]")
plt.ylabel(r"Amplification factor $|F(f)|$")
plt.title("Full and macro-only amplification")
plt.legend()
plt.tight_layout()
plt.savefig(output_dir / "minimum_amplification_comparison.png", dpi=200)
plt.close()

plt.figure(figsize=(9, 5))
plt.semilogx(freq, phase)
plt.axhline(0.0, linestyle="--")
plt.xlabel("Frequency [Hz]")
plt.ylabel("Phase [rad]")
plt.title("Microlensing phase")
plt.tight_layout()
plt.savefig(output_dir / "minimum_phase.png", dpi=200)
plt.close()

print()
print(f"Results written to {output_dir}/")
print(
    "Comparison plot:",
    output_dir / "minimum_amplification_comparison.png",
)
