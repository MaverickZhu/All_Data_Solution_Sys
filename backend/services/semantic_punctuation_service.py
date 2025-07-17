"""
智能语义标点和段落分割服务
基于语义分析为语音识别结果添加合理的标点符号和段落结构
"""
import re
import logging
from typing import List, Dict, Tuple, Any
import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)

class SemanticPunctuationService:
    """
    基于语义分析的智能标点和段落分割服务
    专门针对语音识别结果进行智能化处理
    """
    
    def __init__(self):
        # 句子结束的语义标志词
        self.sentence_endings = {
            '完了', '好了', '结束了', '行了', '可以了', '搞定了', '没问题',
            '明白了', '知道了', '清楚了', '懂了', '对了', '是的', '对的',
            '不是', '不对', '错了', '算了', '罢了', '就这样'
        }
        
        # 问句标志词（更全面）
        self.question_words = {
            '什么', '哪个', '哪里', '哪儿', '怎么', '如何', '为什么',
            '谁', '什么时候', '多少', '几', '吗', '呢', '是吧', '对吧',
            '行不行', '可以吗', '能不能', '会不会', '是不是', '有没有'
        }
        
        # 转折连接词
        self.transition_words = {
            '但是', '可是', '不过', '然而', '而且', '并且', '另外',
            '还有', '接着', '然后', '所以', '因此', '因为', '由于',
            '如果', '要是', '假如', '虽然', '尽管', '即使'
        }
        
        # 停顿词（表示自然的语音停顿）
        self.pause_indicators = {
            '那个', '这个', '就是', '嗯', '啊', '呃', '那么', '这样',
            '比如说', '换句话说', '总之', '总的来说', '简单来说'
        }
        
        # 时间相关词汇
        self.time_indicators = {
            '现在', '今天', '明天', '昨天', '上午', '下午', '晚上',
            '早上', '中午', '刚才', '马上', '立即', '接下来',
            '之前', '之后', '后来', '最后', '开始', '结束'
        }
        
        # 逻辑关系词
        self.logic_words = {
            '首先', '其次', '第一', '第二', '最后', '总结',
            '重要的是', '关键是', '问题是', '事实上', '实际上'
        }
    
    def add_intelligent_punctuation(self, text: str) -> Dict[str, Any]:
        """
        为文本添加智能标点符号和段落分割
        
        Args:
            text: 原始语音识别文本
            
        Returns:
            包含处理结果的字典
        """
        if not text or len(text.strip()) < 3:
            return self._create_result(text, "文本过短，无需处理")
        
        try:
            original_text = text.strip()
            logger.info(f"🔤 开始语义标点分析，文本长度: {len(original_text)}")
            
            # 第一步：清理和预处理
            cleaned_text = self._preprocess_text(original_text)
            
            # 第二步：语义分词和词性分析
            segments = self._semantic_segmentation(cleaned_text)
            
            # 第三步：智能添加标点符号
            punctuated_text = self._add_semantic_punctuation(segments)
            
            # 第四步：段落分割
            paragraphed_text = self._create_paragraphs(punctuated_text)
            
            # 第五步：最终优化
            final_text = self._final_polish(paragraphed_text)
            
            improvements = self._analyze_improvements(original_text, final_text)
            
            logger.info(f"✅ 语义标点分析完成")
            logger.info(f"📝 原始长度: {len(original_text)} -> 处理后长度: {len(final_text)}")
            logger.info(f"🔧 应用改进: {improvements}")
            
            return self._create_result(final_text, "语义分析完成", improvements)
            
        except Exception as e:
            logger.error(f"❌ 语义标点分析失败: {e}", exc_info=True)
            return self._create_result(text, f"处理失败，保留原文: {str(e)}")
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本，清理格式"""
        # 统一空格
        text = re.sub(r'\s+', ' ', text)
        # 移除多余的标点
        text = re.sub(r'[。！？，；：]+', '', text)
        return text.strip()
    
    def _semantic_segmentation(self, text: str) -> List[Dict[str, Any]]:
        """语义分词和分析"""
        segments = []
        
        # 使用jieba进行词性标注
        words = list(pseg.cut(text))
        
        current_segment = {
            'words': [],
            'semantic_type': 'statement',  # statement, question, transition
            'confidence': 1.0,
            'should_end': False
        }
        
        for word, pos in words:
            word_info = {
                'text': word,
                'pos': pos,
                'semantic_roles': self._analyze_word_semantics(word)
            }
            
            current_segment['words'].append(word_info)
            
            # 检查是否应该结束当前片段
            if self._should_segment_here(word, pos, current_segment):
                segments.append(current_segment)
                current_segment = {
                    'words': [],
                    'semantic_type': self._determine_segment_type(word),
                    'confidence': 1.0,
                    'should_end': False
                }
        
        # 添加最后一个片段
        if current_segment['words']:
            segments.append(current_segment)
        
        return segments
    
    def _analyze_word_semantics(self, word: str) -> List[str]:
        """分析词汇的语义角色"""
        roles = []
        
        if word in self.question_words:
            roles.append('question_indicator')
        if word in self.sentence_endings:
            roles.append('sentence_ending')
        if word in self.transition_words:
            roles.append('transition')
        if word in self.pause_indicators:
            roles.append('pause')
        if word in self.time_indicators:
            roles.append('time')
        if word in self.logic_words:
            roles.append('logic')
        
        return roles
    
    def _should_segment_here(self, word: str, pos: str, current_segment: Dict) -> bool:
        """判断是否应该在此处分段"""
        # 检查语义标志
        semantic_roles = self._analyze_word_semantics(word)
        
        # 句子结束标志
        if 'sentence_ending' in semantic_roles:
            return True
        
        # 转折词通常开始新句子
        if 'transition' in semantic_roles and len(current_segment['words']) > 3:
            return True
        
        # 逻辑词开始新段落
        if 'logic' in semantic_roles and len(current_segment['words']) > 5:
            return True
        
        # 时间词可能表示新的时间段
        if 'time' in semantic_roles and len(current_segment['words']) > 8:
            return True
        
        # 根据句子长度判断
        if len(current_segment['words']) > 15:  # 超过15个词的长句需要分割
            return True
        
        return False
    
    def _determine_segment_type(self, trigger_word: str) -> str:
        """根据触发词确定片段类型"""
        roles = self._analyze_word_semantics(trigger_word)
        
        if 'question_indicator' in roles:
            return 'question'
        elif 'transition' in roles:
            return 'transition'
        else:
            return 'statement'
    
    def _add_semantic_punctuation(self, segments: List[Dict]) -> str:
        """为语义片段添加标点符号"""
        result_parts = []
        
        for i, segment in enumerate(segments):
            # 构建片段文本
            segment_text = ''.join([w['text'] for w in segment['words']])
            
            # 根据语义类型添加标点
            if segment['semantic_type'] == 'question':
                # 问句
                if not segment_text.endswith('？'):
                    segment_text += '？'
            elif any('sentence_ending' in w.get('semantic_roles', []) for w in segment['words']):
                # 明确的句子结束
                segment_text += '。'
            elif i < len(segments) - 1:  # 不是最后一个片段
                next_segment = segments[i + 1]
                if next_segment['semantic_type'] == 'transition':
                    segment_text += '，'
                elif len(segment['words']) > 10:  # 长句子用句号
                    segment_text += '。'
                else:
                    segment_text += '，'
            else:  # 最后一个片段
                segment_text += '。'
            
            result_parts.append(segment_text)
        
        return ''.join(result_parts)
    
    def _create_paragraphs(self, text: str) -> str:
        """创建段落结构"""
        # 按句号分割句子
        sentences = re.split(r'([。！？])', text)
        paragraphs = []
        current_paragraph = []
        
        i = 0
        while i < len(sentences) - 1:
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            
            if sentence.strip():
                full_sentence = sentence + punctuation
                current_paragraph.append(full_sentence)
                
                # 判断是否应该开始新段落
                if self._should_start_new_paragraph(sentence, current_paragraph):
                    paragraphs.append(''.join(current_paragraph))
                    current_paragraph = []
            
            i += 2
        
        # 添加最后一个段落
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph))
        
        return '\n\n'.join(paragraphs)
    
    def _should_start_new_paragraph(self, sentence: str, current_paragraph: List[str]) -> bool:
        """判断是否应该开始新段落"""
        # 段落长度控制
        if len(current_paragraph) >= 4:  # 超过4句话开始新段落
            return True
        
        # 包含逻辑词的句子通常开始新段落
        if any(word in sentence for word in self.logic_words):
            return True
        
        # 包含时间词的句子可能开始新的时间段
        if any(word in sentence for word in self.time_indicators) and len(current_paragraph) >= 2:
            return True
        
        return False
    
    def _final_polish(self, text: str) -> str:
        """最终优化处理"""
        # 规范化空格和换行
        text = re.sub(r' +', ' ', text)  # 多个空格合并为一个
        text = re.sub(r'\n\n+', '\n\n', text)  # 多个换行合并为两个
        
        # 标点符号前后的空格处理
        text = re.sub(r' +([，。！？；：])', r'\1', text)
        text = re.sub(r'([，。！？；：]) +', r'\1 ', text)
        
        return text.strip()
    
    def _analyze_improvements(self, original: str, processed: str) -> List[str]:
        """分析处理改进"""
        improvements = []
        
        # 统计标点符号数量
        original_punct = len(re.findall(r'[，。！？；：]', original))
        processed_punct = len(re.findall(r'[，。！？；：]', processed))
        
        if processed_punct > original_punct:
            improvements.append(f"添加了{processed_punct - original_punct}个标点符号")
        
        # 统计段落数量
        processed_paragraphs = len(processed.split('\n\n'))
        if processed_paragraphs > 1:
            improvements.append(f"创建了{processed_paragraphs}个段落")
        
        # 检查句子结构
        sentences = re.split(r'[。！？]', processed)
        if len(sentences) > 1:
            improvements.append(f"分割为{len(sentences)}个句子")
        
        return improvements
    
    def _create_result(self, text: str, message: str, improvements: List[str] = None) -> Dict[str, Any]:
        """创建结果对象"""
        return {
            'success': True,
            'processed_text': text,
            'message': message,
            'improvements': improvements or [],
            'has_paragraphs': '\n\n' in text,
            'sentence_count': len(re.split(r'[。！？]', text)),
            'paragraph_count': len(text.split('\n\n')) if '\n\n' in text else 1
        }

# 全局实例
semantic_punctuation_service = SemanticPunctuationService() 