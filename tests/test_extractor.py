"""Unit tests covering the Extractor workflow."""

import subprocess
import unittest
from unittest.mock import call, patch

# Accessing protected members is acceptable in unit tests.
# pylint: disable=protected-access

from pykeypull.extractor import Extractor, ExtractionError


class ExtractorTests(unittest.TestCase):
    """Behavioural tests for the :class:`Extractor` class."""

    def setUp(self) -> None:
        """Create a fresh extractor instance for each test."""

        # Ensure output directory uses a temporary unique path for tests
        self.extractor = Extractor(output="test-output")
        self.addCleanup(self._cleanup_output)

    def _cleanup_output(self) -> None:
        """Remove any output directory created during a test run."""

        if self.extractor.output.exists():
            for child in self.extractor.output.iterdir():
                if child.is_file():
                    child.unlink()
            self.extractor.output.rmdir()

    def test_adb_stat_detects_device(self) -> None:
        """ADB device discovery should record the first connected device."""

        with patch("pykeypull.extractor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b""),
                subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout="List of devices attached\nABC123\tdevice\n",
                    stderr="",
                ),
            ]

            self.extractor.adb_stat()

        self.assertEqual(self.extractor.device, "ABC123")
        mock_run.assert_has_calls(
            [
                call(
                    [self.extractor.adb_path, "start-server"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ),
                call(
                    [self.extractor.adb_path, "devices"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                ),
            ]
        )

    def test_obtain_root_via_adb(self) -> None:
        """Rooting via ADB should succeed when the command runs cleanly."""

        self.extractor.device = "ABC123"
        with patch("pykeypull.extractor.subprocess.run") as mock_run, patch(
            "pykeypull.extractor.time.sleep",
        ) as mock_sleep:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=b"", stderr=b""
            )

            self.extractor.obtain_root()

        mock_run.assert_called_once_with(
            [self.extractor.adb_path, "-s", "ABC123", "root"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        mock_sleep.assert_called_once_with(2)

    def test_obtain_root_falls_back_to_su(self) -> None:
        """If root fails, the extractor should attempt an SU fallback."""

        self.extractor.device = "ABC123"
        with patch("pykeypull.extractor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CalledProcessError(returncode=1, cmd="adb", stderr=b"fail"),
                subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b""),
            ]

            self.extractor.obtain_root()

        self.assertEqual(mock_run.call_count, 2)
        fallback_call = mock_run.mock_calls[1]
        self.assertEqual(
            fallback_call,
            call(
                [self.extractor.adb_path, "-s", "ABC123", "shell", "su", "-c", "id"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ),
        )

    def test_obtain_root_raises_when_su_fails(self) -> None:
        """The extractor should raise an error if SU access is unavailable."""

        self.extractor.device = "ABC123"
        with patch("pykeypull.extractor.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.CalledProcessError(returncode=1, cmd="adb", stderr=b"fail"),
                subprocess.CalledProcessError(returncode=1, cmd="adb", stderr=b"fail"),
            ]

            with self.assertRaises(ExtractionError):
                self.extractor.obtain_root()

    def test_pull_directory_pulls_each_file(self) -> None:
        """Directory extraction should download each discovered file."""

        self.extractor.device = "ABC123"
        directory_listing = "/data/file1\n/data/keybox.xml\n"

        with (
            patch("pykeypull.extractor.subprocess.run") as mock_run,
            patch.object(self.extractor, "_adb_pull") as mock_pull,
            patch("pykeypull.extractor.validate_keybox") as mock_validate,
        ):
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout=directory_listing, stderr=""
            )

            self.extractor._pull_directory("/data")

        expected_destinations = [
            self.extractor.output / "data_file1",
            self.extractor.output / "data_keybox.xml",
        ]
        mock_pull.assert_has_calls(
            [
                call("/data/file1", expected_destinations[0]),
                call("/data/keybox.xml", expected_destinations[1]),
            ],
            any_order=False,
        )
        mock_validate.assert_called_once_with(expected_destinations[1])

    def test_extract_all_collects_successful_locations(self) -> None:
        """Only successful extraction locations should be returned."""

        locations = ["one", "two", "three"]

        with patch.object(self.extractor, "extract_from_location") as mock_extract:
            mock_extract.side_effect = [None, ExtractionError("boom"), None]

            successes = self.extractor.extract_all(locations)

        self.assertEqual(successes, ["one", "three"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
