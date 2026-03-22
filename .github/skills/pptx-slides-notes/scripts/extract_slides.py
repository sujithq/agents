#!/usr/bin/env python3
"""
extract_slides.py
-----------------
Render each slide of a .pptx file to a PNG image using LibreOffice as the
rendering backend. Falls back to a pure-python approach (python-pptx + Pillow)
when LibreOffice is not available.

Usage:
    python extract_slides.py --pptx <path/to/deck.pptx> --out <output/slides>
                             [--width 1920] [--height 1080]
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _libreoffice_export_pdf(pptx_path: Path, tmp_dir: Path) -> Path:
    """Export the PPTX to PDF via LibreOffice (headless)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found on PATH.")
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(tmp_dir),
        str(pptx_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed:\n{result.stderr}"
        )
    # LibreOffice names the output PDF after the input file
    pdf_path = tmp_dir / (pptx_path.stem + ".pdf")
    if not pdf_path.exists():
        # Locate any PDF produced
        pdfs = list(tmp_dir.glob("*.pdf"))
        if not pdfs:
            raise RuntimeError("LibreOffice did not produce a PDF.")
        pdf_path = pdfs[0]
    return pdf_path


def _render_pdf_to_pngs(pdf_path: Path, out_dir: Path, width: int, height: int) -> None:
    """Render each page of a PDF to a PNG using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF (pymupdf) is required for PDF rendering. "
            "Install it with: pip install pymupdf"
        ) from exc

    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Scale the page to the desired output resolution
        zoom_x = width / page.rect.width
        zoom_y = height / page.rect.height
        zoom = min(zoom_x, zoom_y)
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        slide_num = page_num + 1
        out_path = out_dir / f"slide-{slide_num:03d}.png"
        pix.save(str(out_path))
    doc.close()


def _render_pptx_fallback(pptx_path: Path, out_dir: Path, width: int, height: int) -> None:
    """
    Pure-python fallback using python-pptx + Pillow.
    Produces simple placeholder images with slide number text.
    This is used only when LibreOffice is unavailable.
    """
    try:
        from pptx import Presentation
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError(
            "python-pptx and Pillow are required. "
            "Install with: pip install python-pptx Pillow"
        ) from exc

    prs = Presentation(str(pptx_path))
    for idx, slide in enumerate(prs.slides):
        slide_num = idx + 1
        img = Image.new("RGB", (width, height), color=(30, 30, 80))
        draw = ImageDraw.Draw(img)
        # Draw a simple placeholder label
        label = f"Slide {slide_num}"
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except (IOError, OSError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = (height - text_h) // 2
        draw.text((x, y), label, fill=(255, 255, 255), font=font)
        out_path = out_dir / f"slide-{slide_num:03d}.png"
        img.save(str(out_path))


def extract_slides(pptx_path: Path, out_dir: Path, width: int = 1920, height: int = 1080) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prefer LibreOffice + PyMuPDF pipeline for accurate rendering
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pdf_path = _libreoffice_export_pdf(pptx_path, tmp_dir)
            _render_pdf_to_pngs(pdf_path, out_dir, width, height)
    else:
        print(
            "WARNING: LibreOffice not found. Using pure-python fallback "
            "(placeholder images). Install LibreOffice for accurate rendering.",
            file=sys.stderr,
        )
        _render_pptx_fallback(pptx_path, out_dir, width, height)

    pngs = sorted(out_dir.glob("slide-*.png"))
    print(f"Extracted {len(pngs)} slide(s) to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render PPTX slides to PNG images."
    )
    parser.add_argument("--pptx", required=True, help="Path to the .pptx file")
    parser.add_argument("--out", required=True, help="Output directory for PNGs")
    parser.add_argument("--width", type=int, default=1920, help="Output image width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Output image height (default: 1080)")
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.exists():
        print(f"ERROR: PPTX file not found: {pptx_path}", file=sys.stderr)
        sys.exit(1)

    extract_slides(pptx_path, Path(args.out), args.width, args.height)


if __name__ == "__main__":
    main()
