import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from simulation_config import (
    add_simulation_args,
    config_from_args,
)


parser = argparse.ArgumentParser(
    description="Inspect a minimum-image microlensing simulation."
)

add_simulation_args(parser)

args = parser.parse_args()
config = config_from_args(args)

suffix = config.suffix
micro_dir = config.micro_dir
result_dir = config.minimum_dir

metadata_file = micro_dir / f"AveMassAndNum_{suffix}"
length_file = result_dir / f"TimeLength_min_{suffix}"
area_file = result_dir / f"adptive_Area_min_{suffix}"
time_file = result_dir / f"adptive_Time_min_{suffix}"

for path in [
    metadata_file,
    length_file,
    area_file,
    time_file,
]:
    if not path.exists():
        raise FileNotFoundError(path)

# C++ writes three doubles:
#   average lens mass
#   total number of lenses
#   L2 grid length
metadata = np.fromfile(metadata_file, dtype=np.float64)

if metadata.size != 3:
    raise RuntimeError(
        f"Expected 3 metadata values, got {metadata.size}"
    )

average_mass, n_lenses, l2_length = metadata

# On x86-64 Linux, C++ long is an 8-byte signed integer.
n_samples = int(
    np.fromfile(length_file, dtype=np.int64, count=1)[0]
)

area = np.fromfile(area_file, dtype=np.float64)
time = np.fromfile(time_file, dtype=np.float64)

print(f"Average lens mass : {average_mass}")
print(f"Number of lenses  : {int(n_lenses)}")
print(f"L2 grid length     : {int(l2_length)}")
print(f"Expected samples   : {n_samples}")
print(f"Area samples       : {area.size}")
print(f"Time samples       : {time.size}")

if area.size != n_samples:
    raise RuntimeError(
        f"Area length mismatch: {area.size} != {n_samples}"
    )

if time.size != n_samples:
    raise RuntimeError(
        f"Time length mismatch: {time.size} != {n_samples}"
    )

if not np.all(np.isfinite(area)):
    raise RuntimeError("Area contains NaN/Inf values")

if not np.all(np.isfinite(time)):
    raise RuntimeError("Time contains NaN/Inf values")

print()
print(f"Time range : {time.min():.8g} -> {time.max():.8g}")
print(f"Area range : {area.min():.8g} -> {area.max():.8g}")
print(f"Nonzero area samples: {np.count_nonzero(area)}")

# This follows the beginning of TotalSgnFourier.py:
# F(t) = Area / delta_t
nonzero = np.flatnonzero(area > 0)

if nonzero.size == 0:
    raise RuntimeError("No positive area samples")

start = nonzero[0]

time = time[start:]
area = area[start:]

dt = np.diff(time)

if np.any(dt <= 0):
    raise RuntimeError("Time samples are not strictly increasing")

ft = area[:-1] / dt
ft_time = time[:-1]

print(f"dt = {dt[0]:.8g}")
print(f"F(t) samples = {ft.size}")

plt.figure(figsize=(9, 5))
plt.plot(ft_time, ft)
plt.xlabel("Time delay")
plt.ylabel("dA/dt")
plt.title("Microlensing time-domain response")
plt.grid(True)
plt.tight_layout()

output = Path("minimum_time_response.png")
plt.savefig(output, dpi=200)

print(f"Saved {output}")