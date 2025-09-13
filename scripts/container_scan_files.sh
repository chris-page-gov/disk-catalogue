#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/container_scan_files.sh /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]
# Produces: output/files_<DRIVE_ID>_<YYYYMMDD>.csv

if [ $# -lt 2 ]; then
  echo "Usage: $0 /host/Volumes/DRIVE_NAME DRIVE_ID [output_dir]" >&2
  exit 1
fi

DRIVE_PATH="$1"
DRIVE_ID="$2"
OUT_DIR="${3:-output}"
DATE_STR="$(date +%Y%m%d)"
mkdir -p "$OUT_DIR"

# Generic file export: scan ALL files and capture basic metadata.
# We avoid extension filters to ensure comprehensive coverage.
set +e
exiftool -r -csv -fast3 -m \
  -FileName -Directory -FilePath -FileSize# -MIMEType -FileType \
  -FileInode -FileModifyDate -FileCreateDate \
  -CreateDate -ModifyDate -SourceFile \
  "$DRIVE_PATH" > "$OUT_DIR/files_${DRIVE_ID}_${DATE_STR}.csv"
code=$?
set -e
if [ "$code" -gt 1 ]; then
  echo "[files] ExifTool failed with exit code $code" >&2
  exit "$code"
fi

echo "[files] Wrote $OUT_DIR/files_${DRIVE_ID}_${DATE_STR}.csv"
