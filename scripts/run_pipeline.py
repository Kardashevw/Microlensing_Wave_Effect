import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from image_type import (
    ImageType,
    classify_image,
    jacobian_eigenvalues,
    saddle_orientation_supported,
)
from simulation_config import add_simulation_args, config_from_args


REPO_ROOT = Path(__file__).resolve().parent.parent


ANALYSIS_SCRIPTS = {
    ImageType.MINIMUM: "fourier_minimum.py",
    ImageType.SADDLE: "fourier_saddle.py",
    ImageType.MAXIMUM: "fourier_maximum.py",
}

PLOT_NAMES = {
    ImageType.MINIMUM: "minimum_amplification_comparison.png",
    ImageType.SADDLE: "saddle_amplification_comparison.png",
    ImageType.MAXIMUM: "maximum_amplification_comparison.png",
}


def run_command(command: list[str]) -> None:
    print()
    print("$", shlex.join(str(part) for part in command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def intermediate_directories(repo_root: Path, config) -> list[Path]:
    return [
        repo_root / config.micro_dir,
        repo_root / config.minimum_dir,
        repo_root / config.saddle_dir,
        repo_root / config.maximum_dir,
    ]


def remove_intermediate_directories(repo_root: Path, config) -> list[Path]:
    """Remove only this run's solver-generated intermediate directories."""
    candidates = [path for path in intermediate_directories(repo_root, config) if path.exists()]

    for path in candidates:
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(
                "Refusing to remove an intermediate path that is not a real directory: "
                f"{path}"
            )

    for path in candidates:
        shutil.rmtree(path)

    return candidates


def write_run_parameters(
    path: Path,
    *,
    args: argparse.Namespace,
    config,
    image_type: ImageType,
    radial: float,
    tangential: float,
) -> None:
    metadata = {
        "image_type": image_type.value,
        "inputs": {
            "kappa": config.kappa,
            "gamma": config.gamma,
            "kappa_star": config.kappa_star,
            "lens_z": config.lens_z,
            "source_z": config.source_z,
            "threads": args.threads,
            "precision_factor": args.precision_factor,
            "field_id": config.field_id,
            "seed": args.seed,
            "f_min": args.f_min,
            "f_max": args.f_max,
            "df": args.df,
            "skip_build": args.skip_build,
            "remove_intermediate": args.remove_intermediate,
        },
        "derived": {
            "lambda_r": radial,
            "lambda_t": tangential,
        },
    }
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build and run one microlensing simulation, automatically select "
            "the minimum/saddle/maximum Fourier treatment from kappa and "
            "gamma, and produce the full and macro-only amplification comparison."
        )
    )
    add_simulation_args(parser)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--precision-factor", type=int, default=10)
    parser.add_argument("--seed", type=int, default=12345)
    parser.add_argument("--f-min", type=float, default=0.1)
    parser.add_argument("--f-max", type=float, default=2000.0)
    parser.add_argument("--df", type=float, default=1.0)
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Reuse an existing build/microlensing executable.",
    )
    parser.add_argument(
        "--remove-intermediate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Remove MicroField_<field-id> and ResultMinimum/Saddle/Maximum_<field-id> "
            "after all final products are safely rendered (default: enabled). "
            "Use --no-remove-intermediate to keep them."
        ),
    )

    args = parser.parse_args()
    config = config_from_args(args)

    if args.threads <= 0:
        parser.error("--threads must be > 0")
    if args.precision_factor <= 0:
        parser.error("--precision-factor must be > 0")
    if args.seed < 0 or args.seed > 2**32 - 1:
        parser.error("--seed must fit in an unsigned 32-bit integer")
    if args.f_min <= 0:
        parser.error("--f-min must be > 0 for a logarithmic frequency plot")
    if args.f_max <= args.f_min:
        parser.error("--f-max must be greater than --f-min")
    if args.df <= 0:
        parser.error("--df must be > 0")

    try:
        image_type = classify_image(config.kappa, config.gamma)
    except ValueError as exc:
        parser.error(str(exc))

    radial, tangential = jacobian_eigenvalues(config.kappa, config.gamma)
    if image_type is ImageType.SADDLE and not saddle_orientation_supported(
        config.kappa, config.gamma
    ):
        parser.error(
            "This is a saddle image, but the current C++ saddle branch only "
            "supports 1-kappa+gamma > 0 and 1-kappa-gamma < 0. Supporting "
            "the opposite orientation would require a numerical C++ change."
        )

    print("Detected macro image type:", image_type.value)
    print(f"  1-kappa+gamma = {radial:.10g}")
    print(f"  1-kappa-gamma = {tangential:.10g}")

    if not args.skip_build:
        run_command(["cmake", "-S", ".", "-B", "build"])
        run_command(["cmake", "--build", "build", "--parallel"])

    executable = REPO_ROOT / "build" / "microlensing"
    if not executable.is_file():
        parser.error(
            "build/microlensing does not exist. Run without --skip-build first."
        )

    simulation_command = [
        str(executable),
        "--kappa",
        str(config.kappa),
        "--gamma",
        str(config.gamma),
        "--kappa-star",
        str(config.kappa_star),
        "--lens-z",
        str(config.lens_z),
        "--source-z",
        str(config.source_z),
        "--threads",
        str(args.threads),
        "--precision-factor",
        str(args.precision_factor),
        "--field-id",
        str(config.field_id),
        "--seed",
        str(args.seed),
    ]
    run_command(simulation_command)

    output_dir = REPO_ROOT / config.frequency_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    parameters_path = output_dir / "run_parameters.json"
    write_run_parameters(
        parameters_path,
        args=args,
        config=config,
        image_type=image_type,
        radial=radial,
        tangential=tangential,
    )

    analysis_script = REPO_ROOT / "scripts" / ANALYSIS_SCRIPTS[image_type]
    fourier_command = [
        sys.executable,
        str(analysis_script),
        "--kappa",
        str(config.kappa),
        "--gamma",
        str(config.gamma),
        "--kappa-star",
        str(config.kappa_star),
        "--lens-z",
        str(config.lens_z),
        "--source-z",
        str(config.source_z),
        "--field-id",
        str(config.field_id),
        "--f-min",
        str(args.f_min),
        "--f-max",
        str(args.f_max),
        "--df",
        str(args.df),
    ]
    run_command(fourier_command)

    render_command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "render_outputs.py"),
        "--parameters",
        str(parameters_path),
    ]
    run_command(render_command)

    removed_intermediate: list[Path] = []
    if args.remove_intermediate:
        removed_intermediate = remove_intermediate_directories(REPO_ROOT, config)

    print()
    print("Pipeline complete.")
    print("Image type:", image_type.value)
    print("Final output directory:", output_dir)
    print("Run parameters:", parameters_path)
    print(
        "Amplification comparison plot:",
        output_dir / PLOT_NAMES[image_type],
    )
    print(
        "Amplification comparison data:",
        output_dir / "amplification_comparison.csv",
    )
    print(
        "Stellar field realization plot:",
        output_dir / "stellar_field_realization.png",
    )
    if args.remove_intermediate:
        print("Removed intermediate directories:")
        if removed_intermediate:
            for path in removed_intermediate:
                print(" ", path)
        else:
            print("  none found")
    else:
        print("Intermediate directories kept (--no-remove-intermediate).")


if __name__ == "__main__":
    main()
