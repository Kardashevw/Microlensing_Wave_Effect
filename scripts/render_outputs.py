import argparse
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

from simulation_config import SimulationConfig


REPO_ROOT = Path(__file__).resolve().parent.parent

PLOT_NAMES = {
    "minimum": "minimum_amplification_comparison.png",
    "saddle": "saddle_amplification_comparison.png",
    "maximum": "maximum_amplification_comparison.png",
}


def format_parameter_block(metadata: dict) -> str:
    inputs = metadata["inputs"]
    return (
        rf"$\kappa={inputs['kappa']:.6g}$, "
        rf"$\gamma={inputs['gamma']:.6g}$, "
        rf"$\kappa_*={inputs['kappa_star']:.6g}$, "
        rf"$z_L={inputs['lens_z']:.6g}$, "
        rf"$z_S={inputs['source_z']:.6g}$"
        "\n"
        f"seed={inputs['seed']}, field-id={inputs['field_id']}, "
        f"precision-factor={inputs['precision_factor']}, threads={inputs['threads']}"
        "\n"
        f"frequency={inputs['f_min']:.6g}–{inputs['f_max']:.6g} Hz, "
        f"df={inputs['df']:.6g} Hz, image={metadata['image_type']}"
    )


def config_from_metadata(metadata: dict) -> SimulationConfig:
    inputs = metadata["inputs"]
    return SimulationConfig(
        kappa=float(inputs["kappa"]),
        gamma=float(inputs["gamma"]),
        kappa_star=float(inputs["kappa_star"]),
        lens_z=float(inputs["lens_z"]),
        source_z=float(inputs["source_z"]),
        field_id=int(inputs["field_id"]),
    )


def documented_output_names(metadata: dict) -> set[str]:
    return {
        "run_parameters.json",
        "amplification_comparison.csv",
        PLOT_NAMES[metadata["image_type"]],
        "stellar_field_realization.png",
    }


def clean_output_directory(
    output_dir: Path,
    metadata: dict,
    parameters_path: Path,
) -> None:
    """Leave only the documented one-shot pipeline products in output_dir."""
    expected = documented_output_names(metadata)
    expected_parameters = output_dir / "run_parameters.json"

    if parameters_path.resolve() != expected_parameters.resolve():
        raise RuntimeError(
            "The final renderer expects run_parameters.json inside the frequency "
            f"output directory: {expected_parameters}"
        )

    missing = sorted(
        name for name in expected if not (output_dir / name).is_file()
    )
    if missing:
        raise RuntimeError(
            "Cannot finalize the frequency output directory because required "
            "products are missing: " + ", ".join(missing)
        )

    for path in output_dir.iterdir():
        if path.name in expected:
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()

    remaining = {path.name for path in output_dir.iterdir()}
    if remaining != expected:
        raise RuntimeError(
            "Final frequency output directory does not match the documented "
            f"product set. Expected {sorted(expected)}, got {sorted(remaining)}"
        )


def render_amplification_plot(metadata: dict, output_dir: Path) -> Path:
    comparison_path = output_dir / "amplification_comparison.csv"
    data = np.genfromtxt(comparison_path, delimiter=",", names=True)
    data = np.atleast_1d(data)

    required = {
        "frequency_hz",
        "full_amplification",
        "macro_only_amplification",
    }
    if data.dtype.names is None or not required.issubset(data.dtype.names):
        raise RuntimeError(
            f"{comparison_path} is missing one or more required columns: "
            + ", ".join(sorted(required))
        )

    freq = data["frequency_hz"]
    full = data["full_amplification"]
    macro = data["macro_only_amplification"]

    fig, ax = plt.subplots(figsize=(9, 6.2))
    ax.semilogx(freq, full, label="Macro + microlensing")
    ax.semilogx(freq, macro, linestyle="--", label="Macro only")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel(r"Amplification factor $|F(f)|$")
    ax.set_title(
        f"{metadata['image_type'].capitalize()}: full and macro-only amplification"
    )
    ax.legend()
    ax.grid(True, which="both", alpha=0.2)

    fig.text(
        0.5,
        0.015,
        format_parameter_block(metadata),
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.0, 0.14, 1.0, 1.0))

    plot_name = PLOT_NAMES[metadata["image_type"]]
    output_path = output_dir / plot_name
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def render_stellar_field(metadata: dict, output_dir: Path) -> Path:
    config = config_from_metadata(metadata)
    micro_dir = REPO_ROOT / config.micro_dir

    mass_path = micro_dir / f"Lens_Mass_{config.suffix}"
    coordinate_path = micro_dir / f"MicroLensCoorXY_{config.suffix}"

    masses = np.fromfile(mass_path, dtype=np.float64)
    coordinates_raw = np.fromfile(coordinate_path, dtype=np.float64)

    if masses.size == 0:
        raise RuntimeError(f"No microlens masses found in {mass_path}")
    if coordinates_raw.size != 2 * masses.size:
        raise RuntimeError(
            "Microlens mass/coordinate file lengths are inconsistent: "
            f"{masses.size} masses and {coordinates_raw.size} coordinate values"
        )
    if not np.all(np.isfinite(masses)) or np.any(masses <= 0.0):
        raise RuntimeError("Microlens masses must be finite and positive")
    if not np.all(np.isfinite(coordinates_raw)):
        raise RuntimeError("Microlens coordinates must be finite")

    coordinates = coordinates_raw.reshape((-1, 2))
    x1 = coordinates[:, 0]
    x2 = coordinates[:, 1]

    marker_size = max(0.2, min(8.0, 12000.0 / masses.size))
    mass_min = float(masses.min())
    mass_max = float(masses.max())
    norm = LogNorm(vmin=mass_min, vmax=mass_max) if mass_max > mass_min else None

    fig, ax = plt.subplots(figsize=(8.2, 7.8))
    points = ax.scatter(
        x1,
        x2,
        c=masses,
        s=marker_size,
        linewidths=0.0,
        alpha=0.8,
        norm=norm,
        rasterized=True,
    )
    colorbar = fig.colorbar(points, ax=ax, pad=0.02)
    colorbar.set_label(r"Microlens mass [$M_\odot$]")

    ax.set_xlabel(r"$x_1$")
    ax.set_ylabel(r"$x_2$")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"Stellar/remnant microlens field realization (N={masses.size})")
    ax.grid(True, alpha=0.15)

    fig.text(
        0.5,
        0.012,
        format_parameter_block(metadata),
        ha="center",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.0, 0.14, 1.0, 1.0))

    output_path = output_dir / "stellar_field_realization.png"
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render parameter-annotated final plots from completed microlensing "
            "pipeline outputs without modifying any numerical results."
        )
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        required=True,
        help="Path to run_parameters.json written by scripts/run_pipeline.py.",
    )
    args = parser.parse_args()

    with args.parameters.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    config = config_from_metadata(metadata)
    output_dir = REPO_ROOT / config.frequency_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    amplification_plot = render_amplification_plot(metadata, output_dir)
    field_plot = render_stellar_field(metadata, output_dir)
    clean_output_directory(output_dir, metadata, args.parameters)

    print("Parameter-annotated amplification plot:", amplification_plot)
    print("Stellar field realization plot:", field_plot)
    print("Final frequency output directory contains only documented products.")


if __name__ == "__main__":
    main()
