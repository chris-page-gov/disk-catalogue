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
