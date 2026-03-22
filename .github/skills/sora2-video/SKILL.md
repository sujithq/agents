# Skill: Sora 2 Video Generation + Stitching

## Overview

This skill generates video clips from slide images using Azure AI Foundry's Sora 2 model and stitches them together into a final video. It leverages Sora 2's image-to-video capabilities with asynchronous job processing.

## Capabilities

- **Image-to-Video Generation**: Convert slide images to video clips using Sora 2
- **Async Job Management**: Submit, poll, and track Sora 2 generation jobs
- **Batch Processing**: Handle multiple slides concurrently
- **Video Stitching**: Combine clips into a single seamless video using FFmpeg
- **Manifest Generation**: Track all jobs and metadata in JSON format

## Dependencies

- `requests`: HTTP client for Azure API calls
- `azure-identity`: Azure authentication
- `ffmpeg`: Video processing and stitching
- `python-dotenv`: Environment variable management

## Input

### Slide Images
- Location: `output/slides/slide-*.png`
- Format: PNG images (1920x1080)

### Speaker Notes
- Location: `output/notes/slide-*.txt`
- Format: Plain text files (UTF-8)

### Configuration
- `SORA_ENDPOINT`: Azure AI Foundry endpoint URL
- `SORA_API_KEY`: API authentication key
- `AZURE_TENANT_ID`: (Optional) Azure tenant ID

## Output

### Video Clips
- Location: `output/video/clips/slide-*.mp4`
- Format: MP4 (H.264)
- Resolution: 1920x1080
- Duration: 5-10 seconds per slide

### Manifest File
- Location: `output/video/manifest.json`
- Format: JSON metadata with job tracking

### Final Video
- Location: `output/video/final.mp4`
- Format: MP4 (H.264)
- Resolution: 1920x1080
- Codec: H.264 with AAC audio (if audio added)

## Scripts

### sora_generate.py

Submits video generation jobs to Sora 2 for each slide.

**Usage:**
```bash
python sora_generate.py --slides <slides_dir> --notes <notes_dir> --out <output_dir>
```

**Arguments:**
- `--slides`: Directory containing slide images (required)
- `--notes`: Directory containing notes text files (required)
- `--out`: Output directory for video clips (required)
- `--duration`: Video duration per slide in seconds (default: 8)
- `--endpoint`: Sora API endpoint (optional, uses env var)
- `--api-key`: Sora API key (optional, uses env var)

**Example:**
```bash
export SORA_ENDPOINT="https://your-endpoint.azure.com"
export SORA_API_KEY="your-api-key"

python sora_generate.py \
  --slides output/slides \
  --notes output/notes \
  --out output/video/clips
```

**Output:**
Creates `output/video/manifest.json` with job IDs and status.

### poll_jobs.py

Polls Sora 2 job status and downloads completed video clips.

**Usage:**
```bash
python poll_jobs.py --manifest <manifest.json> --out <output_dir>
```

**Arguments:**
- `--manifest`: Path to manifest.json file (required)
- `--out`: Output directory for downloaded clips (required)
- `--timeout`: Maximum wait time in seconds (default: 600)
- `--interval`: Polling interval in seconds (default: 10)

**Example:**
```bash
python poll_jobs.py \
  --manifest output/video/manifest.json \
  --out output/video/clips \
  --timeout 900
```

**Output:**
Downloads completed MP4 clips and updates manifest with download status.

### stitch_ffmpeg.sh

Stitches individual video clips into a single final video.

**Usage:**
```bash
bash stitch_ffmpeg.sh <clips_dir> <output_file>
```

**Arguments:**
- `clips_dir`: Directory containing video clips (required)
- `output_file`: Path for final stitched video (required)

**Example:**
```bash
bash stitch_ffmpeg.sh output/video/clips output/video/final.mp4
```

**Output:**
Creates `final.mp4` with all clips concatenated in order.

## Sora 2 API Integration

### Authentication

Uses Azure API key authentication:
```python
headers = {
    "api-key": os.getenv("SORA_API_KEY"),
    "Content-Type": "application/json"
}
```

### Job Submission

**Endpoint:** `POST {SORA_ENDPOINT}/video/generate`

**Request Body:**
```json
{
  "mode": "image-to-video",
  "image": {
    "url": "https://...",
    "base64": "..."
  },
  "prompt": "Generate engaging video from this presentation slide...",
  "duration": 8,
  "resolution": "1920x1080",
  "fps": 30
}
```

**Response:**
```json
{
  "job_id": "sora-job-abc123",
  "status": "pending",
  "created_at": "2026-03-22T14:00:00Z"
}
```

### Job Polling

**Endpoint:** `GET {SORA_ENDPOINT}/video/jobs/{job_id}`

**Response:**
```json
{
  "job_id": "sora-job-abc123",
  "status": "completed",
  "progress": 100,
  "output": {
    "url": "https://storage.azure.com/...",
    "duration": 8.2,
    "size_bytes": 1048576
  }
}
```

