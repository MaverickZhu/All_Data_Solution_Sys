-- 清理重复的视频分析记录脚本
-- 实施方案1：严格唯一约束

-- 开始事务
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

-- 第一步：软删除重复记录
-- 保留优先级最高的记录（COMPLETED > IN_PROGRESS > PENDING > FAILED，相同状态下保留最新的）
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

-- 第二步：添加唯一约束，防止未来出现重复
-- 创建部分唯一索引（只对未删除的记录生效）
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_video_analyses_unique_data_source
ON video_analyses (data_source_id) 
WHERE is_deleted = false;

SELECT 'Unique constraint added successfully' as action;

-- 提交事务
COMMIT;

SELECT 'Cleanup completed successfully!' as final_status; 