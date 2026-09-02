from dataclasses import dataclass
from pathlib import Path
import argparse


OUTPUT_ROOT = Path("outputs")


@dataclass(frozen=True)
class SimulationConfig:
    kappa: float
    gamma: float
    kappa_star: float
    lens_z: float
    source_z: float
    field_id: int

    @property
    def suffix(self) -> str:
        return (
            f"{self.kappa:.2f}_"
            f"{self.gamma:.2f}_"
            f"{self.kappa_star:.2f}_"
            f"{self.lens_z:.2f}_"
            f"{self.source_z:.2f}.bin"
        )

    @property
    def micro_dir(self) -> Path:
        return Path(f"MicroField_{self.field_id}")

    @property
    def minimum_dir(self) -> Path:
        return Path(f"ResultMinimum_{self.field_id}")

    @property
    def saddle_dir(self) -> Path:
        return Path(f"ResultSaddle_{self.field_id}")

    @property
    def maximum_dir(self) -> Path:
        return Path(f"ResultMaximum_{self.field_id}")

    @property
    def frequency_dir(self) -> Path:
        return OUTPUT_ROOT / f"Freq_Time_Domain_Result_{self.field_id}"


def add_simulation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--kappa", type=float, default=0.45)
    parser.add_argument("--gamma", type=float, default=0.45)
    parser.add_argument("--kappa-star", type=float, default=0.03)
    parser.add_argument("--lens-z", type=float, default=0.5)
    parser.add_argument("--source-z", type=float, default=1.0)
    parser.add_argument("--field-id", type=int, default=15)


def config_from_args(args: argparse.Namespace) -> SimulationConfig:
    return SimulationConfig(
        kappa=args.kappa,
        gamma=args.gamma,
        kappa_star=args.kappa_star,
        lens_z=args.lens_z,
        source_z=args.source_z,
        field_id=args.field_id,
    )