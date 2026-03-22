#!/usr/bin/env python3
"""
sora_generate.py
----------------
Submit one Sora 2 image→video job per slide to Azure AI Foundry and write a
manifest.json tracking each job.

The script reads slide PNGs and corresponding notes TXT files, builds a prompt
for each slide (notes text + slide number), encodes the slide image as Base64,
and calls the Sora 2 Jobs API (async).

Environment variables (required):
    SORA_ENDPOINT   – Azure AI Foundry endpoint, e.g. https://<resource>.openai.azure.com/
    SORA_API_KEY    – API key for the Sora 2 deployment
    SORA_DEPLOYMENT – Deployment name (default: "sora")

Usage:
    python sora_generate.py \
        --slides-dir output/slides \
        --notes-dir  output/notes \
        --manifest   output/video/manifest.json \
        [--duration  5] \
        [--pptx      input/deck.pptx]
"""

import argparse
import base64
import datetime
import json
import os
import sys
from pathlib import Path

import requests


SORA_API_VERSION = "2025-04-01-preview"


def get_env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        print(f"ERROR: Environment variable '{name}' is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def build_prompt(notes: str, slide_num: int) -> str:
    """Construct the Sora prompt from speaker notes."""
    if notes.strip():
        return notes.strip()
    return f"A professional presentation slide {slide_num} with smooth motion and subtle animation."


def submit_job(
    endpoint: str,
    api_key: str,
    deployment: str,
    slide_num: int,
    slide_png: Path,
    notes_txt: Path,
    duration: int,
) -> dict:
    """Submit a single Sora 2 image→video job and return the response JSON."""
    # Read and encode the slide image
    image_bytes = slide_png.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = "image/png"

    # Read speaker notes
    notes = notes_txt.read_text(encoding="utf-8") if notes_txt.exists() else ""
    prompt = build_prompt(notes, slide_num)

    url = (
        f"{endpoint.rstrip('/')}/openai/v1/video/generations/jobs"
        f"?api-version={SORA_API_VERSION}"
    )
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": deployment,
        "prompt": prompt,
        "duration_seconds": duration,
        "image": {
            "type": "base64",
            "media_type": mime_type,
            "data": image_b64,
        },
        "n_variants": 1,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"Sora API error for slide {slide_num}: "
            f"{response.status_code} {response.text}"
        )
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit Sora 2 image→video jobs for each slide."
    )
    parser.add_argument("--slides-dir", required=True, help="Directory containing slide-NNN.png files")
    parser.add_argument("--notes-dir", required=True, help="Directory containing slide-NNN.txt files")
    parser.add_argument("--manifest", required=True, help="Path to write manifest.json")
    parser.add_argument("--duration", type=int, default=5, help="Video duration per slide in seconds (default: 5)")
    parser.add_argument("--pptx", default="", help="Original PPTX path (recorded in manifest)")
    args = parser.parse_args()

    endpoint = get_env("SORA_ENDPOINT")
    api_key = get_env("SORA_API_KEY")
    deployment = os.environ.get("SORA_DEPLOYMENT", "sora")

    slides_dir = Path(args.slides_dir)
    notes_dir = Path(args.notes_dir)
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    slide_pngs = sorted(slides_dir.glob("slide-*.png"))
    if not slide_pngs:
        print(f"ERROR: No slide PNG files found in {slides_dir}", file=sys.stderr)
        sys.exit(1)

    manifest = {
        "pptx": args.pptx,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "slides": [],
    }

    for png_path in slide_pngs:
        # Extract slide number from filename (slide-001.png → 1)
        stem = png_path.stem  # e.g. "slide-001"
        slide_num = int(stem.split("-")[1])

        notes_path = notes_dir / f"slide-{slide_num:03d}.txt"
        notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
        prompt = build_prompt(notes, slide_num)

        print(f"  Submitting job for slide {slide_num:03d} …")
        try:
            job_response = submit_job(
                endpoint=endpoint,
                api_key=api_key,
                deployment=deployment,
                slide_num=slide_num,
                slide_png=png_path,
                notes_txt=notes_path,
                duration=args.duration,
            )
        except RuntimeError as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            job_response = {"id": None, "status": "failed"}

        job_id = job_response.get("id") or job_response.get("job_id", "")
        status = job_response.get("status", "submitted")

        manifest["slides"].append(
            {
                "index": slide_num,
                "slide_image": str(png_path),
                "notes_file": str(notes_path),
                "prompt": prompt,
                "job_id": job_id,
                "clip": f"output/video/clips/slide-{slide_num:03d}.mp4",
                "status": status,
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
