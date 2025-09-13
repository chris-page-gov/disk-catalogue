# Offline Drive Catalogue — Starter Pack

This kit gives you a **two‑tier** approach:
1) A **master index** for **all files** (photos, videos, and misc) that works even when drives are offline (CSV/JSON → DuckDB).
2) Your **creative tools** on top (e.g., **Capture One** for photos; DaVinci Resolve for editing), using **referenced files** and previews on SSD.

---

## What you’ll get by following this approach

- A single search index covering **every drive** (5–20 TB, spinning HDDs), so you can **find files without mounting** the disks.
- Fast queries over **millions of rows** using **DuckDB**.
- Optional **checksums (MD5)** for de‑duplication (can be run later, as it’s I/O heavy on spinning disks).
- Clean separation between **catalogue (on SSD)** and **originals (on HDDs)**.

---

## Prerequisites

**macOS (Homebrew):**
```bash
brew install exiftool mediainfo duckdb
```

**Windows (winget):**
```powershell
winget install PhilHarvey.ExifTool
winget install MediaArea.MediaInfo.GUI
winget install DuckDB.cli
```
> If winget is locked down, download from the official sites or use Chocolatey (`choco install exiftool mediainfo duckdb`).

---

## Name and identify your drives (once)

Give each drive a human‑readable label and capture a **stable identifier**:

- **macOS:**  
  ```bash
  diskutil info /Volumes/DRIVE_NAME | grep -E "Volume UUID|Device / Media Name|File System Personality"
  ```
- **Windows (PowerShell):**  
  ```powershell
  Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, UniqueId
  Get-PhysicalDisk | Select-Object SerialNumber, FriendlyName
  ```

Copy the template to create a local manifest (untracked):

```bash
cp drive_manifest.template.csv drive_manifest.csv
```

Then edit `drive_manifest.csv` with your drive label, mounts and optional identifiers so the index
always knows **which volume** a file lives on. The file is gitignored to avoid committing
machine-specific details.

Or generate entries from currently mounted volumes inside the Dev Container:

```bash
python scripts/make_manifest.py
```

---

## How the scan works

- We use **ExifTool** for both photos **and** videos (simple, very broad metadata support).  
- Output is **CSV** per‑drive for photos and videos. Misc files (non‑media) can be added later if you like.
- The scan scripts default to **fast mode** (`-fast3`) to avoid long reads on HDDs. You can **re‑run for MD5** later to fill checksums.

### macOS (bash) — scan a single drive
```bash
bash mac_scan_photos.sh "/Volumes/YourDrive" "YourDrive"
bash mac_scan_videos.sh "/Volumes/YourDrive" "YourDrive"
```

### Windows (PowerShell) — scan a single drive
```powershell
.\windows_scan_photos.ps1 -DrivePath "E:" -DriveId "Drive_E"
.\windows_scan_videos.ps1 -DrivePath "E:" -DriveId "Drive_E"
```

Outputs go to `./output/` as date‑stamped CSVs.

---

## Build the unified index

Once you have some CSVs, load them into **DuckDB**:

```bash
duckdb catalogue.duckdb -init duckdb_schema.sql
duckdb catalogue.duckdb
-- Inside DuckDB:
.read sample_queries.sql
```

You can repeatedly append new scan CSVs; the schema creates staging tables (`*_raw`) and tidy views.

---

## Using Capture One for photos (referenced originals)

1. Create a **new Catalogue on your SSD** (not on spinning HDD).  
2. In **Preferences → Image**, set a **Preview size** large enough for offline work (e.g., 2560–5120px) and let Capture One **store previews**.
3. **Import as referenced** from each archive drive. Build previews for the years you access most; add older years incrementally.
4. Back up the C1 catalogue regularly (and your DuckDB database).

> Tip: For six‑figure image counts, keep the catalogue/database on **fast SSD**, exclude temporary folders, and import in chunks (e.g., by year).

---

## Keeping it up to date

- When you add a new shoot or a church service folder, mount the drive and re‑run the scan scripts.  
- Periodically run the **checksum pass** to enrich dedupe analysis when you have time.

---

## What’s included here

- `mac_scan_photos.sh`, `mac_scan_videos.sh` – bash scanners (ExifTool).
- `windows_scan_photos.ps1`, `windows_scan_videos.ps1` – PowerShell scanners.
- `duckdb_schema.sql` – tables, views, and indexes.
- `sample_queries.sql` – examples: duplicates, date/title searches, drive listings.
- `drive_manifest.csv` – fill this with your drive labels/IDs before scanning.

If you want, we can add **misc‑file** capture and a small **web UI** later.

---

## Dev Container Orchestrated Scan (Recommended)

Inside the dev container, use the one‑shot command per drive:

```bash
python scripts/scan_and_ingest.py --drive Ext-10
```

It will:

- Run an all‑files scan (fast; CSV to `output/<drive>/files_*.csv`).
- Derive photo/video path lists from the files CSV and extract rich metadata only for those files.
- Ingest all CSVs and create views `files`, `photos`, `videos` with derived columns:
  - `Drive`, `RelativePath`, `RelativeDirectory`, `FileExt`.
  - `FileKey = hash(Drive, RelativePath, FileSize#)` — stable per‑file ID on a drive.
- Record or update the drive snapshot in a `drives` table (label, mount, UUID, serial, notes, timestamp).
- Append a `drive_scans` history row (start/end time, status, CSV paths, row counts).

Re‑runs skip tables already ingested for that drive; pass `--force` to rescan.

If the drive label isn’t in your manifest yet, you can auto-update from mounted volumes:

```bash
python scripts/scan_and_ingest.py --drive Ext-10 --update-manifest
```

### Duplicates 101

- Candidates by size:

```bash
duckdb catalogue.duckdb -c "select \"FileSize#\" bytes, count(*) n, count(distinct Drive) drives from files group by 1 having n>1 order by n desc, bytes desc limit 50;"
```

- Candidates by name + size:

```bash
duckdb catalogue.duckdb -c "select lower(FileName) name, \"FileSize#\" bytes, count(*) n, list(distinct Drive) drives from files group by 1,2 having n>1 order by n desc, bytes desc limit 50;"
```

- Cross-drive pairs (same name + size):

```bash
duckdb catalogue.duckdb -c "select a.Drive a_drive, b.Drive b_drive, a.RelativePath a_path, b.RelativePath b_path, a.\"FileSize#\" bytes from files a join files b on a.\"FileSize#\"=b.\"FileSize#\" and lower(a.FileName)=lower(b.FileName) and a.Drive<b.Drive limit 50;"
```

For exact duplicate verification, add a `file_checksums` table with content hashes (MD5/SHA256)
keyed by (Drive, RelativePath, FileSize#) and group by checksum.
