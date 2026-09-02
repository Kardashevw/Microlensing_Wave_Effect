import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from output_contract import clean_output_directory, documented_output_names


class FinalOutputCleanupTests(unittest.TestCase):
    def metadata(self) -> dict:
        return {
            "image_type": "minimum",
            "inputs": {
                "kappa": 0.45,
                "gamma": 0.45,
                "kappa_star": 0.03,
                "lens_z": 0.5,
                "source_z": 1.0,
                "threads": 8,
                "precision_factor": 10,
                "field_id": 42,
                "seed": 12345,
                "f_min": 0.1,
                "f_max": 2000.0,
                "df": 1.0,
                "skip_build": True,
            },
            "derived": {"lambda_r": 1.0, "lambda_t": 0.1},
        }

    def test_cleanup_leaves_exact_documented_products(self):
        metadata = self.metadata()
        expected = documented_output_names(metadata)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            parameters_path = output_dir / "run_parameters.json"
            parameters_path.write_text(json.dumps(metadata), encoding="utf-8")
            (output_dir / "amplification_comparison.csv").write_text(
                "frequency_hz,full_amplification,macro_only_amplification\n",
                encoding="utf-8",
            )
            (output_dir / "minimum_amplification_comparison.png").write_bytes(b"png")
            (output_dir / "stellar_field_realization.png").write_bytes(b"png")

            (output_dir / "frequency.csv").write_text("legacy", encoding="utf-8")
            (output_dir / "minimum_phase.png").write_bytes(b"legacy")
            legacy_dir = output_dir / "legacy_diagnostics"
            legacy_dir.mkdir()
            (legacy_dir / "diagnostic.txt").write_text("legacy", encoding="utf-8")

            clean_output_directory(output_dir, metadata, parameters_path)

            self.assertEqual(
                {path.name for path in output_dir.iterdir()},
                expected,
            )

    def test_cleanup_refuses_to_delete_when_required_product_is_missing(self):
        metadata = self.metadata()

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            parameters_path = output_dir / "run_parameters.json"
            parameters_path.write_text(json.dumps(metadata), encoding="utf-8")
            legacy_path = output_dir / "frequency.csv"
            legacy_path.write_text("keep until validation passes", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                clean_output_directory(output_dir, metadata, parameters_path)

            self.assertTrue(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
