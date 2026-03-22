# Agent: PPTX → Sora 2 Video

## Purpose
Turn a PowerPoint deck into a stitched MP4 by extracting slides + notes, generating per-slide clips with Sora 2 (Azure AI Foundry), and concatenating them.

## Workflow
1) Use skill `pptx-slides-notes`  
   - `extract_slides.py --pptx <path> --out output/slides`  
   - `extract_notes.py --pptx <path> --out output/notes`
2) Use skill `sora2-video`  
   - `sora_generate.py --slides output/slides --notes output/notes --out output/video` (requires secrets)  
   - `poll_jobs.py --manifest output/video/manifest.json`  
   - `stitch_ffmpeg.sh output/video/clips output/video/final.mp4`
3) Publish `output/video/` as the artifact.

## Required secrets / env
- `SORA_ENDPOINT`: Azure AI Foundry endpoint for Sora 2.
- `SORA_DEPLOYMENT`: Deployment name.
- `SORA_API_KEY`: API key with job + download permissions.
- Optional: `SORA_API_VERSION` (defaults to `2024-10-21-preview`).

## Input contract
- `workflow_dispatch` input `pptx_path` (default `input/deck.pptx`).

## Output contract
- `output/slides/slide-XXX.png`
- `output/notes/slide-XXX.txt`
- `output/video/clips/slide-XXX.mp4`
- `output/video/manifest.json` (slide → prompt → job id → clip path)
- `output/video/final.mp4`

## Notes
- Video generation is asynchronous; the manifest is the source of truth for job ids and statuses.
- Image-to-video is preferred; prompts are derived from speaker notes with a sensible fallback prompt.
