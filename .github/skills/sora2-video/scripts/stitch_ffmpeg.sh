#!/usr/bin/env bash
set -euo pipefail

CLIPS_DIR="${1:-output/video/clips}"
OUT="${2:-output/video/final.mp4}"

if [ ! -d "$CLIPS_DIR" ]; then
  echo "Clips directory not found: $CLIPS_DIR" >&2
  exit 1
fi

mapfile -t clips < <(ls "$CLIPS_DIR"/slide-*.mp4 2>/dev/null | sort)

if [ "${#clips[@]}" -eq 0 ]; then
  echo "No clips found in $CLIPS_DIR" >&2
  exit 1
fi

tmp_list="$(mktemp)"
trap 'rm -f "$tmp_list"' EXIT

for clip in "${clips[@]}"; do
  printf "file '%s'\n" "$clip" >>"$tmp_list"
done

ffmpeg -y -f concat -safe 0 -i "$tmp_list" -c copy "$OUT"
echo "Stitched video written to $OUT"
