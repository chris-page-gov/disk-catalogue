#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/container_scan_videos.sh /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]
# Produces: output/videos_<DRIVE_ID>_<YYYYMMDD>.csv

if [ $# -lt 2 ]; then
  echo "Usage: $0 /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]" >&2
  exit 1
fi

DRIVE_PATH="$1"
DRIVE_ID="$2"
OUT_DIR="${3:-output}"
DATE_STR="$(date +%Y%m%d)"
mkdir -p "$OUT_DIR"

# Video metadata export (core technical + container usage)
exiftool -r -csv -fast3 \
  -ext mp4 -ext mov -ext mxf -ext avi -ext mpg -ext mpeg -ext mts -ext mkv \
  -FileName -Directory -FilePath -FileSize# -MIMEType \
  -Duration -TrackCreateDate -MediaCreateDate -CreateDate \
  -HandlerDescription -CompressorName -VideoCodec -VideoFrameRate -VideoFrameCount \
  -ImageWidth -ImageHeight -AudioFormat -AudioChannels -AudioSampleRate -BitRate \
  -SourceFile \
  "$DRIVE_PATH" > "$OUT_DIR/videos_${DRIVE_ID}_${DATE_STR}.csv"

echo "[videos] Wrote $OUT_DIR/videos_${DRIVE_ID}_${DATE_STR}.csv"
