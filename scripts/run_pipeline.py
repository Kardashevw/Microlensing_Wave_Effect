import argparse
from pathlib import Path
import shlex
import subprocess
import sys

from simulation_config import add_simulation_args, config_from_args


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_command(command: list[str]) -> None:
    print()
    print("$", shlex.join(str(part) for part in command))
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build, run one minimum-image microlensing simulation, and produce "
            "the full and macro-only frequency-domain amplification comparison."
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

    radial_eigenvalue = 1.0 - config.kappa + config.gamma
    tangential_eigenvalue = 1.0 - config.kappa - config.gamma
    if radial_eigenvalue <= 0 or tangential_eigenvalue <= 0:
        parser.error(
            "The maintained one-shot Fourier workflow currently supports the "
            "minimum-image branch only: both 1-kappa+gamma and "
            "1-kappa-gamma must be > 0."
        )

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

    fourier_command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "fourier_minimum.py"),
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

    output_dir = REPO_ROOT / config.frequency_dir
    print()
    print("Pipeline complete.")
    print(
        "Amplification comparison plot:",
        output_dir / "minimum_amplification_comparison.png",
    )
    print(
        "Amplification comparison data:",
        output_dir / "amplification_comparison.csv",
    )


if __name__ == "__main__":
    main()
