-- 更新项目表结构，添加缺少的字段

-- 添加status字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active' NOT NULL;

-- 添加is_deleted字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT false NOT NULL;

-- 添加deleted_at字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- 确保user_id字段不为空
ALTER TABLE projects ALTER COLUMN user_id SET NOT NULL;

-- 确保created_at和updated_at字段不为空并有默认值
ALTER TABLE projects ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE projects ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE projects ALTER COLUMN updated_at SET NOT NULL;

-- 添加索引
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS ix_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS ix_projects_is_deleted ON projects(is_deleted);

-- 验证表结构
\d projects; 