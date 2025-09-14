# Disk Catalogue Schema Reference

This document describes the DuckDB tables and views produced by the disk catalogue
pipeline. It lists column names, types, and brief explanations. Any columns not
explicitly described are carried through directly from the ExifTool CSV outputs.

Note: Raw CSV schemas can vary slightly across scans and drives depending on what
metadata ExifTool finds. The derived views add consistent identifiers for querying.

## How It’s Built
- Raw CSVs load into `*_raw` tables (`files_raw`, `photos_raw`, `videos_raw`).
- Derived views (`files`, `photos`, `videos`) add:
  - `Drive` — the volume label parsed from `SourceFile`.
  - `RelativePath` — `SourceFile` minus `/host/Volumes/<Drive>/`.
  - `RelativeDirectory` — directory portion of `RelativePath`.
  - `FileExt` — lowercased extension without dot.
  - `FileKey` — stable hash of `(Drive, RelativePath, FileSize#)`.
- Operational tables track ingests and scans: `ingested_files`, `drives`, `drive_scans`.

## Tables

### drives
Drive metadata snapshot from the manifest and last scan.

| Column | Type | Description |
|---|---|---|
| `drive_label` | `TEXT` | Primary key; human-readable drive label from the manifest. |
| `mac_mount` | `TEXT` | Platform mount string from the manifest (e.g., `mac:/Volumes/Ext-10`). |
| `volume_uuid` | `TEXT` | Volume UUID from the manifest, if provided. |
| `serial_number` | `TEXT` | Drive serial number from the manifest, if provided. |
| `notes` | `TEXT` | Free-form notes from the manifest. |
| `last_scanned` | `TIMESTAMP` | Timestamp of the last scan recorded. |

### drive_scans
History of scan runs per drive (start/end, status, CSVs, row counts).

| Column | Type | Description |
|---|---|---|
| `drive_label` | `TEXT` | Drive label used for the scan. |
| `started_at` | `TIMESTAMP` | Scan start time. |
| `ended_at` | `TIMESTAMP` | Scan end time. |
| `status` | `TEXT` | Scan status (`ok`, `skipped`, or error state on failure). |
| `files_csv` | `TEXT` | Path to the files CSV used/created for this run. |
| `photos_csv` | `TEXT` | Path to the photos CSV used/created for this run. |
| `videos_csv` | `TEXT` | Path to the videos CSV used/created for this run. |
| `files_rows` | `BIGINT` | Row count in the files CSV at ingest time. |
| `photos_rows` | `BIGINT` | Row count in the photos CSV at ingest time. |
| `videos_rows` | `BIGINT` | Row count in the videos CSV at ingest time. |

### ingested_files
Ingestion log of CSVs already loaded (idempotency control).

| Column | Type | Description |
|---|---|---|
| `file_path` | `TEXT` | Absolute path to a previously ingested CSV file. Primary key. |
| `ingested_at` | `TIMESTAMP` | Timestamp when this CSV was recorded as ingested. |

### files_raw
Raw ExifTool scan of all files. Columns mirror the CSV headers; the exact set can vary by scan.

Common columns (others are ExifTool pass-through):

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute path to the scanned file (container path if in dev container). |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName` combined; may duplicate `SourceFile`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |

### photos_raw
Raw ExifTool scan for photo files. Same shape as `files_raw` plus photo metadata when available.

Common columns:

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute file path. |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |
| `Model` | `TEXT` | Camera model (if embedded). |
| `Make` | `TEXT` | Camera manufacturer (if embedded). |
| `LensModel` | `TEXT` | Lens model (if embedded). |
| `LensID` | `TEXT` | Lens identifier (if embedded). |
| `FNumber` | `DOUBLE` | Aperture f‑number. |
| `ShutterSpeed` | `DOUBLE` | Exposure time/shutter speed. |
| `ISO` | `BIGINT` | ISO sensitivity. |
| `FocalLength` | `DOUBLE` | Focal length. |
| `ImageWidth` | `BIGINT` | Pixel width. |
| `ImageHeight` | `BIGINT` | Pixel height. |
| `Orientation` | `TEXT` | Image orientation. |
| `GPSLatitude` | `DOUBLE` | Latitude (decimal degrees). |
| `GPSLongitude` | `DOUBLE` | Longitude (decimal degrees). |
| `Rating` | `BIGINT` | User rating (if embedded). |
| `Label` | `TEXT` | User label/flag (if embedded). |
| `XMP-dc:Title` | `TEXT` | XMP title (if embedded). |
| `Keywords` | `TEXT` | Flat keywords. |
| `HierarchicalSubject` | `TEXT` | Hierarchical keywords. |
| `DateTimeOriginal` | `TIMESTAMP` | Original capture time (if embedded). |
| `CreateDate` | `TIMESTAMP` | File or media creation time. |
| `ModifyDate` | `TIMESTAMP` | Last modification time. |

### videos_raw
Raw ExifTool scan for video files. Same shape as `files_raw` plus video metadata when available.

Common columns:

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute file path. |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |
| `Duration` | `DOUBLE` | Media duration (seconds). |
| `TrackCreateDate` | `TIMESTAMP` | Track creation timestamp. |
| `MediaCreateDate` | `TIMESTAMP` | Media creation timestamp. |
| `CreateDate` | `TIMESTAMP` | File creation timestamp. |
| `HandlerDescription` | `TEXT` | Media handler description. |
| `CompressorName` | `TEXT` | Compressor/codec name. |
| `VideoCodec` | `TEXT` | Video codec. |
| `VideoFrameRate` | `DOUBLE` | Frame rate (fps). |
| `VideoFrameCount` | `BIGINT` | Frame count. |
| `ImageWidth` | `BIGINT` | Frame width (pixels). |
| `ImageHeight` | `BIGINT` | Frame height (pixels). |
| `AudioFormat` | `TEXT` | Audio format. |
| `AudioChannels` | `BIGINT` | Audio channel count. |
| `AudioSampleRate` | `BIGINT` | Audio sample rate (Hz). |
| `BitRate` | `BIGINT` | Overall bit rate (bps). |

## Views

The views include all columns from their corresponding `*_raw` table, plus the derived columns below.

### files
All files with derived identifiers and drive/path parsing. This view includes all columns from `files_raw` plus the derived columns below.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute path to the scanned file (container path if in dev container). |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName` combined; may duplicate `SourceFile`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |
| `Drive` | `TEXT` | Volume label parsed from `SourceFile` (`/host/Volumes/<Drive>/...`). |
| `RelativePath` | `TEXT` | Path within the drive root (no leading `/host/Volumes/<Drive>/`). |
| `RelativeDirectory` | `TEXT` | Directory portion of `RelativePath`. |
| `FileExt` | `TEXT` | Lowercased extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: `hash(Drive, RelativePath, FileSize#)`. |
| … | … | Additional ExifTool columns may be present depending on scans. |

