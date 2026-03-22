#!/usr/bin/env python3
"""
Poll Sora 2 job status and download completed video clips.

This script monitors submitted jobs, polls their status, and downloads
completed video clips from Azure AI Foundry's Sora 2 API.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime


def load_manifest(manifest_path):
    """Load manifest JSON file."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest_path, manifest):
    """Save manifest JSON file."""
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def poll_job_status(endpoint, api_key, job_id):
    """
    Poll job status from Sora 2 API.

    Args:
        endpoint: Azure AI Foundry endpoint URL
        api_key: API authentication key
        job_id: Job ID to poll

    Returns:
        Job status dict with status, progress, and output info
    """
    try:
        import requests
    except ImportError:
        print("Error: requests library required", file=sys.stderr)
        print("Install with: pip install requests", file=sys.stderr)
        sys.exit(1)

    # Mock mode for testing
    if os.getenv("SORA_MOCK_MODE") == "1":
        return {
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "output": {
                "url": f"https://mock-storage.azure.com/{job_id}.mp4",
                "duration": 8.2,
                "size_bytes": 1048576
            }
        }

    # Poll job status
    url = f"{endpoint.rstrip('/')}/video/jobs/{job_id}"
    headers = {
        "api-key": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error polling job {job_id}: {e}", file=sys.stderr)
        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e)
        }


def download_video(url, output_path, api_key=None):
    """
    Download video file from URL.

    Args:
        url: Video file URL
        output_path: Local path to save video
        api_key: Optional API key for authenticated downloads

    Returns:
        True if successful, False otherwise
    """
    try:
        import requests
    except ImportError:
        print("Error: requests library required", file=sys.stderr)
        sys.exit(1)

    # Mock mode for testing
    if os.getenv("SORA_MOCK_MODE") == "1":
        # Create dummy video file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            # Write minimal valid MP4 header
            f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41')
            f.write(b'\x00' * 1000)  # Dummy data
        return True

    headers = {}
    if api_key:
        headers["api-key"] = api_key

    try:
        response = requests.get(url, headers=headers, stream=True, timeout=120)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except Exception as e:
        print(f"Error downloading video: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Poll Sora 2 job status and download completed clips"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest.json file"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for video clips"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Maximum wait time in seconds (default: 600)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Polling interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--endpoint",
        help="Sora API endpoint (default: from SORA_ENDPOINT env var)"
    )
    parser.add_argument(
        "--api-key",
        help="Sora API key (default: from SORA_API_KEY env var)"
    )

    args = parser.parse_args()

    # Get configuration
    endpoint = args.endpoint or os.getenv("SORA_ENDPOINT")
    api_key = args.api_key or os.getenv("SORA_API_KEY")

    if not endpoint or not api_key:
        if os.getenv("SORA_MOCK_MODE") != "1":
            print("Error: SORA_ENDPOINT and SORA_API_KEY must be set", file=sys.stderr)
            sys.exit(1)

    manifest_path = Path(args.manifest)
    output_dir = Path(args.out)

    # Load manifest
    if not manifest_path.exists():
        print(f"Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest(manifest_path)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Polling {len(manifest['slides'])} jobs")
    print(f"Timeout: {args.timeout} seconds")
    print(f"Polling interval: {args.interval} seconds")
    print()

    start_time = time.time()
    pending_jobs = [s for s in manifest['slides'] if s.get('job_id') and s.get('job_status') != 'completed']

    completed = 0
    failed = 0
    skipped = 0

    while pending_jobs and (time.time() - start_time) < args.timeout:
        print(f"Polling {len(pending_jobs)} pending jobs...")

        for slide in pending_jobs[:]:  # Copy list to allow modification
            job_id = slide.get('job_id')
            if not job_id:
                pending_jobs.remove(slide)
                skipped += 1
                continue

            # Poll job status
            status = poll_job_status(endpoint, api_key, job_id)

            # Update slide entry
            slide['job_status'] = status.get('status')
            slide['progress'] = status.get('progress', 0)

            if 'error' in status:
                slide['error'] = status['error']

            # Handle completed jobs
            if status.get('status') == 'completed':
                output_url = status.get('output', {}).get('url')
                if output_url:
                    slide_number = slide['slide_number']
                    output_path = output_dir / f"slide-{slide_number:03d}.mp4"

                    print(f"  ✓ Job {job_id} completed - downloading to {output_path.name}...")

                    if download_video(output_url, output_path, api_key):
                        slide['downloaded_at'] = datetime.utcnow().isoformat() + "Z"
                        slide['clip_duration'] = status.get('output', {}).get('duration')
                        slide['clip_size_bytes'] = status.get('output', {}).get('size_bytes')
                        completed += 1
                        print(f"    Downloaded successfully")
                    else:
                        slide['error'] = "Download failed"
                        failed += 1
                        print(f"    Download failed")
                else:
                    slide['error'] = "No output URL in completed job"
                    failed += 1

                pending_jobs.remove(slide)

            # Handle failed jobs
            elif status.get('status') in ['failed', 'error']:
                print(f"  ✗ Job {job_id} failed: {status.get('error', 'Unknown error')}")
                failed += 1
                pending_jobs.remove(slide)

            # Handle processing jobs
            elif status.get('status') == 'processing':
                progress = status.get('progress', 0)
                print(f"  ⋯ Job {job_id} processing ({progress}%)")

        # Save progress
        save_manifest(manifest_path, manifest)

        # Wait before next poll
        if pending_jobs:
            print(f"\nWaiting {args.interval} seconds before next poll...")
            print(f"Status: {completed} completed, {failed} failed, {len(pending_jobs)} pending\n")
            time.sleep(args.interval)

    # Final summary
    print("\n" + "="*60)
    print("Polling Complete")
    print("="*60)

    total_slides = len(manifest['slides'])
    print(f"Total slides: {total_slides}")
    print(f"  ✓ Completed: {completed}")
    print(f"  ✗ Failed: {failed}")
    print(f"  ⊘ Skipped: {skipped}")
    print(f"  ⋯ Still pending: {len(pending_jobs)}")

    if pending_jobs:
        print(f"\nWarning: {len(pending_jobs)} jobs still pending after timeout")
        print("You can run this script again to continue polling.")

    # Update manifest with completion status
    manifest['polling_completed_at'] = datetime.utcnow().isoformat() + "Z"
    manifest['completed_slides'] = completed
    manifest['failed_slides'] = failed
    save_manifest(manifest_path, manifest)

    print(f"\nManifest updated: {manifest_path}")

    # Exit with error if any jobs failed or are still pending
    if failed > 0 or len(pending_jobs) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
