# PPTX to Sora 2 Video Converter

A GitHub Copilot custom agent system that converts PowerPoint presentations into engaging videos using Azure AI Foundry's Sora 2 model.

## Overview

This repository contains a complete GitHub Agent with Skills that:

1. **Extracts slides and notes** from PPTX files
2. **Generates video clips** for each slide using Sora 2's image-to-video capabilities
3. **Stitches clips together** into a final MP4 video

The system follows the GitHub Agent Skills model, with modular skills that can be reused and combined.

## Features

- 🎨 **High-quality slide rendering** (1920x1080 resolution)
- 🤖 **AI-powered video generation** using Sora 2 (Azure AI Foundry)
- 📝 **Speaker notes integration** as video generation guidance
- ⚡ **Asynchronous processing** with job polling and status tracking
- 🎬 **Automatic stitching** using FFmpeg
- 📊 **Detailed manifest** tracking all jobs and metadata
- 🔄 **GitHub Actions workflow** for CI/CD automation

## Repository Structure

```
.github/
├── agents/
│   └── pptx-to-sora-video.agent.md      # Agent definition
├── skills/
│   ├── pptx-slides-notes/               # Skill #1: PPTX extraction
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── extract_slides.py
│   │       └── extract_notes.py
│   └── sora2-video/                     # Skill #2: Video generation
│       ├── SKILL.md
│       └── scripts/
│           ├── sora_generate.py
│           ├── poll_jobs.py
│           └── stitch_ffmpeg.sh
└── workflows/
    └── pptx-to-video.yml                # GitHub Actions workflow

input/                                    # Place your PPTX files here
├── README.md
└── deck.pptx                            # (gitignored, add your own)

output/                                   # Generated output (gitignored)
├── slides/                              # Extracted slide images
├── notes/                               # Extracted speaker notes
└── video/
    ├── clips/                           # Individual video clips
    ├── manifest.json                    # Job tracking metadata
    └── final.mp4                        # Final stitched video

requirements.txt                          # Python dependencies
.gitignore                               # Excludes output files
```

## Quick Start

### Prerequisites

- **Azure AI Foundry** account with Sora 2 access
- **GitHub repository** with Actions enabled
- **PowerPoint file** (.pptx format)

### Setup

1. **Configure GitHub Secrets**

   Go to your repository Settings → Secrets and add:

   - `SORA_ENDPOINT`: Your Azure AI Foundry endpoint URL
   - `SORA_API_KEY`: Your Sora 2 API key
   - `AZURE_TENANT_ID`: (Optional) Azure tenant ID

2. **Add your PPTX file**

   ```bash
   # Place your presentation in the input directory
   cp ~/path/to/your-presentation.pptx input/deck.pptx
   ```

3. **Run the workflow**

   - Go to Actions → "PPTX to Video Conversion"
   - Click "Run workflow"
   - Enter the PPTX file path (default: `input/deck.pptx`)
   - Click "Run workflow"

4. **Download results**

   Once complete, download the artifacts:
   - `final-video`: Contains the final MP4
   - `pptx-video-output`: Contains all slides, notes, clips, and manifest

## Local Development

### Install Dependencies

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-impress imagemagick ffmpeg

# Python dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# 1. Extract slides
python .github/skills/pptx-slides-notes/scripts/extract_slides.py \
  --pptx input/deck.pptx \
  --out output/slides

# 2. Extract notes
python .github/skills/pptx-slides-notes/scripts/extract_notes.py \
  --pptx input/deck.pptx \
  --out output/notes

# 3. Set environment variables
export SORA_ENDPOINT="https://your-endpoint.azure.com"
export SORA_API_KEY="your-api-key"

# 4. Generate video clips
python .github/skills/sora2-video/scripts/sora_generate.py \
  --slides output/slides \
  --notes output/notes \
  --out output/video/clips

# 5. Poll jobs and download clips
python .github/skills/sora2-video/scripts/poll_jobs.py \
  --manifest output/video/manifest.json \
  --out output/video/clips \
  --timeout 900

# 6. Stitch final video
bash .github/skills/sora2-video/scripts/stitch_ffmpeg.sh \
  output/video/clips \
  output/video/final.mp4