### photos
Photos with derived identifiers and drive/path parsing. This view includes all columns from `photos_raw` plus the derived columns below.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute file path. |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |
| `Model` | `TEXT` | Camera model (if embedded). |
| `Make` | `TEXT` | Camera manufacturer (if embedded). |
| `LensModel` | `TEXT` | Lens model (if embedded). |
| `LensID` | `TEXT` | Lens identifier (if embedded). |
| `FNumber` | `DOUBLE` | Aperture f‑number. |
| `ShutterSpeed` | `DOUBLE` | Exposure time/shutter speed. |
| `ISO` | `BIGINT` | ISO sensitivity. |
| `FocalLength` | `DOUBLE` | Focal length. |
| `ImageWidth` | `BIGINT` | Pixel width. |
| `ImageHeight` | `BIGINT` | Pixel height. |
| `Orientation` | `TEXT` | Image orientation. |
| `GPSLatitude` | `DOUBLE` | Latitude (decimal degrees). |
| `GPSLongitude` | `DOUBLE` | Longitude (decimal degrees). |
| `Rating` | `BIGINT` | User rating (if embedded). |
| `Label` | `TEXT` | User label/flag (if embedded). |
| `XMP-dc:Title` | `TEXT` | XMP title (if embedded). |
| `Keywords` | `TEXT` | Flat keywords. |
| `HierarchicalSubject` | `TEXT` | Hierarchical keywords. |
| `DateTimeOriginal` | `TIMESTAMP` | Original capture time (if embedded). |
| `CreateDate` | `TIMESTAMP` | File or media creation time. |
| `ModifyDate` | `TIMESTAMP` | Last modification time. |
| `Drive` | `TEXT` | Volume label parsed from `SourceFile`. |
| `RelativePath` | `TEXT` | Path within the drive root. |
| `RelativeDirectory` | `TEXT` | Directory portion of `RelativePath`. |
| `FileExt` | `TEXT` | Lowercased extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: `hash(Drive, RelativePath, FileSize#)`. |
| … | … | Additional ExifTool columns may be present depending on scans. |

### videos
Videos with derived identifiers and drive/path parsing. This view includes all columns from `videos_raw` plus the derived columns below.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `TEXT` | Absolute file path. |
| `FileName` | `TEXT` | Base name with extension. |
| `Directory` | `TEXT` | Directory portion of the path. |
| `FilePath` | `TEXT` | `Directory` + `FileName`. |
| `FileSize#` | `BIGINT` | File size in bytes. |
| `MIMEType` | `TEXT` | Detected MIME type. |
| `Duration` | `DOUBLE` | Media duration (seconds). |
| `TrackCreateDate` | `TIMESTAMP` | Track creation timestamp. |
| `MediaCreateDate` | `TIMESTAMP` | Media creation timestamp. |
| `CreateDate` | `TIMESTAMP` | File creation timestamp. |
| `HandlerDescription` | `TEXT` | Media handler description. |
| `CompressorName` | `TEXT` | Compressor/codec name. |
| `VideoCodec` | `TEXT` | Video codec. |
| `VideoFrameRate` | `DOUBLE` | Frame rate (fps). |
| `VideoFrameCount` | `BIGINT` | Frame count. |
| `ImageWidth` | `BIGINT` | Frame width (pixels). |
| `ImageHeight` | `BIGINT` | Frame height (pixels). |
| `AudioFormat` | `TEXT` | Audio format. |
| `AudioChannels` | `BIGINT` | Audio channel count. |
| `AudioSampleRate` | `BIGINT` | Audio sample rate (Hz). |
| `BitRate` | `BIGINT` | Overall bit rate (bps). |
| `Drive` | `TEXT` | Volume label parsed from `SourceFile`. |
| `RelativePath` | `TEXT` | Path within the drive root. |
| `RelativeDirectory` | `TEXT` | Directory portion of `RelativePath`. |
| `FileExt` | `TEXT` | Lowercased extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: `hash(Drive, RelativePath, FileSize#)`. |
| … | … | Additional ExifTool columns may be present depending on scans. |

## Regenerating This Reference

To generate an up-to-date schema reference from your actual database (recommended):

```
python scripts/generate_schema_reference.py --db catalogue.duckdb --out SCHEMA_REFERENCE.md
```

This will inspect the live DuckDB, enumerate tables/views, and include the full
set of columns and their DuckDB types for your dataset.
