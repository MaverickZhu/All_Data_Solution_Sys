-- 清理孤立的视频分析记录脚本
-- 目标：删除已删除数据源对应的视频分析记录

BEGIN;

-- 查看即将清理的记录
SELECT 'Orphaned video analyses to be cleaned:' as action;
SELECT 
  ds.id as ds_id,
  ds.name,
  ds.deleted_at as ds_deleted_at,
  va.id as analysis_id,
  va.status,
  va.created_at as va_created_at
FROM data_sources ds 
JOIN video_analyses va ON ds.id = va.data_source_id 
WHERE ds.is_deleted = true AND va.is_deleted = false
ORDER BY ds.id, va.id;

-- 软删除这些孤立的视频分析记录
UPDATE video_analyses 
SET 
  is_deleted = true,
  deleted_at = now(),
  updated_at = now()
WHERE data_source_id IN (
  SELECT id 
  FROM data_sources 
  WHERE is_deleted = true
) AND is_deleted = false;

-- 验证清理结果
SELECT 'Cleanup completed. Orphaned records deleted:' as action;
SELECT 
  ds.id as ds_id,
  ds.name,
  va.id as analysis_id,
  va.status,
  va.deleted_at as va_deleted_at
FROM data_sources ds 
JOIN video_analyses va ON ds.id = va.data_source_id 
WHERE ds.is_deleted = true 
  AND va.is_deleted = true 
  AND va.deleted_at >= now() - interval '1 minute'
ORDER BY ds.id, va.id;

-- 确认现在只有有效数据源的分析记录
SELECT 'Active video analyses (should only show ds_id 145, 146, 147):' as action;
SELECT 
  ds.id as ds_id,
  ds.name,
  va.id as analysis_id,
  va.status
FROM data_sources ds 
JOIN video_analyses va ON ds.id = va.data_source_id 
WHERE ds.is_deleted = false AND va.is_deleted = false
ORDER BY ds.id;

COMMIT;

SELECT 'Data consistency fixed successfully!' as final_status; 