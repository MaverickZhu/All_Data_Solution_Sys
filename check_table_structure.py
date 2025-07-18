#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_table_structure():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@multimodal_postgres:5432/multimodal_analysis')
        
        # 查询表结构
        rows = await conn.fetch('''
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'data_sources' 
            ORDER BY ordinal_position
        ''')
        
        print('data_sources表结构:')
        for row in rows:
            print(f'  {row[0]}: {row[1]}')
            
        # 查询最新的视频数据源
        video_rows = await conn.fetch('''
            SELECT * FROM data_sources 
            WHERE file_type = 'video' 
            ORDER BY id DESC 
            LIMIT 1
        ''')
        
        if video_rows:
            print('\n找到视频数据源:')
            row = video_rows[0]
            for i, col in enumerate(rows):
                col_name = col[0]
                value = row[i] if i < len(row) else 'N/A'
                print(f'  {col_name}: {value}')
        else:
            print('\n没有找到视频数据源')
            
        await conn.close()
    except Exception as e:
        print(f'错误: {e}')

if __name__ == "__main__":
    asyncio.run(check_table_structure()) 