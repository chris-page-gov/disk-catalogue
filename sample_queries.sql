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

-- ---
-- Following Jesus semantic audio catalogue

-- Processing progress from the semantic catalogue status table
SELECT status,
       COUNT(*) AS files,
       ROUND(SUM(COALESCE(elapsed_seconds, 0)), 1) AS elapsed_s
FROM audio_semantic_catalogue_status
GROUP BY 1
ORDER BY files DESC;

-- Failed semantic audio rows with their latest error
SELECT file_key,
       album_folder,
       file_name,
       error,
       failed_at
FROM audio_semantic_catalogue_status
WHERE status = 'failed'
ORDER BY failed_at DESC NULLS LAST, album_folder, file_name;

-- Verification summary for expected files, catalogue sidecars, and transcripts
SELECT total_files,
       catalogued_files,
       transcript_files,
       missing_catalogue,
       missing_transcripts,
       empty_transcripts,
       short_transcripts,
       duplicate_audit_complete,
       exact_duplicate_groups,
       exact_duplicate_files,
       folder_duplicate_groups,
       folder_duplicate_folders,
       verified_at
FROM audio_semantic_catalogue_verification;

-- Duplicate audit groups for the Following Jesus semantic catalogue
SELECT duplicate_kind,
       duplicate_key,
       group_count,
       file_count,
       album_folders,
       file_names
FROM audio_semantic_catalogue_duplicates
ORDER BY duplicate_kind, file_count DESC, duplicate_key;

-- Embedded/source metadata retained for later re-analysis
SELECT file_key,
       album_folder,
       file_name,
       title,
       artist,
       album,
       genre,
       itunes_cddb_ids,
       itunes_ufid,
       metadata_json
FROM audio_semantic_source_metadata
ORDER BY album_folder, disc_index, track_index
LIMIT 25;

-- Semantic catalogue rows with low confidence or missing Bible references
SELECT album_folder,
       file_name,
       embedded_title,
       semantic_title,
       track_type,
       bible_reference,
       metadata_confidence,
       transcript_path
FROM audio_semantic_catalogue
WHERE metadata_confidence <> 'high'
   OR bible_reference IS NULL
ORDER BY album_folder, file_name
LIMIT 100;

-- Bible reference coverage by book
SELECT COALESCE(bible_book, '(none)') AS bible_book,
       COUNT(*) AS tracks,
       LIST(DISTINCT bible_reference) FILTER (WHERE bible_reference IS NOT NULL) AS references
FROM audio_semantic_catalogue
GROUP BY 1
ORDER BY tracks DESC, bible_book;

-- Tracks by inferred type and storying role
SELECT track_type,
       storying_role,
       COUNT(*) AS tracks
FROM audio_semantic_catalogue
GROUP BY 1,2
ORDER BY tracks DESC, track_type, storying_role;

-- Speaker coverage. speaker_names is stored as JSON text in the exported table.
SELECT speaker.value::VARCHAR AS speaker_name,
       COUNT(*) AS tracks
FROM audio_semantic_catalogue,
     json_each(speaker_names) AS speaker
GROUP BY 1
ORDER BY tracks DESC, speaker_name;

-- Keyword search across semantic title, summaries, and keywords JSON
SELECT album_folder,
       file_name,
       semantic_title,
       bible_reference,
       summary_short,
       transcript_path
FROM audio_semantic_catalogue
WHERE LOWER(semantic_title) LIKE '%obedience%'
   OR LOWER(summary_short) LIKE '%obedience%'
   OR LOWER(summary_long) LIKE '%obedience%'
   OR LOWER(keywords) LIKE '%obedience%'
ORDER BY album_folder, file_name
LIMIT 50;

-- Evaluation scores from optional gold questions
SELECT question_id,
       score,
       max_score,
       passed,
       details_json
FROM audio_semantic_catalogue_eval
ORDER BY passed, question_id;
