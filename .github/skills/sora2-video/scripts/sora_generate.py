#!/usr/bin/env python3
"""
Generate video clips using Sora 2 (Azure AI Foundry).

This script submits video generation jobs to Azure AI Foundry's Sora 2 API
for each slide, using image-to-video mode with speaker notes as guidance.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import time


def load_image_as_base64(image_path):
    """Load image and convert to base64 string."""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def load_notes(notes_path):
    """Load speaker notes from text file."""
    if not notes_path.exists():
        return ""
    with open(notes_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def generate_prompt(slide_number, notes_text, duration):
    """
    Generate Sora 2 prompt combining slide context and notes.

    Args:
        slide_number: Slide index
        notes_text: Speaker notes content
        duration: Target video duration in seconds

    Returns:
        Prompt string for Sora 2
    """
    prompt_parts = [
        f"Generate a professional presentation video from this slide (slide {slide_number}).",
        "Create smooth, engaging camera movements that highlight key content.",
    ]

    if notes_text:
        # Incorporate notes as narration guidance
        notes_preview = notes_text[:200] + "..." if len(notes_text) > 200 else notes_text
        prompt_parts.append(f"Speaker notes context: {notes_preview}")
        prompt_parts.append("The video should convey the information from the speaker notes visually.")
    else:
        prompt_parts.append("The video should showcase the slide content in an engaging way.")

    prompt_parts.append(f"Style: Professional business presentation with subtle zoom and pan movements.")
    prompt_parts.append(f"Duration: {duration} seconds. Smooth transitions and professional appearance.")

    return " ".join(prompt_parts)


def submit_sora_job(endpoint, api_key, image_base64, prompt, duration, slide_number):
    """
    Submit a video generation job to Sora 2 API.

    Args:
        endpoint: Azure AI Foundry endpoint URL
        api_key: API authentication key
        image_base64: Base64-encoded slide image
        prompt: Generation prompt
        duration: Video duration in seconds
        slide_number: Slide index for tracking

    Returns:
        Job information dict with job_id and status
    """
    try:
        import requests
    except ImportError:
        print("Error: requests library required", file=sys.stderr)
        print("Install with: pip install requests", file=sys.stderr)
        sys.exit(1)

    # Mock mode for testing without API
    if os.getenv("SORA_MOCK_MODE") == "1":
        print(f"  [MOCK] Simulating job submission for slide {slide_number}")
        return {
            "job_id": f"mock-job-{slide_number:03d}",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

    # Prepare request
    url = f"{endpoint.rstrip('/')}/video/generate"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "mode": "image-to-video",
        "image": {
            "base64": image_base64
        },
        "prompt": prompt,
        "duration": duration,
        "resolution": "1920x1080",
        "fps": 30
    }

    # Submit job
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error submitting job for slide {slide_number}: {e}", file=sys.stderr)
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}", file=sys.stderr)
        return {
            "job_id": None,
            "status": "failed",
            "error": str(e)
        }


def calculate_duration(notes_text, default_duration=8):
    """
    Calculate video duration based on notes length.

    Args:
        notes_text: Speaker notes content
        default_duration: Default duration if no notes

    Returns:
        Duration in seconds (5-15 range)
    """
    if not notes_text:
        return default_duration

    # Estimate based on word count (roughly 150 words per minute speaking rate)
    words = len(notes_text.split())
    estimated_seconds = (words / 150) * 60

    # Clamp to reasonable range
    return max(5, min(15, int(estimated_seconds)))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate video clips using Sora 2 from slides and notes"
    )
    parser.add_argument(
        "--slides",
        required=True,
        help="Directory containing slide images"
    )
    parser.add_argument(
        "--notes",
        required=True,
        help="Directory containing notes text files"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for video clips"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=8,
        help="Default video duration per slide in seconds (default: 8)"
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
            print("Set via environment variables or command line arguments", file=sys.stderr)
            sys.exit(1)

    slides_dir = Path(args.slides)
    notes_dir = Path(args.notes)
    output_dir = Path(args.out)

    # Validate inputs
    if not slides_dir.exists():
        print(f"Error: Slides directory not found: {slides_dir}", file=sys.stderr)
        sys.exit(1)

    if not notes_dir.exists():
        print(f"Error: Notes directory not found: {notes_dir}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all slide images
    slides = sorted(slides_dir.glob("slide-*.png"))
    if not slides:
        print(f"Error: No slide images found in {slides_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(slides)} slides to process")
    print(f"Sora endpoint: {endpoint}")
    print(f"Output directory: {output_dir}")
    print()

    # Initialize manifest
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_slides": len(slides),
        "sora_config": {
            "endpoint": endpoint,
            "model": "sora-2",
            "default_duration": args.duration,
            "resolution": "1920x1080"
        },
        "slides": []
    }

    # Process each slide
    for i, slide_path in enumerate(slides, start=1):
        slide_number = i
        notes_path = notes_dir / f"slide-{slide_number:03d}.txt"

        print(f"Processing slide {slide_number}/{len(slides)}: {slide_path.name}")

        # Load notes
        notes_text = load_notes(notes_path)
        if notes_text:
            print(f"  - Notes: {len(notes_text)} characters")
        else:
            print(f"  - Notes: (none)")

        # Calculate duration based on notes
        duration = calculate_duration(notes_text, args.duration)
        print(f"  - Duration: {duration} seconds")

        # Generate prompt
        prompt = generate_prompt(slide_number, notes_text, duration)
        print(f"  - Prompt: {prompt[:100]}...")

        # Load image as base64
        print(f"  - Loading image...")
        image_base64 = load_image_as_base64(slide_path)

        # Submit job
        print(f"  - Submitting job to Sora 2...")
        job_info = submit_sora_job(
            endpoint, api_key, image_base64, prompt, duration, slide_number
        )

        # Add to manifest
        slide_entry = {
            "slide_number": slide_number,
            "image_path": str(slide_path),
            "notes_path": str(notes_path),
            "prompt": prompt,
            "duration": duration,
            "job_id": job_info.get("job_id"),
            "job_status": job_info.get("status"),
            "clip_path": str(output_dir / f"slide-{slide_number:03d}.mp4"),
            "submitted_at": job_info.get("created_at", datetime.utcnow().isoformat() + "Z")
        }

        if "error" in job_info:
            slide_entry["error"] = job_info["error"]

        manifest["slides"].append(slide_entry)

        if job_info.get("job_id"):
            print(f"  ✓ Job submitted: {job_info['job_id']}")
        else:
            print(f"  ✗ Job failed: {job_info.get('error', 'Unknown error')}")

        print()

        # Small delay to avoid rate limiting
        if i < len(slides):
            time.sleep(1)

    # Save manifest
    manifest_path = output_dir.parent / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest saved to: {manifest_path}")
    print(f"\nSubmitted {len(manifest['slides'])} jobs to Sora 2")

    # Summary
    successful = sum(1 for s in manifest['slides'] if s.get('job_id'))
    failed = len(manifest['slides']) - successful
    print(f"  - Successful: {successful}")
    print(f"  - Failed: {failed}")

    if failed > 0:
        print("\nSome jobs failed to submit. Check the manifest for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
