-- 创建测试用户
INSERT INTO users (
    username, 
    email, 
    full_name, 
    hashed_password, 
    is_active, 
    is_superuser, 
    is_verified,
    is_deleted, 
    created_at, 
    updated_at
) VALUES (
    'testuser',
    'test@example.com',
    'Test User',
    '$2b$12$tJaRukajjPKehOazA0JxOOgq9YbeOanix.4aXEWkVD/fnNnFm3m2C',
    true,
    false,
    true,
    false,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- 检查用户是否创建成功
SELECT username, email, is_active FROM users WHERE username = 'testuser'; 