"""Command line interface for the Python KeyPull clone."""

from __future__ import annotations

import argparse
from typing import Sequence

from .extractor import ExtractionError, Extractor
from .locations import DEVICE_LOCATIONS


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for the KeyPull CLI."""

    parser = argparse.ArgumentParser(
        description="Extract Android keystore and keybox files over ADB",
    )
    parser.add_argument(
        "locations",
        nargs="*",
        help="Custom device paths to extract (defaults to the known KeyPull locations)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Directory where extracted files will be written (default: %(default)s)",
    )
    parser.add_argument(
        "--adb",
        default="adb",
        help="Path to the adb executable (default: %(default)s)",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Execute the extraction workflow and return the exit status."""

    parser = build_parser()
    args = parser.parse_args(argv)

    extractor = Extractor(output=args.output, adb_path=args.adb)

    print("Instantiating extraction process...")
    try:
        extractor.adb_stat()
        extractor.obtain_root()
        extractor.ensure_output_directory()
    except ExtractionError as exc:
        parser.error(str(exc))

    locations = list(args.locations) if args.locations else list(DEVICE_LOCATIONS)
    successes = extractor.extract_all(locations)

    if not successes:
        print("Keybox extraction failed.")
        return 1

    print(f"Extracted keybox data from {len(successes)} location(s):")
    for location in successes:
        print(f"  - {location}")
    print(f"\nExtraction saved to: {extractor.output}")
    return 0


def main() -> None:
    """Entrypoint used by ``python -m`` and console scripts."""

    raise SystemExit(run())
