#!/usr/bin/env python3
"""
检查视频分析数据结构
"""

import json
import pymongo
from pprint import pprint

def check_video_analysis_data():
    try:
        # 连接MongoDB (使用容器名称)
        client = pymongo.MongoClient('mongodb://multimodal_mongo:27017/')
        db = client['all_data_solution_sys']
        collection = db['video_analysis_results']
        
        # 查询最新的视频分析结果
        results = list(collection.find().sort('_id', -1).limit(1))
        
        if results:
            result = results[0]
            print("=== 最新视频分析结果数据结构 ===")
            print(f"分析类型: {result.get('analysis_type', 'N/A')}")
            print(f"文件路径: {result.get('file_path', 'N/A')}")
            print(f"是否有错误: {result.get('error', 'N/A')}")
            
            # 打印主要数据字段
            main_fields = ['file_info', 'metadata', 'video_properties', 'quality_info', 
                          'analysis_summary', 'enhanced_metadata', 'content_analysis', 
                          'thumbnails', 'primary_thumbnail', 'format', 'file_size']
            
            print("\n=== 主要数据字段 ===")
            for field in main_fields:
                if field in result:
                    print(f"{field}: {type(result[field])}")
                    if isinstance(result[field], dict):
                        print(f"  子字段: {list(result[field].keys())}")
                    elif isinstance(result[field], list):
                        print(f"  列表长度: {len(result[field])}")
                    else:
                        print(f"  值: {result[field]}")
                else:
                    print(f"{field}: 不存在")
            
            # 详细打印某些重要字段
            print("\n=== 详细数据 ===")
            if 'video_properties' in result:
                print("video_properties:")
                pprint(result['video_properties'])
            
            if 'enhanced_metadata' in result:
                print("\nenhanced_metadata:")
                pprint(result['enhanced_metadata'])
                
            if 'content_analysis' in result:
                print("\ncontent_analysis:")
                pprint(result['content_analysis'])
            
        else:
            print("没有找到视频分析结果")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_video_analysis_data() 