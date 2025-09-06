#!/usr/bin/env bash
set -euo pipefail

# Placeholder checksum enrichment script.
# Usage: ./scripts/enrich_checksums.sh photos_<DRIVE>_<DATE>.csv
# Adds an MD5 column by hashing file paths (NOT file contents) as a lightweight placeholder.
# Replace logic with real content hashing when ready (will be I/O intensive on HDDs).

if [ $# -lt 1 ]; then
  echo "Usage: $0 input_csv [output_csv]" >&2
  exit 1
fi

IN="$1"
OUT="${2:-${IN%.csv}_with_stub_checksums.csv}"

if [ ! -f "$IN" ]; then
  echo "Input file not found: $IN" >&2
  exit 1
fi

python - <<'PY'
import csv, hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, newline='') as r, open(dst, 'w', newline='') as w:
    reader = csv.DictReader(r)
    fieldnames = list(reader.fieldnames) + ["StubPathMD5"]
    writer = csv.DictWriter(w, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        h = hashlib.md5(row.get('FilePath','').encode('utf-8')).hexdigest()  # noqa: S324 (acceptable placeholder)
        row['StubPathMD5'] = h
        writer.writerow(row)
print(f"Wrote {dst}")
PY

