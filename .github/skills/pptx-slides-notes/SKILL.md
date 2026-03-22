# Skill: PPTX Slides + Notes Extraction

## Overview

This skill extracts slide images and speaker notes from PowerPoint (PPTX) files to prepare them for video generation. It parses the PPTX format, renders each slide as a high-quality PNG image, and extracts associated speaker notes as plain text files.

## Capabilities

- Extract slides as PNG images at high resolution (1920x1080)
- Extract speaker notes as plain text files
- Handle PPTX files with any number of slides
- Preserve slide order and numbering
- Handle slides without notes gracefully

## Dependencies

- `python-pptx`: Parse and extract data from PPTX files
- `Pillow`: Image processing and format conversion
- `comtypes` (Windows only): For high-quality slide rendering
- Alternative: Use `LibreOffice` or `unoconv` on Linux for slide rendering

## Input

- **PPTX File**: Path to PowerPoint presentation file (`.pptx` format)
- **Output Directory**: Base directory for output files

## Output

### Slides Directory
- Location: `{output_dir}/slides/`
- Format: `slide-{number:03d}.png`
- Example: `slide-001.png`, `slide-002.png`, etc.
- Resolution: 1920x1080 pixels (Full HD)

### Notes Directory
- Location: `{output_dir}/notes/`
- Format: `slide-{number:03d}.txt`
- Example: `slide-001.txt`, `slide-002.txt`, etc.
- Encoding: UTF-8
- Content: Plain text speaker notes (empty file if no notes present)

## Scripts

### extract_slides.py

Extracts slide images from PPTX.

**Usage:**
```bash
python extract_slides.py --pptx <input.pptx> --out <output_dir>
```

**Arguments:**
- `--pptx`: Path to input PPTX file (required)
- `--out`: Output directory for slide images (required)
- `--width`: Output width in pixels (default: 1920)
- `--height`: Output height in pixels (default: 1080)

**Example:**
```bash
python extract_slides.py --pptx input/deck.pptx --out output/slides
```

### extract_notes.py

Extracts speaker notes from PPTX.

**Usage:**
```bash
python extract_notes.py --pptx <input.pptx> --out <output_dir>
```

**Arguments:**
- `--pptx`: Path to input PPTX file (required)
- `--out`: Output directory for notes text files (required)

**Example:**
```bash
python extract_notes.py --pptx input/deck.pptx --out output/notes
```

## Implementation Notes

### Slide Rendering Approach

**Linux/Ubuntu (GitHub Actions):**
Uses LibreOffice in headless mode for slide rendering:
```bash
libreoffice --headless --convert-to pdf --outdir /tmp input.pptx
convert -density 300 /tmp/input.pdf -quality 100 output/slides/slide-%03d.png
```

**Alternative (Cross-platform):**
Uses `python-pptx` to extract shapes and content, then renders using PIL/Pillow.

### Notes Extraction

Uses `python-pptx` library to access slide notes directly:
```python
from pptx import Presentation

prs = Presentation('input.pptx')
for i, slide in enumerate(prs.slides):
    notes_text = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
```

## Error Handling

- **File Not Found**: Exits with error if PPTX file doesn't exist
- **Invalid PPTX**: Validates file format before processing
- **Corrupted Slides**: Skips corrupted slides and logs warnings
- **Missing Notes**: Creates empty text file for slides without notes
- **Output Directory**: Creates output directories if they don't exist

## Performance

- Processing time: ~1-2 seconds per slide
- Memory usage: ~100-200MB for typical presentations
- Parallel processing: Slides are processed sequentially (parallelization possible)

## Limitations

- Maximum tested slides: 500
- Slide animations are not captured (static images only)
- Embedded videos/audio are not extracted
- Complex SmartArt may not render perfectly
- Requires LibreOffice installation on Linux systems

## Testing

**Test Files:**
- Sample PPTX files in `input/` directory
- Unit tests for extraction logic
- Integration tests for full pipeline

**Validation:**
```bash
# After extraction, verify outputs
ls -la output/slides/  # Should show slide-*.png files
ls -la output/notes/   # Should show slide-*.txt files

# Check image dimensions
identify output/slides/slide-001.png  # Should show 1920x1080
```

## Troubleshooting

### Issue: Slides not rendering properly
**Solution:** Ensure LibreOffice is installed:
```bash
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-impress
```

### Issue: Permission errors
**Solution:** Ensure output directories have write permissions:
```bash
chmod 755 output/slides output/notes
```

### Issue: Out of memory
**Solution:** Process slides in smaller batches or increase system memory.

## Future Enhancements

- [ ] Parallel slide processing for faster extraction
- [ ] Support for slide animations export
- [ ] Extract embedded media (videos, audio)
- [ ] Preserve slide metadata (title, author, etc.)
- [ ] Support for custom aspect ratios
- [ ] PNG compression options for smaller file sizes
