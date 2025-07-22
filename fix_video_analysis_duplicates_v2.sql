-- 清理重复的视频分析记录脚本 (修复版本)
-- 实施方案1：严格唯一约束

-- 第一部分：在事务中清理重复记录
BEGIN;

-- 记录操作前的状态
SELECT 'Before cleanup:' as action;
SELECT 
  data_source_id,
  COUNT(*) as total_records
FROM video_analyses 
WHERE is_deleted = false
GROUP BY data_source_id 
HAVING COUNT(*) > 1
ORDER BY data_source_id;

-- 软删除重复记录
WITH ranked_analyses AS (
  SELECT 
    id,
    data_source_id,
    status,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY data_source_id 
      ORDER BY 
        CASE status 
          WHEN 'COMPLETED' THEN 1 
          WHEN 'IN_PROGRESS' THEN 2 
          WHEN 'PENDING' THEN 3 
          WHEN 'FAILED' THEN 4 
        END,
        created_at DESC
    ) as priority_rank
  FROM video_analyses 
  WHERE is_deleted = false
),
records_to_delete AS (
  SELECT id, data_source_id, status
  FROM ranked_analyses 
  WHERE priority_rank > 1
)
UPDATE video_analyses 
SET 
  is_deleted = true,
  deleted_at = now(),
  updated_at = now()
WHERE id IN (SELECT id FROM records_to_delete);

-- 显示被删除的记录
SELECT 'Deleted records:' as action;
SELECT 
  id,
  data_source_id, 
  status,
  created_at,
  deleted_at
FROM video_analyses 
WHERE is_deleted = true 
  AND deleted_at >= now() - interval '1 minute'
ORDER BY data_source_id, created_at;

-- 验证清理结果
SELECT 'After cleanup:' as action;
SELECT 
  data_source_id,
  COUNT(*) as total_records
FROM video_analyses 
WHERE is_deleted = false
GROUP BY data_source_id 
ORDER BY data_source_id;

COMMIT;

-- 第二部分：在事务外创建唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_video_analyses_unique_data_source
ON video_analyses (data_source_id) 
WHERE is_deleted = false;

SELECT 'Unique constraint added successfully!' as final_status; 