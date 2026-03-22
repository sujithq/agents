# Skill: PPTX Slides + Notes Extraction

## What this skill does
- Renders each slide in a `.pptx` deck to a PNG image.
- Exports speaker notes per slide to `output/notes/slide-XXX.txt`.
- Provides clean inputs for downstream video generation skills.

## Inputs
- `pptx_path` (file): Path to the PowerPoint deck.
- `slides_out` (dir): Destination for rendered slide PNGs.
- `notes_out` (dir): Destination for per-slide notes.

## Outputs
- `slides_out/slide-XXX.png` — 1-based, zero-padded PNGs.
- `notes_out/slide-XXX.txt` — UTF-8 text of speaker notes (empty if none).

## Prerequisites
- Python 3.11+
- `libreoffice` and `pdftoppm` on `PATH` (used for slide rendering).
- Python deps: `python-pptx` (see `requirements.txt`).

## How to run locally
```bash
# Render slides to PNG
python .github/skills/pptx-slides-notes/scripts/extract_slides.py \
  --pptx input/deck.pptx \
  --out output/slides

# Extract speaker notes to text files
python .github/skills/pptx-slides-notes/scripts/extract_notes.py \
  --pptx input/deck.pptx \
  --out output/notes
```

## Notes
- Slide numbering in outputs matches presentation order.
- Rendering uses LibreOffice -> PDF -> PNG; ensure those tools are installed (CI workflow installs them).
