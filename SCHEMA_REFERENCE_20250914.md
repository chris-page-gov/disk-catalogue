# Disk Catalogue Schema Reference

This document describes the tables and views in the DuckDB catalogue, including column types and brief explanations. Columns not explicitly described are carried through from the ExifTool CSV outputs.

## How It’s Built

- Raw CSVs from scans load into *_raw tables (schema auto‑detected).
- Views (files/photos/videos) add derived identifiers: Drive, RelativePath, RelativeDirectory, FileExt, FileKey.
- Operational tables track ingests and scans: ingested_files, drives, drive_scans.

## Tables

### drives

Drive metadata snapshot from manifest (label, mounts, ids, notes).

| Column | Type | Description |
|---|---|---|
| `drive_label` | `VARCHAR` | Raw ExifTool field or operational field. |
| `mac_mount` | `VARCHAR` | Raw ExifTool field or operational field. |
| `volume_uuid` | `VARCHAR` | Raw ExifTool field or operational field. |
| `serial_number` | `VARCHAR` | Raw ExifTool field or operational field. |
| `notes` | `VARCHAR` | Raw ExifTool field or operational field. |
| `last_scanned` | `TIMESTAMP` | Raw ExifTool field or operational field. |

### drive_scans

History of scan runs per drive (start/end, status, CSVs, row counts).

| Column | Type | Description |
|---|---|---|
| `drive_label` | `VARCHAR` | Raw ExifTool field or operational field. |
| `started_at` | `TIMESTAMP` | Raw ExifTool field or operational field. |
| `ended_at` | `TIMESTAMP` | Raw ExifTool field or operational field. |
| `status` | `VARCHAR` | Raw ExifTool field or operational field. |
| `files_csv` | `VARCHAR` | Raw ExifTool field or operational field. |
| `photos_csv` | `VARCHAR` | Raw ExifTool field or operational field. |
| `videos_csv` | `VARCHAR` | Raw ExifTool field or operational field. |
| `files_rows` | `BIGINT` | Raw ExifTool field or operational field. |
| `photos_rows` | `BIGINT` | Raw ExifTool field or operational field. |
| `videos_rows` | `BIGINT` | Raw ExifTool field or operational field. |

### ingested_files

Ingestion log of CSVs already loaded (idempotency).

| Column | Type | Description |
|---|---|---|
| `file_path` | `VARCHAR` | Raw ExifTool field or operational field. |
| `ingested_at` | `TIMESTAMP` | Raw ExifTool field or operational field. |

### files_raw

Raw ExifTool scan of all files; columns mirror CSV headers.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or operational field. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |
| `FileType` | `VARCHAR` | Raw ExifTool field or operational field. |
| `FileModifyDate` | `VARCHAR` | Raw ExifTool field or operational field. |

### photos_raw

Raw ExifTool scan for photo files; columns mirror CSV headers.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or operational field. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |

### videos_raw

Raw ExifTool scan for video files; columns mirror CSV headers.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or operational field. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |

## Views

### files

All files with derived identifiers and drive/path parsing.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or derived column. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |
| `FileType` | `VARCHAR` | Raw ExifTool field or derived column. |
| `FileModifyDate` | `VARCHAR` | Raw ExifTool field or derived column. |
| `Drive` | `VARCHAR` | Volume label parsed from SourceFile (/host/Volumes/<Drive>/...). |
| `RelativePath` | `VARCHAR` | Path within the drive root (SourceFile without the /host/Volumes/<Drive>/ prefix). |
| `RelativeDirectory` | `VARCHAR` | Directory component of RelativePath (no leading slash). |
| `FileExt` | `VARCHAR` | Lowercased file extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: hash(Drive, RelativePath, FileSize#). |

### photos

Photos with derived identifiers and drive/path parsing.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or derived column. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |
| `Drive` | `VARCHAR` | Volume label parsed from SourceFile (/host/Volumes/<Drive>/...). |
| `RelativePath` | `VARCHAR` | Path within the drive root (SourceFile without the /host/Volumes/<Drive>/ prefix). |
| `RelativeDirectory` | `VARCHAR` | Directory component of RelativePath (no leading slash). |
| `FileExt` | `VARCHAR` | Lowercased file extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: hash(Drive, RelativePath, FileSize#). |

### videos

Videos with derived identifiers and drive/path parsing.

| Column | Type | Description |
|---|---|---|
| `SourceFile` | `VARCHAR` | Absolute path to the scanned file (container path if inside devcontainer). |
| `FileName` | `VARCHAR` | Base name of the file including extension. |
| `Directory` | `VARCHAR` | Directory portion of the SourceFile path. |
| `FilePath` | `VARCHAR` | Raw ExifTool field or derived column. |
| `FileSize#` | `BIGINT` | File size in bytes (numeric). |
| `MIMEType` | `VARCHAR` | Detected MIME type of the file. |
| `Drive` | `VARCHAR` | Volume label parsed from SourceFile (/host/Volumes/<Drive>/...). |
| `RelativePath` | `VARCHAR` | Path within the drive root (SourceFile without the /host/Volumes/<Drive>/ prefix). |
| `RelativeDirectory` | `VARCHAR` | Directory component of RelativePath (no leading slash). |
| `FileExt` | `VARCHAR` | Lowercased file extension without the dot. |
| `FileKey` | `UBIGINT` | Stable per-file identifier: hash(Drive, RelativePath, FileSize#). |

