-- List drives seen
SELECT drive_id, COUNT(*) AS n_files, SUM(bytes)/1e12 AS tb_total
FROM files_union GROUP BY 1 ORDER BY tb_total DESC;

-- Top cameras and lenses
SELECT Model, LensModel, COUNT(*) AS n
FROM photos GROUP BY 1,2 ORDER BY n DESC LIMIT 25;

-- Find duplicates by path+bytes (quick heuristic). If you later add MD5, use that instead.
WITH base AS (
  SELECT path, bytes FROM files_union
)
SELECT bytes, COUNT(*) AS dup_count
FROM base
GROUP BY 1 HAVING COUNT(*) > 1
ORDER BY dup_count DESC, bytes DESC;

-- ---
-- Duplicates (current views)
-- Candidates by size only
SELECT "FileSize#" AS bytes, COUNT(*) AS n, COUNT(DISTINCT Drive) AS drives
FROM files
GROUP BY 1 HAVING COUNT(*) > 1
ORDER BY n DESC, bytes DESC
LIMIT 50;

-- Candidates by name + size
SELECT LOWER(FileName) AS name, "FileSize#" AS bytes, COUNT(*) AS n, LIST(DISTINCT Drive) AS drives
FROM files
GROUP BY 1,2 HAVING COUNT(*) > 1
ORDER BY n DESC, bytes DESC
LIMIT 50;

-- Cross-drive pairs (same name + size)
SELECT a.Drive AS a_drive, b.Drive AS b_drive,
       a.RelativePath AS a_path, b.RelativePath AS b_path,
       a."FileSize#" AS bytes
FROM files a
JOIN files b
  ON a."FileSize#" = b."FileSize#"
 AND LOWER(a.FileName) = LOWER(b.FileName)
 AND a.Drive < b.Drive
LIMIT 50;

-- ---
-- Scan summaries (drive_scans)

-- Last scan per drive (status + counts)
WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY drive_label ORDER BY started_at DESC) AS rn
  FROM drive_scans
)
SELECT drive_label,
       started_at AS last_started_at,
       ended_at   AS last_ended_at,
       status,
       files_rows, photos_rows, videos_rows,
       (epoch(ended_at) - epoch(started_at)) AS duration_s
FROM ranked
WHERE rn = 1
ORDER BY drive_label;

-- Row deltas vs previous scan per drive
SELECT drive_label,
       started_at,
       status,
       files_rows,
       files_rows - LAG(files_rows)  OVER (PARTITION BY drive_label ORDER BY started_at) AS files_delta,
       photos_rows,
       photos_rows - LAG(photos_rows) OVER (PARTITION BY drive_label ORDER BY started_at) AS photos_delta,
       videos_rows,
       videos_rows - LAG(videos_rows) OVER (PARTITION BY drive_label ORDER BY started_at) AS videos_delta
FROM drive_scans
ORDER BY drive_label, started_at DESC
LIMIT 200;

-- Approximate throughput (rows/sec) for last scan per drive
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY drive_label ORDER BY started_at DESC) rn
  FROM drive_scans
), last AS (
  SELECT * FROM ranked WHERE rn = 1
)
SELECT drive_label,
       files_rows + photos_rows + videos_rows AS total_rows,
       (epoch(ended_at) - epoch(started_at)) AS duration_s,
       CASE WHEN (epoch(ended_at) - epoch(started_at)) > 0
            THEN ROUND( (files_rows + photos_rows + videos_rows) * 1.0 / (epoch(ended_at) - epoch(started_at)), 2)
            ELSE NULL END AS rows_per_sec
FROM last
ORDER BY rows_per_sec DESC NULLS LAST;

-- Bethel Church videos by year (matches folder/title pattern)
SELECT *
FROM videos
WHERE (LOWER(path) LIKE '%/bethel%' OR LOWER(path) LIKE '% bethel %' OR LOWER(path) LIKE '%church%')
  AND try_strptime(COALESCE(MediaCreateDate, CreateDate), '%Y:%m:%d %H:%M:%S') BETWEEN TIMESTAMP '2020-01-01' AND TIMESTAMP '2030-01-01'
ORDER BY MediaCreateDate NULLS LAST, CreateDate NULLS LAST;

-- Photos without GPS that you might want to tag
SELECT *
FROM photos
WHERE GPSLatitude IS NULL AND GPSLongitude IS NULL
ORDER BY DateTimeOriginal NULLS LAST
LIMIT 100;
