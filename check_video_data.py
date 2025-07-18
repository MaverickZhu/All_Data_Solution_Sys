#!/usr/bin/env python3
import asyncio
import asyncpg
import json

async def check_video_data():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@multimodal_postgres:5432/multimodal_analysis')
        
        # 查询最新的视频数据源
        rows = await conn.fetch('''
            SELECT id, filename, file_type, analysis_result, profiling_result 
            FROM data_sources 
            WHERE file_type = 'video' 
            ORDER BY id DESC 
            LIMIT 1
        ''')
        
        if rows:
            row = rows[0]
            print(f'数据源ID: {row["id"]}')
            print(f'文件名: {row["filename"]}')
            print(f'文件类型: {row["file_type"]}')
            print(f'分析结果: {"有" if row["analysis_result"] else "无"}')
            print(f'Profiling结果: {"有" if row["profiling_result"] else "无"}')
            
            if row['analysis_result']:
                print('\n=== 分析结果 ===')
                result = row['analysis_result']
                print(f'结果类型: {type(result)}')
                if isinstance(result, dict):
                    print(f'主要字段: {list(result.keys())}')
                    if 'analysis_type' in result:
                        print(f'分析类型: {result["analysis_type"]}')
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
                
        else:
            print('没有找到视频数据源')
            
        await conn.close()
    except Exception as e:
        print(f'错误: {e}')

if __name__ == "__main__":
    asyncio.run(check_video_data()) 