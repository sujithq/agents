#!/usr/bin/env python3
"""
Convert a PPTX into per-slide PNGs using LibreOffice (to PDF) + pdftoppm.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure_tool_exists(name: str) -> None:
    if shutil.which(name) is None:
        sys.stderr.write(f"Required tool not found on PATH: {name}\n")
        sys.exit(1)


def run_command(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"Command failed ({exc.returncode}): {' '.join(cmd)}\n")
        sys.exit(exc.returncode)


def convert_to_pdf(pptx_path: Path, tmp_dir: Path) -> Path:
    run_command(
        [
            "libreoffice",
            "--headless",
            "--nologo",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmp_dir),
            str(pptx_path),
        ]
    )
    pdf_candidates = sorted(tmp_dir.glob("*.pdf"))
    if not pdf_candidates:
        sys.stderr.write("No PDF produced from PPTX conversion.\n")
        sys.exit(1)
    return pdf_candidates[0]


def pdf_to_pngs(pdf_path: Path, tmp_dir: Path, dpi: int) -> list[Path]:
    prefix = tmp_dir / "slide"
    run_command(
        [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            str(pdf_path),
            str(prefix),
        ]
    )
    return sorted(tmp_dir.glob("slide-*.png"))


def renumber_and_move(pngs: list[Path], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for idx, png in enumerate(pngs, start=1):
        target = destination / f"slide-{idx:03d}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        png.replace(target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract per-slide PNGs from a PPTX using LibreOffice + pdftoppm."
    )
    parser.add_argument(
        "--pptx",
        required=True,
        type=Path,
        help="Path to the PowerPoint file.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Directory to write slide PNGs into.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Resolution for rendered PNGs (default: 150).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_tool_exists("libreoffice")
    ensure_tool_exists("pdftoppm")

    pptx_path = args.pptx.resolve()
    if not pptx_path.exists():
        sys.stderr.write(f"PPTX not found: {pptx_path}\n")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        pdf_path = convert_to_pdf(pptx_path, tmp_dir)
        pngs = pdf_to_pngs(pdf_path, tmp_dir, args.dpi)
        if not pngs:
            sys.stderr.write("No PNGs produced from PDF conversion.\n")
            sys.exit(1)
        renumber_and_move(pngs, args.out)


if __name__ == "__main__":
    main()
