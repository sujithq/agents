# Skill: sora2-video

## Summary

Generate per-slide video clips with **Sora 2** (Azure AI Foundry) using
image→video mode (slide PNG as anchor image, speaker notes as guidance text),
then stitch all clips into a single `final.mp4`.

## When to Use

Load this skill when the user wants to:
- Generate AI video from presentation slides
- Submit and poll async Sora 2 video generation jobs
- Assemble individual video clips into a final video

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/sora_generate.py` | Submit one Sora 2 image→video job per slide and write a `manifest.json` |
| `scripts/poll_jobs.py` | Poll all pending jobs until complete and download the resulting clips |
| `scripts/stitch_ffmpeg.sh` | Concatenate all per-slide clips into a single `final.mp4` using ffmpeg |

## Required Secrets / Environment Variables

| Variable | Description |
|----------|-------------|
| `SORA_ENDPOINT` | Azure AI Foundry endpoint (e.g. `https://<resource>.openai.azure.com/`) |
| `SORA_API_KEY` | API key for the Sora 2 deployment |
| `SORA_DEPLOYMENT` | Deployment name (default: `sora`) |

## Usage

```bash
# 1. Submit one Sora job per slide (image→video)
python scripts/sora_generate.py \
    --slides-dir output/slides \
    --notes-dir  output/notes \
    --manifest   output/video/manifest.json \
    [--duration  5]          # seconds per clip (default: 5)
    [--pptx      input/deck.pptx]

# 2. Poll jobs until all are done and download clips
python scripts/poll_jobs.py \
    --manifest   output/video/manifest.json \
    --clips-dir  output/video/clips \
    [--interval  15]         # poll interval in seconds (default: 15)
    [--timeout   1800]       # max wait in seconds (default: 1800)

# 3. Stitch clips into final.mp4
bash scripts/stitch_ffmpeg.sh \
    output/video/clips \
    output/video/final.mp4
```

## Output

| Path | Description |
|------|-------------|
| `output/video/manifest.json` | Job manifest (slide → prompt → job ID → clip path → status) |
| `output/video/clips/slide-NNN.mp4` | Per-slide video clip downloaded from Sora |
| `output/video/final.mp4` | Final stitched video |

## Sora 2 API Notes

- Video generation is **asynchronous**: submit a job, then poll for completion.
- Sora 2 supports both **text→video** and **image→video**; this skill uses image→video.
- The slide PNG is Base64-encoded and sent as the `image` anchor parameter.
- Speaker notes are included as the `prompt` parameter to guide narration/content.
- Reference: [Azure AI Foundry – Sora video generation](https://learn.microsoft.com/azure/ai-services/openai/concepts/video-generation)

## Dependencies

```bash
pip install -r requirements.txt
```

ffmpeg must be installed on the runner:

```bash
sudo apt-get install -y ffmpeg
```
