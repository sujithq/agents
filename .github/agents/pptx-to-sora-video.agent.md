# PPTX to Sora 2 Video Agent

## Description

This agent converts PowerPoint presentations (PPTX files) into video format by:
1. Extracting slide images and speaker notes from the PPTX file
2. Generating video clips for each slide using Azure AI Foundry's Sora 2 model (image-to-video)
3. Stitching all clips together into a single final MP4 video

The agent leverages Sora 2's image-to-video capabilities, anchoring each video clip on the slide image while using speaker notes as guidance text.

## Capabilities

- **PPTX Extraction**: Extracts high-quality slide images (PNG) and speaker notes (TXT)
- **AI Video Generation**: Creates engaging video clips using Sora 2's image-to-video model
- **Asynchronous Processing**: Handles Sora 2's async job model (submit → poll → download)
- **Video Stitching**: Combines individual slide clips into a cohesive final video
- **Manifest Tracking**: Maintains detailed metadata about the conversion process

## Skills Used

This agent orchestrates the following skills:

### 1. PPTX Slides + Notes Extraction (`pptx-slides-notes`)
Located at: `.github/skills/pptx-slides-notes/`

Extracts slide images and speaker notes from PowerPoint files.

### 2. Sora 2 Video Generation + Stitching (`sora2-video`)
Located at: `.github/skills/sora2-video/`

Generates video clips using Azure AI Foundry's Sora 2 model and stitches them together.

## Input Contract

### Required Input
- **PPTX File Path**: Path to the PowerPoint presentation file
  - Default: `input/deck.pptx`
  - Format: `.pptx` (PowerPoint 2007+)

### Required Secrets (GitHub Actions)
The following secrets must be configured in your GitHub repository:

- `SORA_ENDPOINT`: Azure AI Foundry endpoint URL for Sora 2
- `SORA_API_KEY`: API key for authenticating with Azure AI Foundry
- `AZURE_TENANT_ID`: (Optional) Azure tenant ID if using Azure AD authentication

## Output Contract

### Directory Structure
```
output/
├── slides/              # Extracted slide images
│   ├── slide-001.png
│   ├── slide-002.png
│   └── ...
├── notes/               # Extracted speaker notes
│   ├── slide-001.txt
│   ├── slide-002.txt
│   └── ...
└── video/
    ├── clips/           # Individual video clips per slide
    │   ├── slide-001.mp4
    │   ├── slide-002.mp4
    │   └── ...
    ├── manifest.json    # Metadata about the conversion
    └── final.mp4        # Final stitched video
```

### Manifest Schema
The `manifest.json` file contains:
```json
{
  "presentation": "input/deck.pptx",
  "generated_at": "2026-03-22T14:00:00Z",
  "total_slides": 10,
  "slides": [
    {
      "slide_number": 1,
      "image_path": "output/slides/slide-001.png",
      "notes_path": "output/notes/slide-001.txt",
      "prompt": "Generate video from slide image with narration...",
      "job_id": "sora-job-12345",
      "clip_path": "output/video/clips/slide-001.mp4",
      "status": "completed"
    }
  ],
  "final_video": "output/video/final.mp4"
}
```

## Workflow Steps

1. **Extract Slides**: Parse PPTX and save slide images as PNG files
2. **Extract Notes**: Extract speaker notes text for each slide
3. **Generate Prompts**: Create Sora 2 prompts combining slide context with notes
4. **Submit Jobs**: Send image-to-video generation requests to Sora 2 API
5. **Poll Status**: Monitor job completion (async polling pattern)
6. **Download Clips**: Retrieve completed video clips
7. **Stitch Video**: Combine all clips using FFmpeg into final.mp4
8. **Generate Manifest**: Create metadata JSON with all details

## Usage

### Via GitHub Actions (CI)

Run the workflow manually with:
```bash
gh workflow run pptx-to-video.yml -f pptx_path=input/deck.pptx
```

Or trigger via GitHub UI:
1. Go to Actions → "PPTX to Video Conversion"
2. Click "Run workflow"
3. Enter PPTX file path
4. Run workflow

The final video will be available as a workflow artifact.

### Via CLI (Local Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Extract slides and notes
python .github/skills/pptx-slides-notes/scripts/extract_slides.py \
  --pptx input/deck.pptx \
  --out output/slides

python .github/skills/pptx-slides-notes/scripts/extract_notes.py \
  --pptx input/deck.pptx \
  --out output/notes

# Generate videos (requires Azure credentials)
export SORA_ENDPOINT="https://your-endpoint.azure.com"
export SORA_API_KEY="your-api-key"

python .github/skills/sora2-video/scripts/sora_generate.py \
  --slides output/slides \
  --notes output/notes \
  --out output/video/clips

python .github/skills/sora2-video/scripts/poll_jobs.py \
  --manifest output/video/manifest.json \
  --out output/video/clips

# Stitch clips
bash .github/skills/sora2-video/scripts/stitch_ffmpeg.sh \
  output/video/clips \
  output/video/final.mp4
```

## Configuration

### Sora 2 Settings
- **Model**: Sora 2 (Azure AI Foundry)
- **Mode**: Image-to-video (preferred) with text guidance
- **Duration**: Configurable per slide (default: 5-10 seconds based on notes length)
- **Resolution**: 1920x1080 (Full HD)

### FFmpeg Settings
- **Codec**: H.264 for broad compatibility
- **Frame Rate**: 30 fps
- **Audio**: None (video only, unless notes-to-speech is added)

## Error Handling

- **Invalid PPTX**: Validates file format before processing
- **Missing Notes**: Generates video without text guidance if notes are absent
- **Sora Job Failure**: Retries failed jobs up to 3 times with exponential backoff
- **Timeout**: Sets maximum wait time per job (default: 10 minutes)

## Limitations

- Maximum slides: 100 (to prevent excessive API usage)
- Slide resolution: Limited by PPTX source quality
- Processing time: Depends on Sora 2 API queue and slide count
- No audio narration: Speaker notes guide video generation but aren't converted to audio (see stretch goals)

## Stretch Goals (Future Enhancements)

- [ ] Text-to-speech narration from speaker notes
- [ ] Custom transitions between slides
- [ ] Timing estimation based on notes length
- [ ] Background music support
- [ ] Custom branding/watermarks
- [ ] Progress indicators in the video

## References

- [GitHub Agent Skills Documentation](https://docs.github.com/en/copilot/customizing-copilot/creating-custom-agent-skills)
- [Azure AI Foundry - Sora 2](https://azure.microsoft.com/en-us/products/ai-services/openai-service-video)
- [Sora API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/video-generation)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## Support

For issues, questions, or contributions, please refer to the repository documentation or open an issue.
