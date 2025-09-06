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

Put these in `drive_manifest.csv` (provided) so the index always knows **which volume** a file lives on.

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
