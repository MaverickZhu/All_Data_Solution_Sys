#!/usr/bin/env python3
import asyncio
import asyncpg
import json

async def check_all_file_types():
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@multimodal_postgres:5432/multimodal_analysis')
        
        # 查询不同类型的文件
        file_types = ['txt', 'csv', 'mp3', 'm4a', 'mp4']
        
        for file_type in file_types:
            print(f'\n=== {file_type.upper()} 文件 ===')
            rows = await conn.fetch(f'''
                SELECT id, name, file_type, profiling_result 
                FROM data_sources 
                WHERE file_type = '{file_type}' 
                ORDER BY id DESC 
                LIMIT 1
            ''')
            
            if rows:
                row = rows[0]
                print(f'文件名: {row[1]}')
                print(f'有分析结果: {"有" if row[3] else "无"}')
                
                if row[3]:
                    result = row[3]
                    print(f'数据类型: {type(result)}')
                    if isinstance(result, str):
                        print('存储格式: JSON字符串')
                        try:
                            parsed = json.loads(result)
                            print(f'解析后字段: {list(parsed.keys())[:5]}...')
                            if 'analysis_type' in parsed:
                                print(f'分析类型: {parsed["analysis_type"]}')
                        except Exception as e:
                            print(f'解析失败: {e}')
                    elif isinstance(result, dict):
                        print('存储格式: JSON对象')
                        print(f'字段: {list(result.keys())[:5]}...')
                        if 'analysis_type' in result:
                            print(f'分析类型: {result["analysis_type"]}')
                    else:
                        print(f'未知格式: {type(result)}')
            else:
                print('没有找到该类型文件')
                
        await conn.close()
    except Exception as e:
        print(f'错误: {e}')

if __name__ == "__main__":
    asyncio.run(check_all_file_types()) 