**Status Values:**
- `pending`: Job submitted, waiting to start
- `processing`: Video generation in progress
- `completed`: Job finished successfully
- `failed`: Job failed with error

## Manifest Schema

```json
{
  "presentation": "input/deck.pptx",
  "generated_at": "2026-03-22T14:00:00Z",
  "total_slides": 5,
  "sora_config": {
    "endpoint": "https://your-endpoint.azure.com",
    "model": "sora-2",
    "duration_per_slide": 8,
    "resolution": "1920x1080"
  },
  "slides": [
    {
      "slide_number": 1,
      "image_path": "output/slides/slide-001.png",
      "notes_path": "output/notes/slide-001.txt",
      "prompt": "Generate video from slide with title...",
      "job_id": "sora-job-abc123",
      "job_status": "completed",
      "clip_path": "output/video/clips/slide-001.mp4",
      "clip_duration": 8.2,
      "submitted_at": "2026-03-22T14:00:00Z",
      "completed_at": "2026-03-22T14:05:30Z"
    }
  ],
  "final_video": "output/video/final.mp4",
  "total_duration": 41.5
}
```

## Prompt Engineering

The script generates prompts for Sora 2 by combining:

1. **Visual Context**: "Generate a video based on this presentation slide..."
2. **Notes Content**: Incorporates speaker notes as narration guidance
3. **Style Instructions**: "Professional presentation style, smooth camera movements..."
4. **Duration Hint**: Adjusted based on notes length

**Example Prompt:**
```
Generate a professional presentation video from this slide image.
The slide shows [content description].

Speaker notes: "Welcome to our quarterly review. Today we'll discuss..."

Style: Professional business presentation with subtle camera movements
and smooth transitions. Duration: 8 seconds.
```

## FFmpeg Stitching

### Concatenation Method

Uses FFmpeg's concat demuxer for seamless stitching:

```bash
# Create file list
echo "file 'slide-001.mp4'" > filelist.txt
echo "file 'slide-002.mp4'" >> filelist.txt
...

# Concatenate
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output/video/final.mp4
```

### Re-encoding (if clips have different codecs)

```bash
ffmpeg -f concat -safe 0 -i filelist.txt \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  output/video/final.mp4
```

## Error Handling

### API Errors
- **Authentication Failure**: Validates credentials before submitting jobs
- **Rate Limiting**: Implements exponential backoff with retries
- **Quota Exceeded**: Reports clear error message with quota status

### Job Failures
- **Timeout**: Marks jobs as failed after timeout period
- **Generation Error**: Logs error details from Sora API
- **Retry Logic**: Retries failed jobs up to 3 times

### Stitching Errors
- **Missing Clips**: Validates all clips exist before stitching
- **Codec Mismatch**: Automatically re-encodes if needed
- **Duration Mismatch**: Adjusts frame rates if necessary

## Performance

- **Concurrent Jobs**: Submits up to 5 jobs in parallel
- **Polling Efficiency**: Uses adaptive polling interval
- **Processing Time**: ~30-60 seconds per slide (Sora generation)
- **Stitching Time**: ~2-5 seconds for 10 slides

## Limitations

- Maximum video duration per clip: 60 seconds (Sora limit)
- Maximum concurrent jobs: 5 (configurable)
- Total processing time: ~5-10 minutes for 10 slides
- Sora 2 preview limitations apply (check Azure docs)

## Testing

**Unit Tests:**
```bash
pytest tests/test_sora_generate.py
pytest tests/test_poll_jobs.py
pytest tests/test_stitch.py
```

**Integration Test:**
```bash
# Test with sample data
python sora_generate.py --slides tests/fixtures/slides --notes tests/fixtures/notes --out /tmp/test-output
```

**Mock Mode:**
Set `SORA_MOCK_MODE=1` to use mock API responses for testing without consuming API quota.

## Troubleshooting

### Issue: Authentication errors
**Solution:** Verify `SORA_API_KEY` is set correctly:
```bash
echo $SORA_API_KEY  # Should show your key
```

### Issue: Jobs timeout
**Solution:** Increase timeout value:
```bash
python poll_jobs.py --manifest manifest.json --out output --timeout 1800
```

### Issue: FFmpeg not found
**Solution:** Install FFmpeg:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### Issue: Video quality issues
**Solution:** Adjust FFmpeg encoding settings in `stitch_ffmpeg.sh`.

## Future Enhancements

- [ ] Add audio narration from speaker notes using TTS
- [ ] Support for custom transitions between clips
- [ ] Parallel job submission with dynamic concurrency
- [ ] Resume capability for interrupted workflows
- [ ] Progress bar for long-running operations
- [ ] Cost estimation before submitting jobs
- [ ] Quality presets (low/medium/high)
- [ ] Custom video effects and filters
