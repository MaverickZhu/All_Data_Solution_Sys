import re
import logging
from typing import List, Dict, Any, Set, Tuple
import jieba
from .semantic_punctuation_service import semantic_punctuation_service

logger = logging.getLogger(__name__)

class TextOptimizationService:
    """
    真正的文本优化服务 - 专门解决语音识别中的重复循环和冗余
    核心原则：检测并移除重复，保持语义完整，绝不创造新的重复
    """
    
    def __init__(self):
        # 填充词（语音识别中的无意义词汇）
        self.filler_words = {
            '嗯', '啊', '呃', '哦', '额', '唔', '咳咳', '嗯嗯', '那个', '这个'
        }
        
        # 问句标识词
        self.question_indicators = ['什么', '怎么', '为什么', '哪里', '谁', '吗', '呢', '是吧', '对吧']
    
    def optimize_speech_text(self, text: str, language: str = 'zh') -> Dict[str, Any]:
        """
        真正优化语音识别文本 - 重点解决重复循环问题
        """
        if not text or len(text.strip()) < 3:
            return self._create_result(False, text, "文本过短，无需优化")
        
        original_text = text.strip()
        original_length = len(original_text)
        
        try:
            logger.info(f"🔧 开始文本优化，原始长度: {original_length}")
            
            optimized_text = original_text
            all_improvements = []
            
            # 第一步：检测并移除重复循环（最重要的步骤）
            optimized_text, loop_improvements = self._remove_repetitive_loops(optimized_text)
            all_improvements.extend(loop_improvements)
            
            # 第二步：移除明显的填充词
            optimized_text, filler_improvements = self._clean_filler_words(optimized_text)
            all_improvements.extend(filler_improvements)
            
            # 第三步：清理空格和基本标点
            optimized_text = self._normalize_whitespace(optimized_text)
            
            # 第四步：语义分析添加智能标点和段落
            semantic_result = semantic_punctuation_service.add_intelligent_punctuation(optimized_text)
            if semantic_result['success']:
                optimized_text = semantic_result['processed_text']
                all_improvements.extend(semantic_result['improvements'])
            else:
                # 回退到基础标点处理
                optimized_text, punct_improvements = self._add_smart_punctuation(optimized_text)
                all_improvements.extend(punct_improvements)
            
            # 最终安全检查
            if len(optimized_text) < original_length * 0.5:
                logger.warning("优化结果过度缩短，保留原文")
                return self._create_result(True, original_text, "保留原文以确保完整性", 
                                         ["保持原文"], original_length, original_length)
            
            optimized_length = len(optimized_text)
            
            logger.info(f"✅ 文本优化完成")
            logger.info(f"📝 原始长度: {original_length} -> 优化长度: {optimized_length}")
            logger.info(f"📝 应用改进: {all_improvements}")
            
            return self._create_result(True, optimized_text, "优化成功", 
                                     all_improvements, original_length, optimized_length)
                
        except Exception as e:
            logger.error(f"文本优化异常: {str(e)}")
            return self._create_result(True, original_text, f"保留原文: {str(e)}", 
                                     ["保留原文"], original_length, original_length)
    
    def _remove_repetitive_loops(self, text: str) -> Tuple[str, List[str]]:
        """
        检测并移除重复循环 - 这是解决用户问题的核心方法
        """
        improvements = []
        result_text = text
        
        # 方法1：检测完全相同的句子重复
        sentences = re.split(r'[。！？，；]', result_text)
        cleaned_sentences = []
        sentence_count = {}
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 3:  # 跳过太短的片段
                cleaned_sentences.append(sentence)
                continue
                
            # 计算句子出现次数
            if sentence in sentence_count:
                sentence_count[sentence] += 1
                # 如果同一句话出现3次以上，只保留前2次
                if sentence_count[sentence] <= 2:
                    cleaned_sentences.append(sentence)
                else:
                    improvements.append(f"移除重复句子")
            else:
                sentence_count[sentence] = 1
                cleaned_sentences.append(sentence)
        
        if len(cleaned_sentences) < len(sentences):
            result_text = '。'.join([s for s in cleaned_sentences if s.strip()])
            if not result_text.endswith(('。', '！', '？')):
                result_text += '。'
        
        # 方法2：检测短语级别的重复
        result_text, phrase_improvements = self._remove_phrase_repetitions(result_text)
        improvements.extend(phrase_improvements)
        
        return result_text, improvements
    
    def _remove_phrase_repetitions(self, text: str) -> Tuple[str, List[str]]:
        """
        移除短语级别的重复（如"我没有看哪个点是吧"重复多次）
        """
        improvements = []
        
        # 使用滑动窗口检测重复短语
        words = text.split()
        if len(words) < 8:
            return text, improvements
        
        # 检查4-8个词的短语重复
        for phrase_len in range(4, 9):
            if len(words) < phrase_len * 3:  # 至少需要3次重复才处理
                continue
                
            i = 0
            while i < len(words) - phrase_len * 2:
                # 提取当前短语
                current_phrase = words[i:i+phrase_len]
                phrase_text = ' '.join(current_phrase)
                
                # 检查后面是否有连续的重复
                repeat_count = 0
                j = i + phrase_len
                
                while j + phrase_len <= len(words):
                    next_phrase = words[j:j+phrase_len]
                    if current_phrase == next_phrase:
                        repeat_count += 1
                        j += phrase_len
                    else:
                        break
                
                # 如果发现连续重复3次以上，只保留1次
                if repeat_count >= 2:
                    # 移除重复的部分
                    words = words[:i+phrase_len] + words[j:]
                    improvements.append(f"移除重复短语")
                    logger.info(f"移除重复短语: '{phrase_text}' (重复{repeat_count}次)")
                    break  # 重新开始检查
                else:
                    i += 1
        
        return ' '.join(words), improvements
    
    def _clean_filler_words(self, text: str) -> Tuple[str, List[str]]:
        """
        移除填充词，但保持句子结构
        """
        improvements = []
        
        # 分词
        words = list(jieba.cut(text))
        cleaned_words = []
        removed_count = 0
        
        for i, word in enumerate(words):
            word_clean = word.strip()
            
            # 只移除单独的填充词，不影响句子结构
            if (word_clean in self.filler_words and 
                len(word_clean) <= 2 and
                not self._is_important_context(words, i)):
                removed_count += 1
            else:
                cleaned_words.append(word)
        
        if removed_count > 0:
            improvements.append(f"移除{removed_count}个填充词")
            logger.info(f"移除了{removed_count}个填充词")
        
        return ''.join(cleaned_words), improvements
    
    def _is_important_context(self, words: List[str], index: int) -> bool:
        """
        判断填充词是否在重要上下文中（如果是，则保留）
        """
        if index == 0 or index == len(words) - 1:
            return False
        
        prev_word = words[index - 1].strip()
        next_word = words[index + 1].strip()
        
        # 如果前后都是标点符号，可以安全移除
        if prev_word in '，。！？；：' and next_word in '，。！？；：':
            return False
        
        return True
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        规范化空格和标点
        """
        # 规范化空格
        text = re.sub(r'\s+', ' ', text)
        # 标点符号前后的空格处理
        text = re.sub(r'\s*([，。！？；：])\s*', r'\1', text)
        # 去除首尾空格
        return text.strip()
    
    def _add_smart_punctuation(self, text: str) -> Tuple[str, List[str]]:
        """
        智能添加标点符号
        """
        improvements = []
        result_text = text
        
        # 检查是否是问句
        is_question = any(indicator in text for indicator in self.question_indicators)
        
        if is_question and not text.endswith('？'):
            result_text = re.sub(r'[。！；：]+$', '', result_text) + '？'
            improvements.append("添加问号")
        elif not re.search(r'[。！？；：]$', text):
            result_text += '。'
            improvements.append("添加句号")
        
        return result_text, improvements
    
    def _create_result(self, success: bool, text: str, message: str, 
                      improvements: List[str] = None, 
                      original_length: int = 0, 
                      optimized_length: int = 0) -> Dict[str, Any]:
        """创建结果对象"""
        return {
            'success': success,
            'optimized_text': text,
            'message': message,
            'improvements': improvements or [],
            'original_length': original_length,
            'optimized_length': optimized_length,
            'reduction_rate': round((original_length - optimized_length) / original_length * 100, 1) if original_length > 0 else 0
        } 