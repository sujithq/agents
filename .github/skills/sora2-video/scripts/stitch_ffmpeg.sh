#!/usr/bin/env bash
# stitch_ffmpeg.sh
# ----------------
# Concatenate per-slide MP4 clips (in lexicographic order) into a single
# final.mp4 using ffmpeg.
#
# Usage:
#   bash stitch_ffmpeg.sh <clips-dir> <output-mp4>
#
# Example:
#   bash stitch_ffmpeg.sh output/video/clips output/video/final.mp4

set -euo pipefail

CLIPS_DIR="${1:?Usage: stitch_ffmpeg.sh <clips-dir> <output-mp4>}"
OUTPUT_MP4="${2:?Usage: stitch_ffmpeg.sh <clips-dir> <output-mp4>}"

if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg is not installed or not on PATH." >&2
    exit 1
fi

# Resolve to absolute paths
CLIPS_DIR="$(realpath "${CLIPS_DIR}")"
OUTPUT_DIR="$(dirname "$(realpath -m "${OUTPUT_MP4}")")"
mkdir -p "${OUTPUT_DIR}"

# Build a file list for ffmpeg concat demuxer
CONCAT_LIST="$(mktemp /tmp/ffmpeg_concat_XXXXXX.txt)"
trap 'rm -f "${CONCAT_LIST}"' EXIT

shopt -s nullglob
CLIPS=("${CLIPS_DIR}"/slide-*.mp4)
shopt -u nullglob

if [[ ${#CLIPS[@]} -eq 0 ]]; then
    echo "ERROR: No slide-NNN.mp4 files found in ${CLIPS_DIR}" >&2
    exit 1
fi

# Sort clips lexicographically (slide-001.mp4 < slide-002.mp4 …)
IFS=$'\n' SORTED_CLIPS=($(printf '%s\n' "${CLIPS[@]}" | sort))
unset IFS

echo "Stitching ${#SORTED_CLIPS[@]} clip(s) → ${OUTPUT_MP4}"

for clip in "${SORTED_CLIPS[@]}"; do
    echo "file '${clip}'" >> "${CONCAT_LIST}"
done

ffmpeg -y \
    -f concat \
    -safe 0 \
    -i "${CONCAT_LIST}" \
    -c copy \
    "${OUTPUT_MP4}"

echo "Done: ${OUTPUT_MP4}"
