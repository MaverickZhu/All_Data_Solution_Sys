"""
Enhanced Chinese Audio Recognition Service
提供中文音频识别的后处理和优化功能
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ChineseAudioEnhancer:
    """中文音频识别增强器"""
    
    def __init__(self):
        """初始化中文分词和增强模块"""
        # 初始化jieba
        jieba.initialize()
        
        # 常见的语音识别错误模式
        self.error_patterns = {
            r'嗯嗯+': '，',  # 多个"嗯"声
            r'啊啊+': '，',  # 多个"啊"声  
            r'呃+': '，',    # 犹豫声
            r'那个那个': '那个',  # 重复的口头禅
            r'就是就是': '就是',  # 重复短语
            r'然后然后': '然后',
            r'(\w)\1{3,}': r'\1',  # 移除过度重复的字符
            r'[，。]{2,}': '。',   # 修复多重标点
        }
        
        # 连接词列表 - 用于智能断句
        self.connectors = [
            '然后', '接着', '另外', '而且', '但是', '不过', '所以', '因此', '因为',
            '虽然', '尽管', '除了', '此外', '同时', '首先', '其次', '最后', '总之'
        ]
        
        # 句尾词列表 - 用于判断句子结束
        self.sentence_endings = ['了', '的', '过', '着', '呢', '吧', '啊', '呀']
        
        # 连接性词汇 - 表示句子应该继续
        self.continuation_words = ['是', '会', '要', '可以', '应该', '必须', '正在', '已经']
    
    def enhance_transcription(self, raw_text: str, segments: List = None) -> Dict:
        """
        增强转录文本
        
        Args:
            raw_text: 原始转录文本
            segments: Whisper生成的时间段信息
            
        Returns:
            增强后的结果字典
        """
        if not raw_text:
            return {
                "enhanced_text": "",
                "raw_text": raw_text,
                "improvements": []
            }
        
        improvements = []
        enhanced_text = raw_text.strip()
        
        try:
            # 1. 基础清理和规范化
            enhanced_text, step_improvements = self._basic_cleanup(enhanced_text)
            improvements.extend(step_improvements)
            
            # 2. 智能标点符号插入
            enhanced_text, step_improvements = self._add_smart_punctuation(enhanced_text)
            improvements.extend(step_improvements)
            
            # 3. 句子分割优化
            enhanced_text, step_improvements = self._optimize_sentence_breaks(enhanced_text)
            improvements.extend(step_improvements)
            
            # 4. 修复常见识别错误
            enhanced_text, step_improvements = self._fix_common_errors(enhanced_text)
            improvements.extend(step_improvements)
            
            # 5. 最终格式化
            enhanced_text, step_improvements = self._apply_final_formatting(enhanced_text)
            improvements.extend(step_improvements)
            
            # 6. 质量评估
            quality_metrics = self._assess_text_quality(enhanced_text, raw_text)
            
            return {
                "enhanced_text": enhanced_text,
                "raw_text": raw_text,
                "improvements": improvements,
                "quality_metrics": quality_metrics,
                "enhancement_successful": True
            }
            
        except Exception as e:
            logger.error(f"Text enhancement failed: {e}")
            return {
                "enhanced_text": raw_text,  # 失败时返回原文
                "raw_text": raw_text,
                "improvements": [],
                "quality_metrics": {"overall_score": 0},
                "enhancement_successful": False,
                "error": str(e)
            }
    
    def _basic_cleanup(self, text: str) -> Tuple[str, List[str]]:
        """基础清理和规范化"""
        improvements = []
        
        # 规范化空白字符
        original_spaces = len(re.findall(r'\s+', text))
        text = re.sub(r'\s+', ' ', text)
        if original_spaces > len(re.findall(r'\s+', text)):
            improvements.append("规范化空白字符")
        
        # 在句号后添加换行符
        original_breaks = text.count('\n')
        text = re.sub(r'([。！？])([^"\n])', r'\1\n\2', text)
        if text.count('\n') > original_breaks:
            improvements.append("在句子结束后添加换行符")
        
        return text.strip(), improvements
    
    def _add_smart_punctuation(self, text: str) -> Tuple[str, List[str]]:
        """基于jieba分词的智能标点插入"""
        improvements = []
        
        try:
            # 使用jieba进行分词
            words = list(jieba.cut(text))
            result = []
            added_punctuation = 0
            
            for i, word in enumerate(words):
                result.append(word)
                
                # 在连接词后添加逗号
                if (i < len(words) - 1 and 
                    word in self.connectors and
                    not words[i + 1].startswith(('，', '。', '！', '？'))):
                    result.append('，')
                    added_punctuation += 1
                
                # 在特定结尾词后添加句号
                if (i < len(words) - 1 and 
                    word.endswith(tuple(self.sentence_endings)) and 
                    len(word) > 1 and
                    not words[i + 1].startswith(('，', '。', '！', '？'))):
                    
                    # 检查下一个词是否暗示句子继续
                    next_word = words[i + 1] if i + 1 < len(words) else ""
                    if next_word not in self.continuation_words:
                        result.append('。')
                        added_punctuation += 1
            
            enhanced_text = ''.join(result)
            
            if added_punctuation > 0:
                improvements.append(f"智能添加了{added_punctuation}个标点符号")
            
            return enhanced_text, improvements
            
        except Exception as e:
            logger.error(f"Smart punctuation failed: {e}")
            return text, improvements
    
    def _optimize_sentence_breaks(self, text: str) -> Tuple[str, List[str]]:
        """优化句子断句"""
        improvements = []
        
        try:
            # 按现有标点符号分割
            sentences = re.split(r'([。！？])', text)
            
            optimized = []
            current_sentence = ""
            merged_short = 0
            
            for part in sentences:
                if part in ['。', '！', '？']:
                    current_sentence += part
                    # 避免过短的句子（少于5个字符）
                    if len(current_sentence.strip()) > 5:
                        optimized.append(current_sentence.strip())
                        current_sentence = ""
                    else:
                        # 短句子与下一句合并
                        merged_short += 1
                else:
                    current_sentence += part
            
            # 添加剩余文本
            if current_sentence.strip():
                optimized.append(current_sentence.strip())
            
            # 用适当的间距连接
            result = '\n'.join(optimized)
            
            # 移除过多的换行符
            original_breaks = result.count('\n\n\n')
            result = re.sub(r'\n{3,}', '\n\n', result)
            
            if merged_short > 0:
                improvements.append(f"合并了{merged_short}个过短的句子")
            if original_breaks > 0:
                improvements.append("移除了过多的换行符")
            
            return result, improvements
            
        except Exception as e:
            logger.error(f"Sentence break optimization failed: {e}")
            return text, improvements
    
    def _fix_common_errors(self, text: str) -> Tuple[str, List[str]]:
        """修复常见的中文语音识别错误"""
        improvements = []
        original_text = text
        
        try:
            for pattern, replacement in self.error_patterns.items():
                matches = len(re.findall(pattern, text))
                text = re.sub(pattern, replacement, text)
                if matches > 0:
                    improvements.append(f"修复了{matches}个'{pattern}'模式的错误")
            
            # 修复重复的短语（更精确的检测）
            repeated_phrases = re.findall(r'(\w{2,4})\1+', text)
            for phrase in set(repeated_phrases):
                text = re.sub(f'({phrase})+', phrase, text)
            
            if repeated_phrases:
                improvements.append(f"修复了{len(set(repeated_phrases))}个重复短语")
            
            return text, improvements
            
        except Exception as e:
            logger.error(f"Error fixing failed: {e}")
            return original_text, improvements
    
    def _apply_final_formatting(self, text: str) -> Tuple[str, List[str]]:
        """应用最终格式化"""
        improvements = []
        
        try:
            # 确保标点符号周围有适当的间距
            original_spacing = len(re.findall(r'[。！？]\s*[^。！？\s]', text))
            text = re.sub(r'([。！？])\s*', r'\1 ', text)
            text = re.sub(r'\s+([。！？，])', r'\1', text)
            
            # 首字母大写（如果包含英文）
            capitalized = 0
            def capitalize_func(match):
                nonlocal capitalized
                capitalized += 1
                return match.group(1) + match.group(2).upper()
            
            text = re.sub(r'([。！？]\s*)([a-z])', capitalize_func, text)
            
            # 最终清理
            text = text.strip()
            
            if original_spacing > 0:
                improvements.append("规范化了标点符号间距")
            if capitalized > 0:
                improvements.append(f"大写了{capitalized}个句首字母")
            
            return text, improvements
            
        except Exception as e:
            logger.error(f"Final formatting failed: {e}")
            return text, improvements
    
    def _assess_text_quality(self, enhanced_text: str, original_text: str) -> Dict:
        """评估文本质量"""
        try:
            # 基础指标
            enhanced_len = len(enhanced_text)
            original_len = len(original_text)
            
            # 字符多样性
            enhanced_chars = len(set(enhanced_text))
            original_chars = len(set(original_text))
            
            # 标点符号密度
            enhanced_punct = len(re.findall(r'[。！？，]', enhanced_text))
            original_punct = len(re.findall(r'[。！？，]', original_text))
            
            # 句子结构
            enhanced_sentences = len(re.findall(r'[。！？]', enhanced_text))
            original_sentences = len(re.findall(r'[。！？]', original_text))
            
            # 连接词密度（文本连贯性指标）
            connector_count = sum(1 for word in self.connectors if word in enhanced_text)
            
            # 重复率评估
            chars = list(enhanced_text)
            repetition_ratio = 1 - (len(set(chars)) / len(chars)) if chars else 0
            
            # 综合质量分数 (0-1)
            quality_factors = [
                min(1.0, enhanced_len / 100),  # 长度因子
                min(1.0, enhanced_chars / 50),  # 多样性因子
                1 - min(1.0, repetition_ratio * 2),  # 反重复因子
                min(1.0, enhanced_punct / enhanced_len * 20) if enhanced_len > 0 else 0,  # 标点密度
                min(1.0, enhanced_sentences / 10),  # 句子数量因子
                min(1.0, connector_count / 5)  # 连贯性因子
            ]
            
            overall_score = sum(quality_factors) / len(quality_factors)
            
            return {
                "overall_score": round(overall_score, 3),
                "text_length": enhanced_len,
                "character_variety": enhanced_chars,
                "punctuation_count": enhanced_punct,
                "sentence_count": enhanced_sentences,
                "connector_count": connector_count,
                "repetition_ratio": round(repetition_ratio, 3),
                "improvement_ratio": round(enhanced_len / original_len, 2) if original_len > 0 else 1.0,
                "punctuation_improvement": enhanced_punct - original_punct,
                "sentence_improvement": enhanced_sentences - original_sentences
            }
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {"overall_score": 0, "error": str(e)}

    def calculate_enhanced_confidence(self, segments: List) -> Dict:
        """计算增强的置信度指标"""
        if not segments:
            return {"confidence": 0, "confidence_distribution": {}}
            
        try:
            total_confidence = 0
            total_duration = 0
            word_count = 0
            confidence_scores = []
            
            for segment in segments:
                if 'end' in segment and 'start' in segment:
                    duration = segment['end'] - segment['start']
                    
                    # 增强的置信度计算
                    if 'avg_logprob' in segment:
                        confidence = max(0.0, min(1.0, np.exp(segment['avg_logprob'])))
                    elif 'confidence' in segment:
                        confidence = segment.get('confidence', 0)
                    else:
                        # 基于文本的置信度估算
                        text_length = len(segment.get('text', ''))
                        confidence = min(0.9, max(0.1, text_length / 50.0))
                    
                    confidence_scores.append(confidence)
                    total_confidence += confidence * duration
                    total_duration += duration
                    
                    # 计算词数
                    words = segment.get('words', [])
                    if words:
                        word_count += len(words)
                    else:
                        word_count += len(segment.get('text', '').split())
            
            avg_confidence = total_confidence / total_duration if total_duration > 0 else 0
            
            # 置信度分布分析
            confidence_distribution = {
                "high": len([c for c in confidence_scores if c > 0.7]),
                "medium": len([c for c in confidence_scores if 0.4 <= c <= 0.7]),
                "low": len([c for c in confidence_scores if c < 0.4])
            }
            
            return {
                "confidence": round(avg_confidence, 3),
                "confidence_distribution": confidence_distribution,
                "total_segments": len(segments),
                "word_count": word_count,
                "words_per_minute": round((word_count / (total_duration / 60)) if total_duration > 0 else 0, 1),
                "average_segment_confidence": round(np.mean(confidence_scores), 3) if confidence_scores else 0,
                "confidence_std": round(np.std(confidence_scores), 3) if confidence_scores else 0
            }
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return {"confidence": 0, "confidence_distribution": {}, "error": str(e)} 