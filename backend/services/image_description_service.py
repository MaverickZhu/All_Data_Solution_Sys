import logging
import re
from pathlib import Path
from typing import Dict, Optional
import base64
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class ImageDescriptionService:
    """图像描述生成服务，使用Qwen2.5-VL模型"""
    
    def __init__(self, model_name: str = "qwen2.5vl:7b", ollama_url: str = "http://host.docker.internal:11435"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        
    def encode_image_to_base64(self, image_path: Path) -> str:
        """将图像文件编码为base64字符串"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise
    
    async def generate_description(self, image_path: Path) -> Dict:
        """生成图像的智能描述"""
        try:
            logger.info(f"Initializing LLM for image analysis (model: {self.model_name})...")
            
            # 编码图像
            image_base64 = self.encode_image_to_base64(image_path)
            
            # 初始化Ollama LLM，使用与文本分析相同的配置
            llm = ChatOllama(
                base_url=self.ollama_url,
                model=self.model_name,
                temperature=0.1
            )
            
            # 创建图像分析提示模板
            prompt_template = """
            <|system|>
            你是一个专业的图像分析专家。你的任务是详细分析用户提供的图像，并提供准确、全面的描述。
            你必须严格遵守以下规则：
            1. 描述必须准确、客观，基于图像的实际内容
            2. 描述要包含主要物体、场景、颜色、构图等关键信息
            3. 分析图像的情感基调和氛围
            4. 识别可能的用途或场景类型
            5. 注意值得关注的细节
            6. 用中文回答，语言要简洁明了
            7. 描述长度控制在200字以内

            <|user|>
            请详细分析这张图片，包括：
            1. 主要物体和场景
            2. 颜色和构图特点
            3. 情感基调和氛围
            4. 可能的用途或场景类型
            5. 值得注意的细节

            图像内容：[IMAGE]
            """
            
            # 注意：LangChain的ChatOllama支持图像输入，但需要特殊处理
            # 我们使用消息格式来传递图像
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_template},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ]
            
            logger.info("Invoking LLM for image analysis...")
            
            # 直接调用LLM
            response = await llm.ainvoke(messages)
            
            if hasattr(response, 'content'):
                description = response.content.strip()
            else:
                description = str(response).strip()
            
            logger.info("Successfully generated image description from LLM.")
            
            # 清理模型输出中可能包含的特殊标签
            cleaned_description = re.sub(r"<think>.*?</think>", "", description, flags=re.DOTALL)
            cleaned_description = cleaned_description.strip()
            
            # 解析描述内容，提取结构化信息
            parsed_result = self._parse_description(cleaned_description)
            
            return {
                "success": True,
                "description": cleaned_description,
                "parsed_analysis": parsed_result
            }
                
        except Exception as e:
            logger.error(f"Error generating image description: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "description": "图像分析失败"
            }
    
    def _parse_description(self, description: str) -> Dict:
        """解析描述文本，提取结构化信息"""
        try:
            # 简单的关键词提取和分类
            lines = description.split('\n')
            
            # 提取关键信息
            key_elements = []
            scene_type = "未知"
            mood_tone = "中性"
            suggested_tags = []
            
            # 基于描述内容的简单分析
            description_lower = description.lower()
            
            # 场景类型判断
            if any(word in description_lower for word in ['室内', '房间', '家', '办公室']):
                scene_type = "室内场景"
            elif any(word in description_lower for word in ['户外', '街道', '公园', '自然', '风景']):
                scene_type = "户外场景"
            elif any(word in description_lower for word in ['人物', '人像', '面部', '肖像']):
                scene_type = "人物场景"
            elif any(word in description_lower for word in ['产品', '物品', '商品']):
                scene_type = "产品展示"
            
            # 情感基调判断
            if any(word in description_lower for word in ['明亮', '温暖', '愉快', '活跃']):
                mood_tone = "积极明亮"
            elif any(word in description_lower for word in ['暗', '冷', '沉重', '严肃']):
                mood_tone = "沉稳冷静"
            elif any(word in description_lower for word in ['柔和', '温和', '舒适']):
                mood_tone = "温和舒适"
            
            # 提取可能的标签
            common_objects = ['人物', '建筑', '车辆', '动物', '植物', '食物', '电子产品', '家具', '服装', '艺术品']
            for obj in common_objects:
                if obj in description:
                    suggested_tags.append(obj)
            
            return {
                "key_elements": key_elements,
                "scene_type": scene_type,
                "mood_tone": mood_tone,
                "suggested_tags": suggested_tags[:5]  # 限制标签数量
            }
            
        except Exception as e:
            logger.error(f"Error parsing description: {e}")
            return {
                "key_elements": [],
                "scene_type": "未知",
                "mood_tone": "中性",
                "suggested_tags": []
            }
    
    async def generate_simple_description(self, image_path: Path) -> str:
        """生成简单的图像描述"""
        try:
            result = await self.generate_description(image_path)
            return result.get("description", "无法生成图像描述")
        except Exception as e:
            logger.error(f"Error generating simple description: {e}")
            return "图像分析失败" 