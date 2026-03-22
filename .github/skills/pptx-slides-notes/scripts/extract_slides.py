#!/usr/bin/env python3
"""
Extract slide images from PPTX files.

This script extracts each slide from a PowerPoint presentation as a PNG image.
It uses LibreOffice for rendering on Linux systems, ensuring high-quality output.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil


def check_dependencies():
    """Check if required dependencies are available."""
    # Check for LibreOffice
    try:
        result = subprocess.run(
            ["libreoffice", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("Warning: LibreOffice not found. Install with: sudo apt-get install libreoffice", file=sys.stderr)
            return False
    except FileNotFoundError:
        print("Warning: LibreOffice not found. Install with: sudo apt-get install libreoffice", file=sys.stderr)
        return False

    # Check for ImageMagick convert
    try:
        result = subprocess.run(
            ["convert", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("Warning: ImageMagick not found. Install with: sudo apt-get install imagemagick", file=sys.stderr)
            return False
    except FileNotFoundError:
        print("Warning: ImageMagick not found. Install with: sudo apt-get install imagemagick", file=sys.stderr)
        return False

    return True


def extract_slides_libreoffice(pptx_path, output_dir, width=1920, height=1080):
    """
    Extract slides using LibreOffice and ImageMagick.

    Args:
        pptx_path: Path to input PPTX file
        output_dir: Directory to save slide images
        width: Output image width in pixels
        height: Output image height in pixels
    """
    pptx_path = Path(pptx_path).resolve()
    output_dir = Path(output_dir).resolve()

    # Validate input
    if not pptx_path.exists():
        print(f"Error: PPTX file not found: {pptx_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting slides from: {pptx_path}")
    print(f"Output directory: {output_dir}")

    # Create temporary directory for PDF
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        # Step 1: Convert PPTX to PDF using LibreOffice
        print("\nStep 1: Converting PPTX to PDF...")
        pdf_path = tmp_dir / "presentation.pdf"

        try:
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(tmp_dir),
                    str(pptx_path)
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            print("PDF conversion successful")
        except subprocess.TimeoutExpired:
            print("Error: PDF conversion timed out", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error converting to PDF: {e}", file=sys.stderr)
            print(f"stdout: {e.stdout}", file=sys.stderr)
            print(f"stderr: {e.stderr}", file=sys.stderr)
            sys.exit(1)

        # Find the generated PDF (LibreOffice may change the filename)
        pdf_files = list(tmp_dir.glob("*.pdf"))
        if not pdf_files:
            print("Error: No PDF file generated", file=sys.stderr)
            sys.exit(1)
        pdf_path = pdf_files[0]

        # Step 2: Convert PDF pages to PNG images using ImageMagick
        print("\nStep 2: Converting PDF pages to PNG images...")

        # Calculate DPI to achieve target resolution
        # Standard slide is 10x7.5 inches, so for 1920x1080:
        dpi = int(width / 10)  # ~192 DPI for 1920 width

        output_pattern = output_dir / "slide-%03d.png"

        try:
            result = subprocess.run(
                [
                    "convert",
                    "-density", str(dpi),
                    "-quality", "100",
                    "-background", "white",
                    "-alpha", "remove",
                    "-resize", f"{width}x{height}",
                    str(pdf_path),
                    str(output_pattern)
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # 10 minute timeout
            )
            print("PNG conversion successful")
        except subprocess.TimeoutExpired:
            print("Error: PNG conversion timed out", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error converting to PNG: {e}", file=sys.stderr)
            print(f"stdout: {e.stdout}", file=sys.stderr)
            print(f"stderr: {e.stderr}", file=sys.stderr)
            sys.exit(1)

    # Count generated slides
    slides = sorted(output_dir.glob("slide-*.png"))
    print(f"\nExtracted {len(slides)} slides successfully!")

    # Print slide details
    for slide in slides:
        size_kb = slide.stat().st_size / 1024
        print(f"  - {slide.name} ({size_kb:.1f} KB)")

    return len(slides)


def extract_slides_python_pptx(pptx_path, output_dir, width=1920, height=1080):
    """
    Fallback method using python-pptx (lower quality).

    This method attempts to extract slides using the python-pptx library,
    but may not render complex layouts perfectly.
    """
    try:
        from pptx import Presentation
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Error: python-pptx and Pillow required for fallback method", file=sys.stderr)
        print("Install with: pip install python-pptx Pillow", file=sys.stderr)
        sys.exit(1)

    pptx_path = Path(pptx_path).resolve()
    output_dir = Path(output_dir).resolve()

    if not pptx_path.exists():
        print(f"Error: PPTX file not found: {pptx_path}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting slides from: {pptx_path}")
    print(f"Output directory: {output_dir}")
    print("Warning: Using fallback method - slide rendering may be limited")

    prs = Presentation(str(pptx_path))

    for i, slide in enumerate(prs.slides, start=1):
        # Create blank image
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # Add placeholder text
        text = f"Slide {i}\n(Rendering limited - use LibreOffice method for better quality)"
        draw.text((width//2, height//2), text, fill='black', anchor='mm')

        # Save image
        output_path = output_dir / f"slide-{i:03d}.png"
        img.save(output_path)
        print(f"  - Created {output_path.name}")

    print(f"\nExtracted {len(prs.slides)} slides (with limited rendering)")
    return len(prs.slides)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract slide images from PPTX files"
    )
    parser.add_argument(
        "--pptx",
        required=True,
        help="Path to input PPTX file"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for slide images"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Output image width in pixels (default: 1920)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Output image height in pixels (default: 1080)"
    )

    args = parser.parse_args()

    # Check dependencies and choose method
    if check_dependencies():
        # Use LibreOffice method (preferred)
        extract_slides_libreoffice(args.pptx, args.out, args.width, args.height)
    else:
        print("\nFalling back to python-pptx method (limited rendering)")
        response = input("Continue with limited rendering? (y/n): ")
        if response.lower() != 'y':
            print("Aborted. Please install LibreOffice and ImageMagick.")
            sys.exit(1)
        extract_slides_python_pptx(args.pptx, args.out, args.width, args.height)


if __name__ == "__main__":
    main()
