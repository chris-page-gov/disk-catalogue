#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/container_scan_photos.sh /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]
# Produces: output/photos_<DRIVE_ID>_<YYYYMMDD>.csv

if [ $# -lt 2 ]; then
  echo "Usage: $0 /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]" >&2
  exit 1
fi

DRIVE_PATH="$1"
DRIVE_ID="$2"
OUT_DIR="${3:-output}"
DATE_STR="$(date +%Y%m%d)"
mkdir -p "$OUT_DIR"

# ExifTool fast recursive photo metadata export
exiftool -r -csv -fast3 \
  -ext arw -ext arq -ext srx -ext sr2 -ext cr2 -ext raf -ext nef -ext dng \
  -ext jpg -ext jpeg -ext tiff -ext tif -ext png -ext heic -ext heif \
  -FileName -Directory -FilePath -FileSize# -MIMEType \
  -CreateDate -DateTimeOriginal -ModifyDate \
  -Model -Make -LensModel -LensID -FNumber -ShutterSpeed -ISO -FocalLength \
  -ImageWidth -ImageHeight -Orientation \
  -GPSLatitude -GPSLongitude \
  -Rating -Label -XMP-dc:Title -Keywords -HierarchicalSubject \
  -SourceFile \
  "$DRIVE_PATH" > "$OUT_DIR/photos_${DRIVE_ID}_${DATE_STR}.csv"

echo "[photos] Wrote $OUT_DIR/photos_${DRIVE_ID}_${DATE_STR}.csv"
