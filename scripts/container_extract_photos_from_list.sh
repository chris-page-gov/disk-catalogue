#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/container_extract_photos_from_list.sh PATHS_LIST DRIVE_ID [output_dir]
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
  -ext arw -ext arq -ext srx -ext sr2 -ext cr2 -ext raf -ext nef -ext dng \
  -ext jpg -ext jpeg -ext tiff -ext tif -ext png -ext heic -ext heif \
  -FileName -Directory -FilePath -FileSize# -MIMEType \
  -CreateDate -DateTimeOriginal -ModifyDate \
  -Model -Make -LensModel -LensID -FNumber -ShutterSpeed -ISO -FocalLength \
  -ImageWidth -ImageHeight -Orientation \
  -GPSLatitude -GPSLongitude \
  -Rating -Label -XMP-dc:Title -Keywords -HierarchicalSubject \
  -SourceFile \
  -@ "$LIST_FILE" > "$OUT_DIR/photos_${DRIVE_ID}_${DATE_STR}.csv"
code=$?
set -e
if [ "$code" -gt 1 ]; then
  echo "[photos-from-list] ExifTool failed with exit code $code" >&2
  exit "$code"
fi

echo "[photos-from-list] Wrote $OUT_DIR/photos_${DRIVE_ID}_${DATE_STR}.csv"