```

### Testing Mode

For testing without consuming API quota:

```bash
export SORA_MOCK_MODE=1

# Run scripts - they will create mock outputs
python .github/skills/sora2-video/scripts/sora_generate.py ...
python .github/skills/sora2-video/scripts/poll_jobs.py ...
```

## Agent Skills

### Skill #1: PPTX Slides + Notes Extraction

**Location**: `.github/skills/pptx-slides-notes/`

Extracts slide images and speaker notes from PowerPoint files.

**Capabilities**:
- Renders slides at 1920x1080 resolution using LibreOffice
- Extracts speaker notes as plain text
- Handles presentations with any number of slides

**Documentation**: See [SKILL.md](.github/skills/pptx-slides-notes/SKILL.md)

### Skill #2: Sora 2 Video Generation + Stitching

**Location**: `.github/skills/sora2-video/`

Generates video clips using Sora 2 and stitches them together.

**Capabilities**:
- Image-to-video generation using Sora 2
- Asynchronous job management (submit → poll → download)
- Intelligent prompt generation from speaker notes
- Video stitching with FFmpeg

**Documentation**: See [SKILL.md](.github/skills/sora2-video/SKILL.md)

## Configuration

### Video Settings

Edit `.github/skills/sora2-video/scripts/sora_generate.py`:

- **Duration**: Adjust `--duration` parameter (default: 8 seconds)
- **Resolution**: Modify resolution in script (default: 1920x1080)
- **Frame rate**: Change FPS setting (default: 30)

### FFmpeg Settings

Edit `.github/skills/sora2-video/scripts/stitch_ffmpeg.sh`:

- **Codec**: Change from H.264 to other formats
- **Quality**: Adjust CRF value (lower = higher quality)
- **Audio**: Add audio track configuration

## Output Format

### Manifest (manifest.json)

The manifest tracks all generation jobs and metadata:

```json
{
  "generated_at": "2026-03-22T14:00:00Z",
  "total_slides": 10,
  "sora_config": {
    "endpoint": "https://...",
    "model": "sora-2",
    "duration_per_slide": 8
  },
  "slides": [
    {
      "slide_number": 1,
      "image_path": "output/slides/slide-001.png",
      "notes_path": "output/notes/slide-001.txt",
      "prompt": "Generate video...",
      "job_id": "sora-job-abc123",
      "job_status": "completed",
      "clip_path": "output/video/clips/slide-001.mp4"
    }
  ],
  "final_video": "output/video/final.mp4"
}
```

## Troubleshooting

### Common Issues

**Issue**: Slides not rendering properly
```bash
# Ensure LibreOffice is installed
sudo apt-get install -y libreoffice libreoffice-impress
```

**Issue**: Sora API authentication errors
```bash
# Verify environment variables
echo $SORA_ENDPOINT
echo $SORA_API_KEY
```

**Issue**: Jobs timing out
```bash
# Increase timeout when polling
python poll_jobs.py --manifest manifest.json --timeout 1800
```

**Issue**: FFmpeg stitching fails
```bash
# Install FFmpeg
sudo apt-get install -y ffmpeg
```

## Performance

- **Slide extraction**: ~1-2 seconds per slide
- **Sora generation**: ~30-60 seconds per slide
- **Stitching**: ~2-5 seconds for 10 slides
- **Total time**: ~5-15 minutes for a 10-slide presentation

## Limitations

- Maximum tested slides: 100
- Sora 2 preview limitations apply
- Requires Azure AI Foundry access
- Processing time scales linearly with slide count

## Future Enhancements

- [ ] Text-to-speech narration from speaker notes
- [ ] Custom transitions between slides
- [ ] Background music support
- [ ] Progress estimation and ETA
- [ ] Parallel job processing
- [ ] Custom video effects and filters

## References

- [GitHub Agent Skills Documentation](https://docs.github.com/en/copilot/customizing-copilot/creating-custom-agent-skills)
- [Azure AI Foundry - Sora 2](https://azure.microsoft.com/en-us/products/ai-services/openai-service-video)
- [Sora API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/video-generation)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For questions or issues:
1. Check the skill documentation in `.github/skills/*/SKILL.md`
2. Review the GitHub Actions workflow logs
3. Open an issue in this repository
