import pymongo
import json
from datetime import datetime

def check_video_analysis_data():
    try:
        # 连接MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["data_analysis"]
        collection = db["analysis_results"]
        
        print("=== 检查视频分析数据 ===")
        
        # 查找最近的视频分析结果
        video_results = collection.find({
            "analysis_type": {"$in": ["video", "video_enhanced"]}
        }).sort("created_at", -1).limit(3)
        
        for i, result in enumerate(video_results):
            print(f"\n--- 视频分析结果 {i+1} ---")
            print(f"分析类型: {result.get('analysis_type', 'N/A')}")
            print(f"数据源ID: {result.get('data_source_id', 'N/A')}")
            print(f"创建时间: {result.get('created_at', 'N/A')}")
            
            # 检查enhanced_metadata
            if 'enhanced_metadata' in result:
                metadata = result['enhanced_metadata']
                print(f"\n增强元数据:")
                print(f"  宽度: {metadata.get('width', 'N/A')}")
                print(f"  高度: {metadata.get('height', 'N/A')}")
                print(f"  帧率: {metadata.get('fps', 'N/A')}")
                print(f"  时长: {metadata.get('duration', 'N/A')}")
                print(f"  格式: {metadata.get('format_name', 'N/A')}")
                print(f"  视频编码: {metadata.get('video_codec', 'N/A')}")
                print(f"  音频编码: {metadata.get('audio_codec', 'N/A')}")
                print(f"  比特率: {metadata.get('bit_rate', 'N/A')}")
                print(f"  像素格式: {metadata.get('pixel_format', 'N/A')}")
                print(f"  有音频: {metadata.get('has_audio', 'N/A')}")
                print(f"  流数量: {metadata.get('nb_streams', 'N/A')}")
            
            # 检查其他字段
            print(f"\n其他字段:")
            print(f"  format: {result.get('format', 'N/A')}")
            print(f"  file_size: {result.get('file_size', 'N/A')}")
            print(f"  primary_thumbnail: {result.get('primary_thumbnail', 'N/A')}")
            print(f"  thumbnails数量: {len(result.get('thumbnails', []))}")
            
            # 检查content_analysis
            if 'content_analysis' in result:
                content = result['content_analysis']
                print(f"\n内容分析:")
                print(f"  分析帧数: {content.get('analyzed_frames', 'N/A')}")
                if 'brightness_analysis' in content:
                    print(f"  亮度分析: {content['brightness_analysis']}")
                if 'contrast_analysis' in content:
                    print(f"  对比度分析: {content['contrast_analysis']}")
                if 'visual_stability' in content:
                    print(f"  视觉稳定性: {content['visual_stability']}")
            
            print("\n" + "="*50)
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_video_analysis_data() 