#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/container_extract_videos_from_list.sh PATHS_LIST DRIVE_ID [output_dir]
# PATHS_LIST is a file containing one absolute path per line

if [ $# -lt 2 ]; then
  echo "Usage: $0 PATHS_LIST DRIVE_ID [output_dir]" >&2
  exit 1
fi

LIST_FILE="$1"
DRIVE_ID="$2"
OUT_DIR="${3:-output}"
DATE_STR="$(date +%Y%m%d)"
mkdir -p "$OUT_DIR"

set +e
exiftool -csv -fast3 -m \
  -ext mp4 -ext mov -ext mxf -ext avi -ext mpg -ext mpeg -ext mts -ext mkv \
  -FileName -Directory -FilePath -FileSize# -MIMEType \
  -Duration -TrackCreateDate -MediaCreateDate -CreateDate \
  -HandlerDescription -CompressorName -VideoCodec -VideoFrameRate -VideoFrameCount \
  -ImageWidth -ImageHeight -AudioFormat -AudioChannels -AudioSampleRate -BitRate \
  -SourceFile \
  -@ "$LIST_FILE" > "$OUT_DIR/videos_${DRIVE_ID}_${DATE_STR}.csv"
code=$?
set -e
if [ "$code" -gt 1 ]; then
  echo "[videos-from-list] ExifTool failed with exit code $code" >&2
  exit "$code"
fi

echo "[videos-from-list] Wrote $OUT_DIR/videos_${DRIVE_ID}_${DATE_STR}.csv"

