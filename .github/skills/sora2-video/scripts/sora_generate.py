#!/usr/bin/env python3
"""
Submit Sora 2 image-to-video jobs for each slide.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import requests


@dataclass
class SlideJob:
    slide: int
    image: str
    notes_file: Optional[str]
    prompt: str
    job_id: str
    status: str


def read_notes(notes_file: Optional[Path]) -> str:
    if notes_file and notes_file.exists():
        return notes_file.read_text(encoding="utf-8").strip()
    return ""


def build_prompt(notes_text: str, fallback: str) -> str:
    if notes_text:
        return notes_text
    return fallback


def b64_image(image_path: Path) -> str:
    data = image_path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def submit_job(
    session: requests.Session,
    base_url: str,
    deployment: str,
    api_version: str,
    api_key: str,
    image_path: Path,
    prompt: str,
    duration_seconds: int,
    aspect_ratio: str,
) -> dict:
    url = f"{base_url.rstrip('/')}/openai/deployments/{deployment}/jobs?api-version={api_version}"
    payload = {
        "task": "image-to-video",
        "input_image": b64_image(image_path),
        "prompt": prompt,
        "duration": duration_seconds,
        "aspect_ratio": aspect_ratio,
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    response = session.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit Sora 2 image-to-video jobs for each slide."
    )
    parser.add_argument(
        "--slides",
        required=True,
        type=Path,
        help="Directory containing slide PNGs.",
    )
    parser.add_argument(
        "--notes",
        required=True,
        type=Path,
        help="Directory containing per-slide notes (optional per slide).",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Directory where manifest + clips will live (e.g., output/video).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to manifest.json (default: <out>/manifest.json).",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("SORA_ENDPOINT"),
        help="Base endpoint for Azure AI Foundry Sora.",
    )
    parser.add_argument(
        "--deployment",
        default=os.environ.get("SORA_DEPLOYMENT"),
        help="Sora deployment name.",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=os.environ.get("SORA_API_KEY"),
        help="API key for the Sora endpoint.",
    )
    parser.add_argument(
        "--api-version",
        default=os.environ.get("SORA_API_VERSION", "2024-10-21-preview"),
        help="API version for the Sora endpoint.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=6,
        help="Duration of each clip in seconds.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="16:9",
        help="Aspect ratio to request from Sora.",
    )
    parser.add_argument(
        "--fallback-prompt",
        default="Generate a smooth, realistic video that matches the provided slide image and keeps on-screen text sharp.",
        help="Used when a slide has no notes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.endpoint or not args.api_key or not args.deployment:
        raise SystemExit("Missing endpoint/deployment/api-key for Sora requests.")

    slides_dir = args.slides.resolve()
    notes_dir = args.notes.resolve()
    out_dir = args.out.resolve()
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = args.manifest or (out_dir / "manifest.json")

    slide_files = sorted(slides_dir.glob("slide-*.png"))
    if not slide_files:
        raise SystemExit(f"No slides found in {slides_dir}")

    session = requests.Session()
    jobs: list[SlideJob] = []

    for slide_path in slide_files:
        slide_num = int(slide_path.stem.split("-")[-1])
        notes_file = notes_dir / f"slide-{slide_num:03d}.txt"
        notes_text = read_notes(notes_file if notes_file.exists() else None)
        prompt = build_prompt(notes_text, args.fallback_prompt)
        response = submit_job(
            session=session,
            base_url=args.endpoint,
            deployment=args.deployment,
            api_version=args.api_version,
            api_key=args.api_key,
            image_path=slide_path,
            prompt=prompt,
            duration_seconds=args.duration,
            aspect_ratio=args.aspect_ratio,
        )
        job_id = response.get("id") or response.get("job_id")
        if not job_id:
            raise SystemExit(f"Did not receive job id for slide {slide_num}")
        jobs.append(
            SlideJob(
                slide=slide_num,
                image=str(slide_path),
                notes_file=str(notes_file) if notes_file.exists() else None,
                prompt=prompt,
                job_id=job_id,
                status=response.get("status", "submitted"),
            )
        )

    manifest = {
        "endpoint": args.endpoint,
        "deployment": args.deployment,
        "api_version": args.api_version,
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "slides": [asdict(job) for job in jobs],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
