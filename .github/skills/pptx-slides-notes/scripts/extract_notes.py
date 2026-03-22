#!/usr/bin/env python3
"""
extract_notes.py
----------------
Extract speaker notes from each slide of a .pptx file and write them to
individual plain-text files.

Usage:
    python extract_notes.py --pptx <path/to/deck.pptx> --out <output/notes>
"""

import argparse
import sys
from pathlib import Path


def extract_notes(pptx_path: Path, out_dir: Path) -> None:
    try:
        from pptx import Presentation
    except ImportError as exc:
        raise RuntimeError(
            "python-pptx is required. Install with: pip install python-pptx"
        ) from exc

    out_dir.mkdir(parents=True, exist_ok=True)
    prs = Presentation(str(pptx_path))

    for idx, slide in enumerate(prs.slides):
        slide_num = idx + 1
        notes_text = ""
        if slide.has_notes_slide:
            tf = slide.notes_slide.notes_text_frame
            notes_text = tf.text.strip() if tf else ""

        out_path = out_dir / f"slide-{slide_num:03d}.txt"
        out_path.write_text(notes_text, encoding="utf-8")

    txt_files = sorted(out_dir.glob("slide-*.txt"))
    print(f"Extracted notes for {len(txt_files)} slide(s) to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract speaker notes from a PPTX file."
    )
    parser.add_argument("--pptx", required=True, help="Path to the .pptx file")
    parser.add_argument("--out", required=True, help="Output directory for note TXT files")
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.exists():
        print(f"ERROR: PPTX file not found: {pptx_path}", file=sys.stderr)
        sys.exit(1)

    extract_notes(pptx_path, Path(args.out))


if __name__ == "__main__":
    main()
