from pathlib import Path
import shutil


PLOT_NAMES = {
    "minimum": "minimum_amplification_comparison.png",
    "saddle": "saddle_amplification_comparison.png",
    "maximum": "maximum_amplification_comparison.png",
}


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
