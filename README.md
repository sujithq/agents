# PPTX to Sora 2 Video Agent

This repository contains a GitHub Copilot custom agent plus skills that turn a `.pptx` deck into a stitched MP4 using Sora 2 (Azure AI Foundry). The pipeline extracts slide images and speaker notes, submits image-to-video jobs per slide, polls asynchronously, and stitches the clips.

## Prerequisites
- Python 3.11+
- System tools: `libreoffice`, `pdftoppm` (from `poppler-utils`), `ffmpeg`
- Python deps: `pip install -r requirements.txt`
- Secrets for Sora: `SORA_ENDPOINT`, `SORA_DEPLOYMENT`, `SORA_API_KEY` (optional `SORA_API_VERSION`)

## Run locally
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt

# Extract slides + notes
python .github/skills/pptx-slides-notes/scripts/extract_slides.py --pptx input/deck.pptx --out output/slides
python .github/skills/pptx-slides-notes/scripts/extract_notes.py --pptx input/deck.pptx --out output/notes

# Submit Sora jobs
python .github/skills/sora2-video/scripts/sora_generate.py --slides output/slides --notes output/notes --out output/video

# Poll + download clips
python .github/skills/sora2-video/scripts/poll_jobs.py --manifest output/video/manifest.json

# Stitch clips
bash .github/skills/sora2-video/scripts/stitch_ffmpeg.sh output/video/clips output/video/final.mp4
```

Outputs (relative to repo):
- `output/slides/slide-XXX.png`
- `output/notes/slide-XXX.txt`
- `output/video/clips/slide-XXX.mp4`
- `output/video/manifest.json`
- `output/video/final.mp4`

## GitHub Actions workflow
- Workflow: `.github/workflows/pptx-to-video.yml`
- Trigger: `workflow_dispatch` with input `pptx_path` (default `input/deck.pptx`)
- Secrets required: `SORA_ENDPOINT`, `SORA_DEPLOYMENT`, `SORA_API_KEY` (optional `SORA_API_VERSION`)
- Artifacts: uploads `output/video/` (includes `final.mp4` and `manifest.json`)

## Skills / Agent
- Agent definition: `.github/agents/pptx-to-sora-video.agent.md`
- Skills:
  - `.github/skills/pptx-slides-notes` — slide rendering + note extraction
  - `.github/skills/sora2-video` — Sora job submit/poll + ffmpeg stitching
