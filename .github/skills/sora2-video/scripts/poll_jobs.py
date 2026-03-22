#!/usr/bin/env python3
"""
poll_jobs.py
------------
Poll Sora 2 video generation jobs recorded in manifest.json until all jobs
reach a terminal state (succeeded / failed), then download the resulting
video clips.

Environment variables (required):
    SORA_ENDPOINT   – Azure AI Foundry endpoint
    SORA_API_KEY    – API key for the Sora 2 deployment
    SORA_DEPLOYMENT – Deployment name (default: "sora")

Usage:
    python poll_jobs.py \
        --manifest   output/video/manifest.json \
        --clips-dir  output/video/clips \
        [--interval  15] \
        [--timeout   1800]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests


SORA_API_VERSION = "2025-04-01-preview"
TERMINAL_STATES = {"succeeded", "failed", "cancelled"}


def get_env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        print(f"ERROR: Environment variable '{name}' is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def poll_job_status(endpoint: str, api_key: str, job_id: str) -> dict:
    """Return the current job status dict from the Sora API."""
    url = (
        f"{endpoint.rstrip('/')}/openai/v1/video/generations/jobs/{job_id}"
        f"?api-version={SORA_API_VERSION}"
    )
    headers = {"api-key": api_key}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to poll job {job_id}: {response.status_code} {response.text}"
        )
    return response.json()


def download_clip(endpoint: str, api_key: str, job_data: dict, out_path: Path) -> None:
    """Download the generated video clip from the completed Sora job."""
    # The Sora response includes a 'generations' list with a 'video' object
    generations = job_data.get("generations", [])
    if not generations:
        raise RuntimeError(f"No generations found in job response: {job_data}")

    video = generations[0].get("video", {})
    # Try direct URL first, then content_url
    video_url = video.get("url") or video.get("content_url", "")
    if not video_url:
        raise RuntimeError(f"No video URL found in job response: {job_data}")

    headers = {"api-key": api_key}
    response = requests.get(video_url, headers=headers, timeout=300, stream=True)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download clip from {video_url}: {response.status_code}"
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=8192):
            fh.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Poll Sora 2 jobs and download completed video clips."
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    parser.add_argument("--clips-dir", required=True, help="Directory to save downloaded clips")
    parser.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    parser.add_argument("--timeout", type=int, default=1800, help="Max total wait in seconds (default: 1800)")
    args = parser.parse_args()

    endpoint = get_env("SORA_ENDPOINT")
    api_key = get_env("SORA_API_KEY")

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips_dir = Path(args.clips_dir)
    clips_dir.mkdir(parents=True, exist_ok=True)

    # Build list of pending slides
    pending = [s for s in manifest["slides"] if s.get("job_id") and s.get("status") not in TERMINAL_STATES]
    print(f"Polling {len(pending)} pending job(s) …")

    start_time = time.time()
    while pending:
        if time.time() - start_time > args.timeout:
            print("ERROR: Timeout waiting for Sora jobs to complete.", file=sys.stderr)
            sys.exit(1)

        still_pending = []
        for slide in pending:
            job_id = slide["job_id"]
            slide_num = slide["index"]
            try:
                job_data = poll_job_status(endpoint, api_key, job_id)
            except RuntimeError as exc:
                print(f"  WARNING: {exc}", file=sys.stderr)
                still_pending.append(slide)
                continue

            status = job_data.get("status", "unknown")
            print(f"  Slide {slide_num:03d} job {job_id}: {status}")

            if status == "succeeded":
                clip_path = clips_dir / f"slide-{slide_num:03d}.mp4"
                try:
                    download_clip(endpoint, api_key, job_data, clip_path)
                    print(f"  Downloaded clip → {clip_path}")
                    slide["status"] = "succeeded"
                    slide["clip"] = str(clip_path)
                except RuntimeError as exc:
                    print(f"  ERROR downloading clip for slide {slide_num}: {exc}", file=sys.stderr)
                    slide["status"] = "download_failed"
            elif status in TERMINAL_STATES:
                slide["status"] = status
                print(f"  Slide {slide_num:03d} job ended with status: {status}")
            else:
                still_pending.append(slide)

        # Update manifest after each poll round
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        if still_pending:
            pending = still_pending
            print(f"  {len(pending)} job(s) still running. Waiting {args.interval}s …")
            time.sleep(args.interval)
        else:
            pending = []

    # Final manifest save
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    succeeded = sum(1 for s in manifest["slides"] if s.get("status") == "succeeded")
    total = len(manifest["slides"])
    print(f"Done. {succeeded}/{total} slide(s) downloaded successfully.")
    if succeeded < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
