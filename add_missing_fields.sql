-- 添加data_sources表缺失的字段
ALTER TABLE data_sources ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL;

-- 为is_deleted字段添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_data_sources_is_deleted ON data_sources(is_deleted);

-- 验证字段添加成功
\d data_sources;

-- 更新 data_sources 表中 created_at 为 NULL 的记录
UPDATE data_sources
SET created_at = NOW()
WHERE created_at IS NULL;

-- 更新 data_sources 表中 updated_at 为 NULL 的记录
UPDATE data_sources
SET updated_at = NOW()
WHERE updated_at IS NULL;

-- 更新 projects 表中 created_at 为 NULL 的记录
UPDATE projects
SET created_at = NOW()
WHERE created_at IS NULL;

-- 更新 projects 表中 updated_at 为 NULL 的记录
UPDATE projects
SET updated_at = NOW()
WHERE updated_at IS NULL;

-- (可选) 未来为了防止这种情况，可以考虑将这两列设置为 NOT NULL
-- ALTER TABLE data_sources ALTER COLUMN created_at SET NOT NULL;
-- ALTER TABLE data_sources ALTER COLUMN updated_at SET NOT NULL;
-- ALTER TABLE projects ALTER COLUMN created_at SET NOT NULL;
-- ALTER TABLE projects ALTER COLUMN updated_at SET NOT NULL;

SELECT id, name, created_at, updated_at FROM data_sources;
SELECT id, name, created_at, updated_at FROM projects; 