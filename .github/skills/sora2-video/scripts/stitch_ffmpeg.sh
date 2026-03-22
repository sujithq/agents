#!/bin/bash
#
# Stitch video clips into final MP4 using FFmpeg.
#
# Usage: stitch_ffmpeg.sh <clips_dir> <output_file>
#

set -e  # Exit on error

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <clips_dir> <output_file>" >&2
    echo "" >&2
    echo "Example: $0 output/video/clips output/video/final.mp4" >&2
    exit 1
fi

CLIPS_DIR="$1"
OUTPUT_FILE="$2"

# Validate clips directory
if [ ! -d "$CLIPS_DIR" ]; then
    echo "Error: Clips directory not found: $CLIPS_DIR" >&2
    exit 1
fi

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg not found. Install with: sudo apt-get install ffmpeg" >&2
    exit 1
fi

echo "Stitching video clips..."
echo "Clips directory: $CLIPS_DIR"
echo "Output file: $OUTPUT_FILE"
echo ""

# Find all clip files
CLIPS=($(ls "$CLIPS_DIR"/slide-*.mp4 2>/dev/null | sort))

if [ ${#CLIPS[@]} -eq 0 ]; then
    echo "Error: No video clips found in $CLIPS_DIR" >&2
    exit 1
fi

echo "Found ${#CLIPS[@]} video clips:"
for clip in "${CLIPS[@]}"; do
    echo "  - $(basename "$clip")"
done
echo ""

# Create temporary directory for concat list
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

CONCAT_LIST="$TMPDIR/concat_list.txt"

# Generate concat list file
echo "Creating concat list..."
for clip in "${CLIPS[@]}"; do
    # Convert to absolute path and escape for FFmpeg
    abs_path=$(realpath "$clip")
    echo "file '$abs_path'" >> "$CONCAT_LIST"
done

echo "Concat list:"
cat "$CONCAT_LIST"
echo ""

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Stitch videos using FFmpeg
echo "Running FFmpeg..."

# Try concat demuxer first (fastest, no re-encoding)
if ffmpeg -f concat -safe 0 -i "$CONCAT_LIST" -c copy "$OUTPUT_FILE.tmp" 2>/dev/null; then
    echo "✓ Concatenation successful (copy mode)"
    mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
else
    echo "Copy mode failed, trying with re-encoding..."

    # Fallback: re-encode with consistent settings
    if ffmpeg -f concat -safe 0 -i "$CONCAT_LIST" \
        -c:v libx264 -preset medium -crf 23 \
        -c:a aac -b:a 128k \
        -movflags +faststart \
        -y "$OUTPUT_FILE" 2>&1 | tail -20; then
        echo "✓ Concatenation successful (re-encode mode)"
    else
        echo "Error: FFmpeg concatenation failed" >&2
        exit 1
    fi
fi

# Verify output
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file was not created" >&2
    exit 1
fi

# Get video info
echo ""
echo "Final video created: $OUTPUT_FILE"
echo ""

if command -v ffprobe &> /dev/null; then
    echo "Video information:"
    ffprobe -v quiet -print_format json -show_format -show_streams "$OUTPUT_FILE" | \
        grep -E '"duration"|"size"|"width"|"height"|"codec_name"' | head -10
else
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "File size: $FILE_SIZE"
fi

echo ""
echo "✓ Stitching complete!"
