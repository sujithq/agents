#!/usr/bin/env python3
"""
Poll Sora 2 jobs until completion and download resulting clips.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll Sora jobs referenced in a manifest until they complete."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to manifest.json created during submission.",
    )
    parser.add_argument(
        "--clips",
        type=Path,
        help="Directory to write downloaded clips (default: sibling clips dir to manifest).",
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
        "--interval",
        type=int,
        default=20,
        help="Seconds to wait between polls.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=90,
        help="Maximum poll attempts before giving up.",
    )
    return parser.parse_args()


def fetch_job(
    session: requests.Session,
    base_url: str,
    deployment: str,
    api_version: str,
    api_key: str,
    job_id: str,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/openai/deployments/{deployment}/jobs/{job_id}?api-version={api_version}"
    response = session.get(url, headers={"api-key": api_key}, timeout=30)
    response.raise_for_status()
    return response.json()


def first_video_url(payload: Dict[str, Any]) -> Optional[str]:
    candidates = []
    for key in ("output", "outputs", "result", "results"):
        node = payload.get(key)
        if isinstance(node, list):
            candidates.extend(node)
        elif isinstance(node, dict):
            candidates.append(node)
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if "url" in item:
            return item["url"]
        asset = item.get("asset") or item.get("video")
        if isinstance(asset, dict) and "url" in asset:
            return asset["url"]
    return None


def download_file(session: requests.Session, url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)


def save_manifest(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not args.endpoint or not args.api_key or not args.deployment:
        raise SystemExit("Missing endpoint/deployment/api-key for Sora requests.")

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    clips_dir = args.clips or (manifest_path.parent / "clips")
    clips_dir = clips_dir.resolve()
    session = requests.Session()

    pending = {entry["job_id"] for entry in manifest.get("slides", [])}
    attempt = 0
    while pending and attempt < args.max_attempts:
        attempt += 1
        print(f"Poll attempt {attempt} for {len(pending)} job(s)...")
        completed_now = set()
        for entry in manifest.get("slides", []):
            job_id = entry["job_id"]
            if job_id not in pending:
                continue
            payload = fetch_job(
                session=session,
                base_url=args.endpoint,
                deployment=args.deployment,
                api_version=args.api_version,
                api_key=args.api_key,
                job_id=job_id,
            )
            status = payload.get("status", "").lower()
            entry["status"] = status or "unknown"
            if status in {"succeeded", "completed"}:
                video_url = first_video_url(payload)
                if not video_url:
                    raise SystemExit(f"No video URL returned for job {job_id}")
                slide_num = entry.get("slide") or entry.get("slide_num")
                filename = f"slide-{int(slide_num):03d}.mp4" if slide_num else f"{job_id}.mp4"
                dest = clips_dir / filename
                download_file(session, video_url, dest)
                entry["clip"] = str(dest)
                entry["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                completed_now.add(job_id)
            elif status in {"failed", "canceled"}:
                entry["error"] = payload
                completed_now.add(job_id)
        pending -= completed_now
        save_manifest(manifest_path, manifest)
        if pending:
            time.sleep(args.interval)

    if pending:
        raise SystemExit(f"Polling ended with incomplete jobs: {pending}")
    print("All jobs finished. Manifest updated.")


if __name__ == "__main__":
    main()
