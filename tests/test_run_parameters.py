import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from image_type import ImageType
from run_pipeline import write_run_parameters
from simulation_config import SimulationConfig


class RunParameterOutputTests(unittest.TestCase):
    def test_all_user_inputs_are_written(self):
        config = SimulationConfig(
            kappa=0.45,
            gamma=0.45,
            kappa_star=0.03,
            lens_z=0.5,
            source_z=1.0,
            field_id=42,
        )
        args = argparse.Namespace(
            threads=12,
            precision_factor=20,
            seed=98765,
            f_min=0.2,
            f_max=1500.0,
            df=0.5,
            skip_build=True,
            remove_intermediate=True,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run_parameters.json"
            write_run_parameters(
                path,
                args=args,
                config=config,
                image_type=ImageType.MINIMUM,
                radial=1.0,
                tangential=0.1,
            )
            metadata = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(metadata["image_type"], "minimum")
        self.assertEqual(
            metadata["inputs"],
            {
                "kappa": 0.45,
                "gamma": 0.45,
                "kappa_star": 0.03,
                "lens_z": 0.5,
                "source_z": 1.0,
                "threads": 12,
                "precision_factor": 20,
                "field_id": 42,
                "seed": 98765,
                "f_min": 0.2,
                "f_max": 1500.0,
                "df": 0.5,
                "skip_build": True,
                "remove_intermediate": True,
            },
        )
        self.assertEqual(
            metadata["derived"],
            {"lambda_r": 1.0, "lambda_t": 0.1},
        )


if __name__ == "__main__":
    unittest.main()
