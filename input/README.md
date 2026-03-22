# Input Directory

This directory is for storing PowerPoint (PPTX) files that will be converted to video.

## Usage

1. Place your `.pptx` file in this directory
2. The default filename expected by the workflow is `deck.pptx`
3. You can use any filename, but specify it when running the workflow

## Example

```bash
# Copy your presentation here
cp ~/Documents/my-presentation.pptx input/deck.pptx

# Or use a custom name and specify it in the workflow
cp ~/Documents/quarterly-review.pptx input/q1-review.pptx
```

## Requirements

Your PPTX file should:
- Be in PowerPoint 2007+ format (`.pptx`)
- Ideally include speaker notes for better video generation
- Have clear, high-quality slides (will be rendered at 1920x1080)
- Not be corrupted or password-protected

## Sample PPTX

To test the workflow, you can:
1. Create a simple presentation in PowerPoint/Google Slides/LibreOffice
2. Add speaker notes to slides for better video narration
3. Export as `.pptx` format
4. Place it in this directory as `deck.pptx`

## Notes

- The PPTX file itself is not committed to the repository (see `.gitignore`)
- Each user should provide their own presentation file
- Maximum recommended slides: 100 (to avoid excessive processing time)
