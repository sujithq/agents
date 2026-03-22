# Skill: pptx-slides-notes

## Summary

Extract per-slide **PNG images** and **speaker notes** from a `.pptx` file.

## When to Use

Load this skill whenever the user provides a PowerPoint file and asks to:
- Convert slides to images
- Extract speaker notes
- Prepare slides for downstream video generation

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract_slides.py` | Render each slide to a PNG file |
| `scripts/extract_notes.py` | Extract speaker notes to plain-text files |

## Usage

```bash
# Extract slides to PNG
python scripts/extract_slides.py \
    --pptx <path/to/deck.pptx> \
    --out  <output/slides>

# Extract speaker notes to TXT
python scripts/extract_notes.py \
    --pptx <path/to/deck.pptx> \
    --out  <output/notes>
```

## Output

| Path | Description |
|------|-------------|
| `<out>/slide-NNN.png` | Rendered slide image (1-indexed, zero-padded to 3 digits) |
| `<out>/slide-NNN.txt` | Speaker notes for that slide (empty file if no notes) |

## Dependencies

Listed in the repository root `requirements.txt`:

- `python-pptx` – parse PPTX structure and notes
- `Pillow` – image handling
- `pymupdf` (optional) – higher-quality slide rendering via LibreOffice export fallback

Install with:

```bash
pip install -r requirements.txt
```

## Notes

- Slides are rendered at **1920×1080** resolution by default (configurable via `--width` / `--height`).
- LibreOffice (`soffice`) is used as the rendering backend. On Ubuntu it can be installed with `sudo apt-get install libreoffice`.
- If a slide has no speaker notes, an empty `.txt` file is still created to keep the index consistent.
- Numbering is 1-based and zero-padded to three digits (`slide-001`, `slide-002`, …).
