from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_pipeline import intermediate_directories, remove_intermediate_directories
from simulation_config import SimulationConfig


class PipelineCleanupTests(unittest.TestCase):
    def config(self) -> SimulationConfig:
        return SimulationConfig(
            kappa=0.45,
            gamma=0.45,
            kappa_star=0.03,
            lens_z=0.5,
            source_z=1.0,
            field_id=42,
        )

    def test_frequency_outputs_live_under_dedicated_output_root(self):
        self.assertEqual(
            self.config().frequency_dir,
            Path("outputs") / "Freq_Time_Domain_Result_42",
        )

    def test_intermediate_cleanup_removes_only_current_field_directories(self):
        config = self.config()

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            expected = intermediate_directories(repo_root, config)
            for path in expected:
                path.mkdir()
                (path / "intermediate.bin").write_bytes(b"binary")

            final_output = repo_root / config.frequency_dir
            final_output.mkdir(parents=True)
            (final_output / "keep.csv").write_bytes(b"keep")

            unrelated = repo_root / "MicroField_99"
            unrelated.mkdir()
            (unrelated / "keep.bin").write_bytes(b"keep")

            removed = remove_intermediate_directories(repo_root, config)

            self.assertEqual(removed, expected)
            self.assertTrue(all(not path.exists() for path in expected))
            self.assertTrue((final_output / "keep.csv").is_file())
            self.assertTrue((unrelated / "keep.bin").is_file())

    def test_intermediate_cleanup_refuses_symlinks(self):
        config = self.config()

        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            target = repo_root / "target"
            target.mkdir()
            linked = repo_root / config.micro_dir

            try:
                linked.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are not supported on this platform")

            with self.assertRaises(RuntimeError):
                remove_intermediate_directories(repo_root, config)

            self.assertTrue(target.is_dir())


if __name__ == "__main__":
    unittest.main()
