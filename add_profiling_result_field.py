#!/usr/bin/env python3
"""
添加profiling_result字段到data_sources表
"""

import asyncio
import asyncpg
from backend.core.config import settings

async def add_profiling_result_field():
    """添加profiling_result字段"""
    try:
        # 解析数据库URL
        db_url = settings.database_url
        # 格式: postgresql+asyncpg://user:password@localhost/dbname
        # 需要转换为asyncpg格式: postgresql://user:password@localhost/dbname
        asyncpg_url = db_url.replace("+asyncpg", "")
        
        conn = await asyncpg.connect(asyncpg_url)
        
        # 检查字段是否已存在
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'data_sources' AND column_name = 'profiling_result';
        """
        
        result = await conn.fetchval(check_sql)
        
        if result:
            print("✅ profiling_result字段已存在")
        else:
            # 添加字段
            add_sql = "ALTER TABLE data_sources ADD COLUMN profiling_result TEXT;"
            await conn.execute(add_sql)
            print("✅ 成功添加profiling_result字段")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")

if __name__ == "__main__":
    asyncio.run(add_profiling_result_field()) 