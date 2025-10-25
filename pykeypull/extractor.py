"""Core extraction logic for the Python port of KeyPull."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Iterable, List

from .keybox import KeyboxValidationError, validate as validate_keybox


class ExtractionError(RuntimeError):
    """Raised when a high-level extraction step fails."""


class Extractor:
    """Replicates the behaviour of the Go extractor in Python."""

    def __init__(self, output: str = "output", adb_path: str = "adb") -> None:
        self.adb_path = adb_path
        self.device: str | None = None
        self.output = Path.cwd() / output

    # ------------------------------------------------------------------
    # ADB helpers
    def adb_stat(self) -> None:
        """Detect a connected device and ensure the ADB server is running."""

        try:
            subprocess.run(
                [self.adb_path, "start-server"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise ExtractionError("ADB executable not found in PATH") from exc
        except subprocess.CalledProcessError as exc:
            raise ExtractionError(f"failed to start ADB server: {exc.stderr.decode().strip()}") from exc

        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ExtractionError(f"failed to fetch connected devices: {exc.stderr.strip()}") from exc

        connected: List[str] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                connected.append(parts[0])

        if not connected:
            raise ExtractionError("could not find any connected devices via ADB")

        self.device = connected[0]
        print(f"Connected to device: {self.device}")

    def obtain_root(self) -> None:
        """Attempt to elevate privileges on the connected device."""

        self._ensure_device()

        try:
            subprocess.run(
                [self.adb_path, "-s", self.device, "root"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as exc:
            print(f"ADB root failed: {exc.stderr.decode().strip()}")
            print("Attempting via SU")
            try:
                subprocess.run(
                    [self.adb_path, "-s", self.device, "shell", "su", "-c", "id"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError:
                raise ExtractionError(
                    "root access required but not available. Please root your device or enable root access in Developer Options."
                ) from None
            print("Obtained root via SU")
            return

        print("Obtained root via ADB")
        time.sleep(2)

    # ------------------------------------------------------------------
    # File operations
    def ensure_output_directory(self) -> None:
        self.output.mkdir(parents=True, exist_ok=True)

    def extract_from_location(self, location: str) -> None:
        """Extract data from a specific device path."""

        if location.endswith(".xml"):
            self._pull_keybox(location)
        elif location.endswith(".sqlite"):
            self._pull_keystore(location)
        else:
            self._pull_directory(location)

    # ------------------------------------------------------------------
    # Internal helpers
    def _ensure_device(self) -> None:
        if not self.device:
            raise ExtractionError("ADB device not initialised; call adb_stat() first")

    def _adb_pull(self, remote: str, local: Path) -> None:
        self._ensure_device()

        local.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [self.adb_path, "-s", self.device, "pull", remote, str(local)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as exc:
            raise ExtractionError(f"ADB pull failed for {remote}: {exc.stderr.decode().strip()}") from exc

    def _pull_keybox(self, remote: str) -> None:
        destination = self.output / Path(remote).name
        self._adb_pull(remote, destination)
        print(f"Keybox extracted: {destination}")
        try:
            validate_keybox(destination)
        except KeyboxValidationError as exc:
            raise ExtractionError(f"downloaded keybox failed validation: {exc}") from exc

    def _pull_keystore(self, remote: str) -> None:
        destination = self.output / Path(remote).name
        self._adb_pull(remote, destination)
        print(f"Keystore extracted: {destination}")

    def _pull_directory(self, remote_dir: str) -> None:
        self._ensure_device()

        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device, "shell", "find", remote_dir, "-type", "f"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ExtractionError(
                f"failed to list directory contents for {remote_dir}: {exc.stderr.strip()}"
            ) from exc

        files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not files:
            raise ExtractionError(f"no files found in {remote_dir}")

        for remote_file in files:
            safe_name = remote_file.strip("/").replace("/", "_")
            destination = self.output / safe_name
            try:
                self._adb_pull(remote_file, destination)
            except ExtractionError as exc:
                print(f"Failed to pull {remote_file}: {exc}")
                continue

            if "keybox" in remote_file or remote_file.endswith(".xml"):
                try:
                    validate_keybox(destination)
                except KeyboxValidationError:
                    # Ignore invalid XML files pulled during directory traversal
                    continue

    # ------------------------------------------------------------------
    # Convenience methods
    def extract_all(self, locations: Iterable[str]) -> List[str]:
        """Extract from a series of locations, returning the successful ones."""

        successes: List[str] = []
        for location in locations:
            print(f"Attempting extraction: {location}")
            try:
                self.extract_from_location(location)
            except ExtractionError as exc:
                print(f"  Failed: {exc}")
                continue
            successes.append(location)
            print(f"  Success: {location}")
        return successes
