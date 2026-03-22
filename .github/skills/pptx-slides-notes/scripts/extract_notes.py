#!/usr/bin/env python3
"""
Extract speaker notes from a PPTX into per-slide text files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pptx import Presentation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract speaker notes into per-slide .txt files."
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
        help="Directory where per-slide notes will be saved.",
    )
    return parser.parse_args()


def extract_notes(prs: Presentation, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for idx, slide in enumerate(prs.slides, start=1):
        text = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            lines = []
            for paragraph in slide.notes_slide.notes_text_frame.paragraphs:
                runs = [run.text for run in paragraph.runs if run.text]
                paragraph_text = "".join(runs).strip()
                if paragraph_text:
                    lines.append(paragraph_text)
            text = "\n".join(lines).strip()
        target = destination / f"slide-{idx:03d}.txt"
        target.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    pptx_path = args.pptx.resolve()
    if not pptx_path.exists():
        raise SystemExit(f"PPTX not found: {pptx_path}")
    prs = Presentation(str(pptx_path))
    extract_notes(prs, args.out)


if __name__ == "__main__":
    main()
