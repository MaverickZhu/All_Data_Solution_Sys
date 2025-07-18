#!/usr/bin/env python3
import asyncio
import asyncpg
import json

async def check_mp4_data():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@multimodal_postgres:5432/multimodal_analysis')
        
        rows = await conn.fetch('''
            SELECT id, name, file_type, profiling_result 
            FROM data_sources 
            WHERE file_type = 'mp4' 
            ORDER BY id DESC 
            LIMIT 1
        ''')
        
        if rows:
            row = rows[0]
            print(f'MP4文件: {row[1]}')
            print(f'ID: {row[0]}')
            print(f'类型: {row[2]}')
            print(f'有分析结果: {"有" if row[3] else "无"}')
            
            if row[3]:
                result = row[3]
                print(f'\n分析结果类型: {type(result)}')
                if isinstance(result, dict):
                    print(f'主要字段: {list(result.keys())}')
                    if 'analysis_type' in result:
                        print(f'分析类型: {result["analysis_type"]}')
                print('\n完整结果:')
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print('没有找到MP4文件')
            
        await conn.close()
    except Exception as e:
        print(f'错误: {e}')

if __name__ == "__main__":
    asyncio.run(check_mp4_data()) 