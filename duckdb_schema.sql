-- Create raw staging tables (append-only)
CREATE TABLE IF NOT EXISTS photos_raw AS SELECT * FROM read_csv_auto('output/photos_*.csv', HEADER=TRUE) LIMIT 0;
CREATE TABLE IF NOT EXISTS videos_raw AS SELECT * FROM read_csv_auto('output/videos_*.csv', HEADER=TRUE) LIMIT 0;

-- Append helpers (use after dropping the LIMIT 0 tables if empty)
COPY photos_raw FROM 'output/photos_*.csv' (AUTO_DETECT=TRUE, HEADER=TRUE);
COPY videos_raw FROM 'output/videos_*.csv' (AUTO_DETECT=TRUE, HEADER=TRUE);

-- Normalised views
CREATE OR REPLACE VIEW photos AS
SELECT
  COALESCE(FilePath, CONCAT(Directory, '/', FileName)) AS path,
  COALESCE(Drive, 'UNKNOWN') AS drive_id,
  try_cast(FileSize# AS BIGINT) AS bytes,
  MIMEType,
  Model, Make, LensModel, LensID,
  FNumber, ShutterSpeed, ISO, FocalLength,
  ImageWidth, ImageHeight, Orientation,
  GPSLatitude, GPSLongitude,
  Rating, Label, "XMP-dc:Title" AS title,
  Keywords, HierarchicalSubject,
  DateTimeOriginal, CreateDate, ModifyDate
FROM photos_raw;

CREATE OR REPLACE VIEW videos AS
SELECT
  COALESCE(FilePath, CONCAT(Directory, '/', FileName)) AS path,
  COALESCE(Drive, 'UNKNOWN') AS drive_id,
  try_cast(FileSize# AS BIGINT) AS bytes,
  MIMEType,
  Duration, TrackCreateDate, MediaCreateDate, CreateDate,
  HandlerDescription, CompressorName, VideoCodec, VideoFrameRate, VideoFrameCount,
  ImageWidth, ImageHeight, AudioFormat, AudioChannels, AudioSampleRate, BitRate
FROM videos_raw;

-- Convenience views
CREATE OR REPLACE VIEW files_union AS
SELECT 'photo' AS kind, * FROM photos
UNION ALL
SELECT 'video' AS kind, * FROM videos;

-- Indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_photos_when ON photos(DateTimeOriginal);
CREATE INDEX IF NOT EXISTS idx_photos_drive ON photos(drive_id);
CREATE INDEX IF NOT EXISTS idx_videos_when ON videos(MediaCreateDate);
CREATE INDEX IF NOT EXISTS idx_videos_drive ON videos(drive_id);
