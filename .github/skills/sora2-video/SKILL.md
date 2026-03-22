# Skill: Sora 2 Video Generation + Stitching

## What this skill does
- Submits per-slide image-to-video jobs to Sora 2 (Azure AI Foundry).
- Polls jobs asynchronously until clips are ready and downloads them.
- Stitches ordered clips into a single `final.mp4`.

## Inputs
- `slides_dir`: PNG slides (e.g., `output/slides`).
- `notes_dir`: Per-slide notes (optional, e.g., `output/notes`).
- `video_out`: Directory for manifest + clips (e.g., `output/video`).
- Credentials: `SORA_ENDPOINT`, `SORA_DEPLOYMENT`, `SORA_API_KEY` (optional `SORA_API_VERSION`).

## Outputs
- `video_out/manifest.json` — slide → prompt → job id → clip mapping.
- `video_out/clips/slide-XXX.mp4` — per-slide clips.
- `video_out/final.mp4` — concatenated video.

## How to run locally
```bash
# Submit jobs
python .github/skills/sora2-video/scripts/sora_generate.py \
  --slides output/slides \
  --notes output/notes \
  --out output/video

# Poll + download clips
python .github/skills/sora2-video/scripts/poll_jobs.py \
  --manifest output/video/manifest.json

# Stitch clips
bash .github/skills/sora2-video/scripts/stitch_ffmpeg.sh \
  output/video/clips \
  output/video/final.mp4
```

## Notes
- Sora requests are async: `sora_generate.py` writes `manifest.json` with job ids; `poll_jobs.py` updates it as jobs complete.
- The payload uses base64-encoded slide images with prompts derived from notes (fallback prompt if notes are empty).
- Ensure `ffmpeg` is available for stitching (installed on ubuntu-latest runners).
