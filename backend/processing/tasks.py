import logging
import time
from pathlib import Path
import json
import pandas as pd
import numpy as np
import asyncio # 引入asyncio
from datetime import datetime, timezone

from ydata_profiling import ProfileReport
from sqlalchemy.exc import OperationalError
from PIL import Image
import imagehash

# NLP imports
import nltk
import jieba
import jieba.analyse # 导入jieba的分析模块
from langdetect import detect, LangDetectException
from snownlp import SnowNLP
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Document processing
import docx
import fitz  # PyMuPDF
import pypandoc
from sklearn.cluster import KMeans # 导入KMeans
from PIL.ExifTags import TAGS # 导入TAGS用于解析EXIF

# Audio/Video processing imports
import librosa
import mutagen
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
import cv2

# Explicitly add the NLTK data path defined in the Dockerfile
# This ensures that NLTK looks for data in our specified location.
nltk.data.path.append("/usr/local/share/nltk_data")

# Sumy imports for summarization
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer

from backend.core.celery_app import celery_app
from backend.core.database import get_sync_db
from backend.models.data_source import DataSource, ProfileStatusEnum, AnalysisCategory
from backend.core.config import settings
from backend.semantic_processing.embedding_service import EmbeddingService
from backend.services.mongo_service import mongo_service
from backend.services.llm_service import LLMService # 引入LLMService
# Removed AudioDescriptionService import - using direct Whisper integration instead

from backend.services.audio_enhancement import AudioEnhancementService

import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# 🔥 修复moviepy导入错误
try:
    from moviepy.editor import VideoFileClip  # type: ignore
    MOVIEPY_AVAILABLE = True
except ImportError:
    # 如果moviepy不可用，提供fallback
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None  # type: ignore
    logging.warning("MoviePy not available, some video processing features may be limited")


logger = logging.getLogger("ml")

# 🔥 修复get_session_local未定义错误
def get_session_local():
    """创建同步数据库会话工厂"""
    from backend.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 转换异步URL为同步URL
    sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

# Ensure NLTK data is downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK 'stopwords' resource...")
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    logger.info("Downloading NLTK 'vader_lexicon' resource...")
    nltk.download('vader_lexicon', quiet=True)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK 'punkt' resource...")
    nltk.download('punkt', quiet=True)

# 构建一个指向 "backend/data/stopwords" 目录的绝对路径
# 这使得路径查找与当前工作目录无关，更加健壮
STOPWORDS_DIR = Path(__file__).resolve().parent.parent / "data" / "stopwords"


def get_stopwords(file_path: Path) -> list[str]:
    """从给定路径的文件中加载停用词列表。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.warning(f"Stopwords file not found at {file_path}. Proceeding without custom stopwords.")
        return []

def extract_text_from_md(file_path: Path) -> str:
    """Extracts text content from a .md file."""
    try:
        # Pandoc needs the path as a string
        return pypandoc.convert_file(str(file_path), 'plain')
    except Exception as e:
        logger.error(f"Error reading markdown file {file_path} with pandoc: {e}")
        # Fallback to simple read if pandoc fails
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as read_e:
            logger.error(f"Fallback direct read failed for markdown file {file_path}: {read_e}")
            return ""

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text content from a .pdf file."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"Error reading pdf file {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text content from a .docx file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error reading docx file {file_path}: {e}")
        return ""

def perform_text_analysis(df: pd.DataFrame) -> dict:
    """
    Performs enhanced text analysis on a DataFrame, supporting both English and Chinese.
    Returns comprehensive analysis including improved summaries, keywords, and insights.
    """
    text_content = " ".join(df.iloc[:, 0].astype(str).tolist())
    
    # Language Detection
    try:
        lang = detect(text_content[:200]) # Detect based on the first 200 chars
    except LangDetectException:
        lang = "unknown"

    # --- Basic Text Stats ---
    sentences = nltk.sent_tokenize(text_content)
    words = text_content.split()
    word_count = len(words)
    sentence_count = len(sentences)
    char_count = len(text_content)
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
    
    # Enhanced text statistics
    unique_words = len(set(word.lower() for word in words if word.isalpha()))
    lexical_diversity = unique_words / word_count if word_count > 0 else 0
    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0

    text_stats = {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "char_count": char_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "unique_words": unique_words,
        "lexical_diversity": round(lexical_diversity, 3),
        "avg_word_length": round(avg_word_length, 2),
        "readability_score": round(206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 100), 2) if avg_sentence_length > 0 and avg_word_length > 0 else 0
    }

    # --- Enhanced Keyword Extraction ---
    keywords = []
    keyword_scores = {}
    try:
        if lang == 'zh-cn':
            # 使用jieba内置的TextRank算法提取关键词和权重
            tags = jieba.analyse.extract_tags(text_content, topK=15, withWeight=True)
            keywords = [tag for tag, weight in tags]
            keyword_scores = {tag: round(weight, 4) for tag, weight in tags}
        elif lang == 'en':
            # 对于英文，我们可以继续使用一个简单有效的方法，或者未来替换成例如spaCy等更专业的库
            # 这里暂时保留一个基于NLTK和TF-IDF的简化版作为示例
            stop_words_list = nltk.corpus.stopwords.words('english')
            vectorizer = TfidfVectorizer(stop_words=stop_words_list, max_features=15)
            tfidf_matrix = vectorizer.fit_transform([text_content])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray().flatten()
            keywords = [feature_names[i] for i in scores.argsort()[-15:][::-1] if scores[i] > 0]
            keyword_scores = {feature_names[i]: round(scores[i], 4) for i in scores.argsort()[-15:][::-1] if scores[i] > 0}

    except Exception as e:
        logger.warning(f"Enhanced keyword extraction failed: {e}")

    # --- Enhanced Sentiment Analysis ---
    sentiment_scores = {}
    sentiment_interpretation = ""
    try:
        if lang == 'zh-cn':
            sentiment = SnowNLP(text_content[:1000]).sentiments  # Analyze more text
            sentiment_scores = {
                'polarity': round(sentiment, 3),
                'pos': round(sentiment, 3),
                'neu': round(abs(sentiment - 0.5) * 2, 3),
                'neg': round(1-sentiment, 3),
                'compound': round(sentiment * 2 - 1, 3)
            }
            # Add interpretation
            if sentiment > 0.7:
                sentiment_interpretation = "非常积极"
            elif sentiment > 0.6:
                sentiment_interpretation = "积极"
            elif sentiment > 0.4:
                sentiment_interpretation = "中性偏积极"
            elif sentiment > 0.3:
                sentiment_interpretation = "中性偏消极"
            else:
                sentiment_interpretation = "消极"
                
        elif lang == 'en':
            analyzer = SentimentIntensityAnalyzer()
            sentiment_scores = analyzer.polarity_scores(text_content[:1000])
            # Round scores for better readability
            sentiment_scores = {k: round(v, 3) for k, v in sentiment_scores.items()}
            
            # Add interpretation based on compound score
            compound = sentiment_scores.get('compound', 0)
            if compound >= 0.5:
                sentiment_interpretation = "Very Positive"
            elif compound >= 0.1:
                sentiment_interpretation = "Positive"
            elif compound >= -0.1:
                sentiment_interpretation = "Neutral"
            elif compound >= -0.5:
                sentiment_interpretation = "Negative"
            else:
                sentiment_interpretation = "Very Negative"
    except Exception as e:
        logger.warning(f"Enhanced sentiment analysis failed: {e}")

    # --- Enhanced Summarization with LLM ---
    summary = ""
    summary_sentences = []
    try:
        # 优先使用大模型生成摘要
        logger.info(f"Attempting to generate summary with LLM for a text of {len(text_content)} chars.")
        summary = asyncio.run(LLMService.generate_summary(text_content))
        logger.info("LLM summary generation successful.")
    except Exception as e:
        logger.error(f"LLM summarization process failed: {e}", exc_info=True)

    # --- Fallback Summarization Logic ---
    try:
        # 如果LLM失败或返回空，则使用降级逻辑
        if not summary or not summary.strip():
            logger.warning("LLM did not provide a summary. Activating fallback summarization.")
            
            # 降级方案1：使用关键词构造摘要
            if keywords:
                key_topics = ", ".join(keywords[:5])
                if lang == 'zh-cn':
                    summary = f"本文的核心议题围绕 {key_topics} 展开。"
                else:
                    summary = f"The core topics of this document revolve around {key_topics}."
                logger.info(f"Fallback summary created from keywords: {summary}")
            
            # 降级方案2：使用原文前几句
            elif sentences:
                summary = " ".join(sentences[:3])
                logger.info("Fallback summary created from first 3 sentences.")

    except Exception as e:
        logger.error(f"Fallback summarization failed: {e}", exc_info=True)
        if not summary:
            summary = "无法生成摘要。"

    # --- Content Analysis Insights ---
    content_insights = {
        "document_structure": {
            "has_questions": "?" in text_content,
            "has_exclamations": "!" in text_content,
            "has_numbers": any(char.isdigit() for char in text_content),
            "paragraph_count": text_content.count('\n\n') + 1
        },
        "language_characteristics": {
            "detected_language": lang,
            "language_confidence": "high" if lang in ['en', 'zh-cn'] else "low",
            "mixed_language": len(set(detect(sent[:50]) if len(sent) > 10 else lang for sent in sentences[:5])) > 1 if sentences else False
        }
    }

    return {
        "analysis_type": "text",
        "detected_language": lang,
        "text_stats": text_stats,
        "keywords": keywords,
        "keyword_scores": keyword_scores,
        "sentiment": sentiment_scores,
        "sentiment_interpretation": sentiment_interpretation,
        "summary": summary,
        "summary_sentences": summary_sentences,
        "content_insights": content_insights,
        "analysis_quality": {
            "keywords_extracted": len(keywords),
            "summary_length": len(summary),
            "analysis_completeness": "high" if keywords and summary and sentiment_scores else "partial"
        }
    }

def perform_tabular_analysis(df: pd.DataFrame) -> dict:
    """
    Performs comprehensive tabular data analysis on a DataFrame.
    Returns detailed statistical analysis and data profiling.
    """
    try:
        logger.info(f"Starting tabular analysis for DataFrame with shape {df.shape}")
        
        # Basic DataFrame information
        basic_info = {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "memory_usage": int(df.memory_usage(deep=True).sum()),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "column_names": df.columns.tolist()
        }
        
        # Data quality assessment
        missing_values = {col: int(val) for col, val in df.isnull().sum().to_dict().items()}
        missing_percentage = {col: float(val) for col, val in (df.isnull().sum() / len(df) * 100).round(2).to_dict().items()}
        
        data_quality = {
            "missing_values": missing_values,
            "missing_percentage": missing_percentage,
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_percentage": round(float(df.duplicated().sum() / len(df) * 100), 2)
        }
        
        # Column-wise analysis
        column_analysis = {}
        for col in df.columns:
            col_data = df[col]
            col_info = {
                "dtype": str(col_data.dtype),
                "non_null_count": int(col_data.count()),
                "null_count": int(col_data.isnull().sum()),
                "unique_count": int(col_data.nunique()),
                "unique_percentage": round(float(col_data.nunique() / len(col_data) * 100), 2)
            }
            
            # Numeric column analysis
            if pd.api.types.is_numeric_dtype(col_data):
                # Helper function to safely convert numeric values
                def safe_numeric_convert(value):
                    if pd.isna(value) or np.isnan(value) or np.isinf(value):
                        return None
                    return round(float(value), 3)
                
                col_info.update({
                    "mean": safe_numeric_convert(col_data.mean()) if not col_data.empty else None,
                    "median": safe_numeric_convert(col_data.median()) if not col_data.empty else None,
                    "std": safe_numeric_convert(col_data.std()) if not col_data.empty else None,
                    "min": convert_to_serializable(col_data.min()) if not col_data.empty else None,
                    "max": convert_to_serializable(col_data.max()) if not col_data.empty else None,
                    "quartiles": {
                        "q25": safe_numeric_convert(col_data.quantile(0.25)) if not col_data.empty else None,
                        "q75": safe_numeric_convert(col_data.quantile(0.75)) if not col_data.empty else None
                    }
                })
            
            # Text/categorical column analysis
            elif pd.api.types.is_object_dtype(col_data):
                # Get most common values (limit to prevent large results)
                value_counts = col_data.value_counts().head(5)
                most_common = {}
                for k, v in value_counts.to_dict().items():
                    # Truncate long strings to prevent JSON bloat
                    key_str = str(k)
                    if len(key_str) > 100:
                        key_str = key_str[:97] + "..."
                    most_common[key_str] = int(v)
                
                col_info.update({
                    "most_common": most_common,
                    "avg_length": round(float(col_data.astype(str).str.len().mean()), 2) if not col_data.empty else None,
                    "max_length": int(col_data.astype(str).str.len().max()) if not col_data.empty else None,
                    "min_length": int(col_data.astype(str).str.len().min()) if not col_data.empty else None
                })
            
            column_analysis[col] = col_info
        
        # Data type distribution
        dtype_counts = df.dtypes.value_counts().to_dict()
        dtype_distribution = {str(k): int(v) for k, v in dtype_counts.items()}
        
        # Generate insights
        insights = []
        
        # Missing data insights
        high_missing_cols = [col for col, pct in data_quality["missing_percentage"].items() if pct > 50]
        if high_missing_cols:
            insights.append(f"警告：以下列缺失数据超过50%: {', '.join(high_missing_cols)}")
        
        # Duplicate data insights
        if data_quality["duplicate_percentage"] > 10:
            insights.append(f"警告：发现{data_quality['duplicate_percentage']}%的重复行")
        
        # High cardinality insights
        high_cardinality_cols = [col for col, info in column_analysis.items() 
                               if info["unique_percentage"] > 95 and info["unique_count"] > 10]
        if high_cardinality_cols:
            insights.append(f"注意：以下列具有高基数（可能是ID列）: {', '.join(high_cardinality_cols)}")
        
        # Numeric vs categorical balance
        numeric_cols = len([col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])])
        categorical_cols = len(df.columns) - numeric_cols
        insights.append(f"数据结构：{numeric_cols}个数值列，{categorical_cols}个分类列")
        
        result = {
            "analysis_type": "tabular",
            "basic_info": basic_info,
            "data_quality": data_quality,
            "column_analysis": column_analysis,
            "dtype_distribution": dtype_distribution,
            "insights": insights,
            "analysis_quality": {
                "completeness": "high" if data_quality["missing_percentage"] else "partial",
                "columns_analyzed": len(column_analysis),
                "total_insights": len(insights)
            }
        }
        
        logger.info(f"Tabular analysis completed successfully. Generated {len(insights)} insights.")
        
        # Check result size and optimize if necessary
        result_json = json.dumps(result, ensure_ascii=False)
        if len(result_json) > 50000:  # 50KB limit
            logger.warning(f"Analysis result is large ({len(result_json)} chars), optimizing...")
            # Reduce column analysis detail for large datasets
            optimized_column_analysis = {}
            for col_name, col_data in result["column_analysis"].items():
                optimized_col_data = {
                    "dtype": col_data["dtype"],
                    "non_null_count": col_data["non_null_count"],
                    "null_count": col_data["null_count"],
                    "unique_count": col_data["unique_count"],
                    "unique_percentage": col_data["unique_percentage"]
                }
                # Add essential stats for numeric columns
                if col_data.get("mean") is not None:
                    optimized_col_data.update({
                        "mean": col_data["mean"],
                        "median": col_data["median"],
                        "std": col_data["std"],
                        "min": col_data["min"],
                        "max": col_data["max"]
                    })
                # Add top 3 most common for categorical columns
                if col_data.get("most_common"):
                    top_3_common = dict(list(col_data["most_common"].items())[:3])
                    optimized_col_data["most_common"] = top_3_common
                
                optimized_column_analysis[col_name] = optimized_col_data
            
            result["column_analysis"] = optimized_column_analysis
            result["optimization_applied"] = True
            logger.info("Analysis result optimized for storage.")
        
        return result
        
    except Exception as e:
        logger.error(f"Tabular analysis failed: {e}", exc_info=True)
        return {
            "analysis_type": "tabular",
            "error": "表格分析失败",
            "details": str(e),
            "basic_info": {
                "rows": len(df) if df is not None else 0,
                "columns": len(df.columns) if df is not None else 0
            }
        }

def perform_image_analysis(image_path: Path) -> dict:
    """
    Performs comprehensive analysis on an image file.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        A dictionary containing analysis results like dimensions, format, phash,
        dominant colors, EXIF data, and intelligent description.
    """
    try:
        with Image.open(image_path) as img:
            # 1. Basic properties
            width, height = img.size
            image_format = img.format
            file_size = image_path.stat().st_size
            
            # 2. Perceptual Hash
            try:
                phash = str(imagehash.phash(img))
            except Exception as e:
                logger.warning(f"Could not compute phash for {image_path}: {e}")
                phash = None

            # 3. Dominant Colors (using KMeans)
            try:
                # Resize for faster processing
                img_small = img.resize((100, 100))
                # Convert to RGB if it's not
                if img_small.mode != 'RGB':
                    img_small = img_small.convert('RGB')
                
                pixels = np.array(img_small.getdata())
                kmeans = KMeans(n_clusters=8, random_state=42, n_init=10).fit(pixels)
                dominant_colors = [f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}" for c in kmeans.cluster_centers_]
            except Exception as e:
                logger.warning(f"Could not determine dominant colors for {image_path}: {e}")
                dominant_colors = []

            # 4. EXIF Data
            exif_data = {}
            try:
                if hasattr(img, '_getexif'):
                    exif_info = img._getexif()
                    if exif_info:
                        for tag_id, value in exif_info.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            # To avoid issues with bytes, decode if possible
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode('utf-8', errors='ignore')
                                except:
                                    value = repr(value)
                            exif_data[str(tag_name)] = str(value) # Ensure keys and values are strings
            except Exception as e:
                logger.warning(f"Could not extract EXIF data from {image_path}: {e}")

            # 5. Intelligent Description using Qwen2.5-VL
            intelligent_analysis = {}
            try:
                from backend.services.image_description_service import ImageDescriptionService
                import asyncio
                
                logger.info(f"Starting intelligent image analysis for {image_path}")
                description_service = ImageDescriptionService()
                
                # 使用asyncio.run来运行异步函数
                description_result = asyncio.run(description_service.generate_description(image_path))
                
                if description_result.get("success", False):
                    intelligent_analysis = {
                        "description": description_result.get("description", ""),
                        "scene_type": description_result.get("parsed_analysis", {}).get("scene_type", "未知"),
                        "mood_tone": description_result.get("parsed_analysis", {}).get("mood_tone", "中性"),
                        "suggested_tags": description_result.get("parsed_analysis", {}).get("suggested_tags", []),
                        "analysis_status": "success"
                    }
                    logger.info("Intelligent image analysis completed successfully")
                else:
                    intelligent_analysis = {
                        "description": description_result.get("description", "无法生成图像描述"),
                        "scene_type": "未知",
                        "mood_tone": "中性",
                        "suggested_tags": [],
                        "analysis_status": "failed",
                        "error": description_result.get("error", "未知错误")
                    }
                    logger.warning(f"Intelligent image analysis failed: {description_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error during intelligent image analysis: {e}", exc_info=True)
                intelligent_analysis = {
                    "description": "智能分析暂时不可用",
                    "scene_type": "未知",
                    "mood_tone": "中性",
                    "suggested_tags": [],
                    "analysis_status": "error",
                    "error": str(e)
                }

            report = {
                "analysis_type": "image",
                "image_properties": {
                    "dimensions": {
                        "width": width,
                        "height": height
                    },
                    "format": img.format,
                    "mode": img.mode,
                    "file_size_bytes": file_size,
                    "phash": phash,
                    "dominant_colors": dominant_colors,
                    "exif_data": exif_data,
                },
                "intelligent_analysis": intelligent_analysis
            }

            return report
            
    except Exception as e:
        logger.error(f"Failed to analyze image {image_path}: {e}", exc_info=True)
        return {
            "error": f"Failed to analyze image: {e}"
        }


def perform_audio_analysis(audio_path: Path) -> dict:
    """
    Performs comprehensive analysis on an audio file.
    
    Args:
        audio_path: Path to the audio file.
        
    Returns:
        A dictionary containing analysis results like duration, sample rate,
        bitrate, format, and basic audio features.
    """
    try:
        logger.info(f"Starting audio analysis for {audio_path}")
        
        # 1. Basic file information
        file_size = audio_path.stat().st_size
        file_extension = audio_path.suffix.lower()
        
        # 2. Metadata extraction using mutagen
        metadata = {}
        audio_info = {}
        
        try:
            # Try to load with mutagen for metadata
            if file_extension == '.mp3':
                audio_file = MP3(audio_path)
            elif file_extension == '.wav':
                audio_file = WAVE(audio_path)
            elif file_extension in ['.m4a', '.mp4']:
                audio_file = MP4(audio_path)
            elif file_extension == '.flac':
                audio_file = FLAC(audio_path)
            else:
                # Fallback to generic mutagen
                audio_file = mutagen.File(audio_path)
            
            if audio_file is not None:
                # Extract metadata
                for key, value in audio_file.items():
                    if isinstance(value, (list, tuple)) and len(value) > 0:
                        metadata[key] = str(value[0])
                    else:
                        metadata[key] = str(value)
                
                # Audio properties
                if hasattr(audio_file, 'info'):
                    info = audio_file.info
                    audio_info = {
                        "duration_seconds": getattr(info, 'length', 0),
                        "bitrate": getattr(info, 'bitrate', 0),
                        "sample_rate": getattr(info, 'sample_rate', 0),
                        "channels": getattr(info, 'channels', 0),
                        "format": file_extension[1:]  # Remove the dot
                    }
                
        except Exception as e:
            logger.warning(f"Could not extract metadata from {audio_path}: {e}")
        
        # 3. Audio feature analysis using librosa
        audio_features = {}
        try:
            # Fix scipy compatibility issue
            import scipy.signal
            if not hasattr(scipy.signal, 'hann'):
                scipy.signal.hann = scipy.signal.windows.hann
            
            # Load audio with librosa - first get full duration
            full_duration = librosa.get_duration(path=audio_path)
            
            # Load audio for feature analysis (limit to 30 seconds for performance)
            y, sr = librosa.load(audio_path, sr=None, duration=min(30, full_duration))
            
            # Basic features
            duration = full_duration  # Use full duration, not truncated
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # MFCC features (first 13 coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            audio_features = {
                "duration_seconds": float(duration),
                "tempo_bpm": float(tempo),
                "sample_rate": int(sr),
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                "mfcc_means": [float(np.mean(mfcc)) for mfcc in mfccs],
                "energy": float(np.sum(y**2) / len(y))  # RMS energy
            }
            
        except Exception as e:
            logger.warning(f"Could not extract audio features from {audio_path}: {e}")
            # Fallback to basic info
            if not audio_info:
                audio_features = {
                    "duration_seconds": 0,
                    "tempo_bpm": 0,
                    "sample_rate": 0,
                    "format": file_extension[1:]
                }
        
        # 4. Generate analysis summary
        analysis_summary = {
            "total_duration": audio_features.get("duration_seconds", audio_info.get("duration_seconds", 0)),
            "audio_quality": "高质量" if audio_info.get("bitrate", 0) > 256 else "标准质量" if audio_info.get("bitrate", 0) > 128 else "低质量",
            "format_info": f"{file_extension[1:].upper()} 格式",
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
        
        # 5. 语音识别处理（如果是音频文件）- 临时简化版本
        speech_analysis = {}
        if file_extension.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.aac']:
            try:
                # 临时方案：跳过音频预处理，直接语音识别
                logger.info(f"🎯 启动简化音频分析（跳过预处理）...")
                
                # 直接使用WhisperService，避免AudioDescriptionService的复杂依赖
                from backend.services.whisper_service import WhisperService
                whisper_service = WhisperService.get_instance()
                
                # 简单的语音识别，没有预处理
                result = whisper_service.transcribe_audio(str(audio_path))
                
                # 修复：根据实际结果判断成功，而不是依赖success字段
                if result and result.get('text', '').strip() and not result.get('error'):
                    speech_text = result.get('text', '')
                    logger.info(f"✅ 语音识别成功，识别文本长度: {len(speech_text)}")
                    
                    # 应用文本优化 - 使用重写的安全版本
                    text_optimization_result = None
                    if True:  # 启用改进的文本优化
                        if speech_text and len(speech_text.strip()) > 0:
                            try:
                                logger.info(f"🧠 开始智能文本优化...")
                                from backend.services.text_optimization_service import TextOptimizationService
                                
                                text_optimizer = TextOptimizationService()
                                optimization_result = text_optimizer.optimize_speech_text(speech_text, 'zh')
                                
                                if optimization_result and optimization_result.get('success', False):
                                    text_optimization_result = optimization_result
                                    logger.info(f"✅ 文本优化成功！")
                                    logger.info(f"📝 原始文本长度: {len(speech_text)}")
                                    logger.info(f"📝 优化文本长度: {len(optimization_result.get('optimized_text', ''))}")
                                    logger.info(f"📝 应用改进: {optimization_result.get('improvements', [])}")
                                else:
                                    logger.warning(f"⚠️ 文本优化失败")
                                    
                            except Exception as e:
                                logger.error(f"❌ 文本优化异常: {str(e)}")
                    
                    # 确定最终展示的文本：暂时直接使用原始文本
                    final_transcribed_text = speech_text
                    if text_optimization_result and text_optimization_result.get('success', False):
                        optimized_text = text_optimization_result.get('optimized_text', '')
                        if optimized_text and optimized_text.strip():
                            final_transcribed_text = optimized_text
                            logger.info(f"✅ 文本优化成功：优化后长度 {len(optimized_text)} 字符")
                            logger.info(f"🔧 应用改进：{text_optimization_result.get('improvements', [])}")
                    else:
                        logger.info(f"🔄 使用原始语音识别结果，长度: {len(speech_text)} 字符")
                    
                    speech_analysis = {
                        'success': True,
                        'transcription': speech_text,  # 原始识别文本
                        'transcribed_text': final_transcribed_text,  # 前端期望的字段，优化后的文本
                        'raw_text': speech_text,  # 原始文本，用于前端对比显示
                        'confidence': result.get('confidence', 0.0),
                        'language': result.get('language', 'unknown'),
                        'text_optimization': text_optimization_result,  # 新增字段
                        'processing_time': result.get('processing_time', 0.0),
                        'model_used': 'whisper-simple'
                    }
                else:
                    error_msg = result.get('error', 'Speech recognition failed') if result else 'No result returned'
                    logger.error(f"❌ 语音识别失败: {error_msg}")
                    speech_analysis = {
                        'success': False,
                        'error': error_msg,
                        'model_used': 'whisper-simple'
                    }
                    
            except Exception as e:
                logger.error(f"❌ 音频分析异常: {str(e)}")
                import traceback
                traceback.print_exc()
                speech_analysis = {
                    'success': False,
                    'error': str(e),
                    'model_used': 'whisper-simple'
                }

        # 6. Enhanced analysis summary with rule-based classification
        enhanced_summary = analysis_summary.copy()
        
        # Rule-based audio type classification
        audio_type = "未知"
        if speech_analysis.get("success") and speech_analysis.get("transcription"):
            if len(speech_analysis["transcription"]) > 50:
                audio_type = "语音/对话"
            else:
                audio_type = "可能包含语音"
        elif audio_features.get("tempo_bpm", 0) > 120:
            audio_type = "快节奏音乐"
        elif audio_features.get("tempo_bpm", 0) > 80:
            audio_type = "中等节奏音乐"
        elif audio_features.get("tempo_bpm", 0) > 0:
            audio_type = "慢节奏音乐"
        elif audio_features.get("energy", 0) < 0.01:
            audio_type = "安静音频"
        else:
            audio_type = "音频内容"
        
        enhanced_summary["audio_type"] = audio_type
        
        # Basic quality assessment based on technical features
        sample_rate = audio_features.get("sample_rate", 0)
        energy = audio_features.get("energy", 0)
        
        if sample_rate >= 44100 and energy > 0.02:
            audio_quality = "高质量"
        elif sample_rate >= 22050 and energy > 0.01:
            audio_quality = "中等质量"
        else:
            audio_quality = "低质量"
            
        enhanced_summary["audio_quality"] = audio_quality
        
        # 文本优化已经在前面执行过了，这里不需要重复执行

        # Combine all results
        result = {
            "analysis_type": "audio",
            "file_info": {
                "file_size_bytes": file_size,
                "format": file_extension[1:],
                "file_path": str(audio_path)
            },
            "metadata": metadata,
            "audio_properties": {**audio_info, **audio_features},
            "analysis_summary": enhanced_summary,
            "speech_recognition": speech_analysis,  # Whisper语音识别结果
            "text_optimization": text_optimization_result  # 新增：智能文本优化结果
        }
        
        logger.info(f"Audio analysis completed successfully for {audio_path}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze audio {audio_path}: {e}", exc_info=True)
        return {
            "analysis_type": "audio",
            "error": f"Failed to analyze audio: {e}",
            "file_info": {
                "file_size_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
                "format": audio_path.suffix[1:] if audio_path.suffix else "unknown"
            }
        }


def perform_video_analysis(video_path: Path) -> dict:
    """
    Performs comprehensive analysis on a video file.
    
    Args:
        video_path: Path to the video file.
        
    Returns:
        A dictionary containing analysis results like duration, resolution,
        frame rate, format, and basic video features.
    """
    try:
        logger.info(f"Starting video analysis for {video_path}")
        
        # 1. Basic file information
        file_size = video_path.stat().st_size
        file_extension = video_path.suffix.lower()
        
        # 2. Enhanced video analysis using OpenCV and moviepy
        video_info = {}
        metadata = {}
        
        try:
            # Primary analysis with OpenCV
            cap = cv2.VideoCapture(str(video_path))
            
            if cap.isOpened():
                # Basic video properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                video_info = {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "frame_count": frame_count,
                    "duration_seconds": duration,
                    "resolution": f"{width}x{height}",
                    "aspect_ratio": round(width / height, 2) if height > 0 else 0
                }
                
                # Enhanced thumbnail generation with better quality
                ret, frame = cap.read()
                if ret:
                    # Create thumbnails directory if it doesn't exist
                    thumbnails_dir = video_path.parent / "thumbnails"
                    thumbnails_dir.mkdir(exist_ok=True)
                    
                    thumbnail_filename = f"thumb_{video_path.stem}.jpg"
                    thumbnail_path = thumbnails_dir / thumbnail_filename
                    
                    # Resize thumbnail to reasonable size (max 400px width)
                    h, w = frame.shape[:2]
                    if w > 400:
                        scale = 400 / w
                        new_w, new_h = int(w * scale), int(h * scale)
                        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    
                    # Save thumbnail with high quality
                    cv2.imwrite(str(thumbnail_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    video_info["thumbnail_path"] = str(thumbnail_path)
                    logger.info(f"Generated thumbnail: {thumbnail_path}")
                
                cap.release()
                
                # Try to get additional metadata with moviepy (fallback)
                try:
                    if MOVIEPY_AVAILABLE:
                        with VideoFileClip(str(video_path)) as clip:
                            if not video_info.get("duration_seconds"):
                                video_info["duration_seconds"] = clip.duration
                            if not video_info.get("fps"):
                                video_info["fps"] = clip.fps
                            
                            # Additional moviepy-specific info
                            video_info["has_audio"] = clip.audio is not None
                            if clip.audio:
                                video_info["audio_duration"] = clip.audio.duration
                            
                            logger.info(f"Enhanced video info with moviepy: duration={clip.duration:.2f}s, has_audio={clip.audio is not None}")
                            
                    else:
                        logger.warning("MoviePy is not available, skipping enhanced video info with moviepy.")
                        
                except Exception as e:
                    logger.warning(f"MoviePy enhancement failed (using OpenCV data): {e}")
                    
            else:
                logger.warning(f"Could not open video file with OpenCV: {video_path}")
                
        except Exception as e:
            logger.warning(f"Could not extract video properties from {video_path}: {e}")
            # Try moviepy as fallback
            try:
                if MOVIEPY_AVAILABLE:
                    with VideoFileClip(str(video_path)) as clip:
                        video_info = {
                            "width": clip.w,
                            "height": clip.h,
                            "fps": clip.fps,
                            "duration_seconds": clip.duration,
                            "resolution": f"{clip.w}x{clip.h}",
                            "aspect_ratio": round(clip.w / clip.h, 2) if clip.h > 0 else 0,
                            "has_audio": clip.audio is not None
                        }
                        logger.info(f"Fallback to moviepy successful: {video_info}")
                else:
                    logger.warning("MoviePy is not available, skipping fallback to moviepy.")
            except Exception as fallback_e:
                logger.error(f"Both OpenCV and moviepy failed: {fallback_e}")
                video_info = {
                    "width": 0,
                    "height": 0,
                    "fps": 0,
                    "duration_seconds": 0,
                    "resolution": "Unknown",
                    "aspect_ratio": 0,
                    "has_audio": False
                }
            
        except Exception as e:
            logger.warning(f"Could not extract video properties from {video_path}: {e}")
        
        # 3. Metadata extraction using mutagen (for some video formats)
        try:
            if file_extension in ['.mp4', '.m4v']:
                video_file = MP4(video_path)
                if video_file is not None:
                    for key, value in video_file.items():
                        if isinstance(value, (list, tuple)) and len(value) > 0:
                            metadata[key] = str(value[0])
                        else:
                            metadata[key] = str(value)
                            
        except Exception as e:
            logger.warning(f"Could not extract metadata from {video_path}: {e}")
        
        # 4. Video quality assessment
        quality_info = {
            "resolution_category": "4K" if video_info.get("height", 0) >= 2160 else 
                                  "Full HD" if video_info.get("height", 0) >= 1080 else 
                                  "HD" if video_info.get("height", 0) >= 720 else 
                                  "SD",
            "frame_rate_category": "高帧率" if video_info.get("fps", 0) >= 60 else 
                                  "标准帧率" if video_info.get("fps", 0) >= 24 else 
                                  "低帧率",
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }
        
        # 5. Video type classification
        duration = video_info.get("duration_seconds", 0)
        video_type = "未知"
        if duration < 30:
            video_type = "短视频"
        elif duration < 300:  # 5 minutes
            video_type = "中等时长视频"
        elif duration < 3600:  # 1 hour
            video_type = "长视频"
        else:
            video_type = "超长视频"
        
        # 6. Generate analysis summary
        analysis_summary = {
            "duration_formatted": f"{int(duration // 60)}分{int(duration % 60)}秒",
            "video_type": video_type,
            "quality_summary": f"{quality_info['resolution_category']} {quality_info['frame_rate_category']}",
            "format_info": f"{file_extension[1:].upper()} 格式"
        }
        
        # Combine all results
        result = {
            "analysis_type": "video",
            "file_info": {
                "file_size_bytes": file_size,
                "format": file_extension[1:],
                "file_path": str(video_path)
            },
            "metadata": metadata,
            "video_properties": video_info,
            "quality_info": quality_info,
            "analysis_summary": analysis_summary
        }
        
        logger.info(f"Video analysis completed successfully for {video_path}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze video {video_path}: {e}", exc_info=True)
        return {
            "analysis_type": "video",
            "error": f"Failed to analyze video: {e}",
            "file_info": {
                "file_size_bytes": video_path.stat().st_size if video_path.exists() else 0,
                "format": video_path.suffix[1:] if video_path.suffix else "unknown"
            }
        }


def convert_to_serializable(obj):
    """
    Recursively converts non-serializable objects (like numpy types)
    """
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        # Handle NaN and infinity values
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

def generate_fallback_profile(df: pd.DataFrame) -> dict:
    """
    Generates a basic, guaranteed-to-work profile using pandas.describe().
    """
    logger.warning("ydata-profiling failed, generating a fallback profile.")
    try:
        describe = df.describe(include='all').to_dict()
        fallback_report = {
            "table": {
                "n": int(len(df)),
                "n_var": int(len(df.columns)),
                "memory_size": int(df.memory_usage(deep=True).sum()),
                "n_duplicates": int(df.duplicated().sum()),
            },
            "variables": {},
            "fallback": True, # Flag to indicate this is not a full report
        }
        for col, stats in describe.items():
            fallback_report["variables"][col] = {
                k: convert_to_serializable(v) for k, v in stats.items()
            }
        return fallback_report
    except Exception as e:
        logger.error(f"Fallback profiling also failed: {e}", exc_info=True)
        return {"error": "Both profiling and fallback failed.", "details": str(e)}


@celery_app.task(
    bind=True,
    autoretry_for=(),  # 不自动重试任何错误，手动控制重试逻辑
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 2}  # 减少重试次数
)
def run_profiling_task(self, data_source_id: int):
    """
    Main Celery task to perform profiling on a data source.
    Handles different file types and updates the database with results.
    """
    logger.info(f"Starting profiling task for data_source_id: {data_source_id}")
    db = next(get_sync_db())
    
    data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
    if not data_source:
        logger.error(f"DataSource with id {data_source_id} not found.")
        return

    # Update status to 'in_progress'
    data_source.profile_status = ProfileStatusEnum.in_progress
    db.commit()

    try:
        file_path = Path(settings.upload_dir) / data_source.file_path
        logger.info(f"Processing file: {file_path} of type {data_source.file_type}")

        profile_result = {}
        text_content_for_analysis = ""

        # Handle different analysis categories
        if data_source.analysis_category == AnalysisCategory.TEXTUAL:
            # Text-based file handling
            if not file_path.exists():
                raise FileNotFoundError(f"File not found at {file_path}")

            if data_source.file_type == 'docx':
                text_content_for_analysis = extract_text_from_docx(file_path)
            elif data_source.file_type == 'pdf':
                text_content_for_analysis = extract_text_from_pdf(file_path)
            elif data_source.file_type == 'md':
                text_content_for_analysis = extract_text_from_md(file_path)
            elif data_source.file_type == 'txt':
                text_content_for_analysis = file_path.read_text(encoding='utf-8')
            else:
                logger.warning(f"Unsupported text file type: {data_source.file_type}")
                text_content_for_analysis = ""

            if text_content_for_analysis:
                # We need to wrap the text content in a DataFrame for perform_text_analysis
                df_for_analysis = pd.DataFrame({'text': [text_content_for_analysis]})
                profile_result = perform_text_analysis(df_for_analysis)
            else:
                logger.warning(f"No text content extracted from {file_path}. Skipping text analysis.")

        elif data_source.analysis_category == AnalysisCategory.TABULAR:
            # Tabular data handling (CSV files)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found at {file_path}")
            
            if data_source.file_type == 'csv':
                df = pd.read_csv(file_path)
                profile_result = perform_tabular_analysis(df)
            else:
                logger.warning(f"Unsupported tabular file type: {data_source.file_type}")
                profile_result = {"error": f"Unsupported tabular file type: {data_source.file_type}"}

        elif data_source.analysis_category == AnalysisCategory.IMAGE:
            # Image file handling
            if data_source.file_type in ['jpg', 'jpeg', 'png']:
                profile_result = perform_image_analysis(file_path)
            else:
                logger.warning(f"Unsupported image file type: {data_source.file_type}")
                profile_result = {"error": f"Unsupported image file type: {data_source.file_type}"}

        elif data_source.analysis_category == AnalysisCategory.AUDIO:
            # Audio file handling
            if data_source.file_type in ['mp3', 'wav', 'm4a', 'flac']:
                profile_result = perform_audio_analysis(file_path)
            else:
                logger.warning(f"Unsupported audio file type: {data_source.file_type}")
                profile_result = {"error": f"Unsupported audio file type: {data_source.file_type}"}

        elif data_source.analysis_category == AnalysisCategory.VIDEO:
            # Video file handling with basic analysis for profiling
            if data_source.file_type in ['mp4', 'avi', 'mov', 'm4v', 'mkv', 'wmv', 'flv', 'webm', '3gp']:
                # 使用基础视频分析进行profiling
                profile_result = perform_video_analysis(file_path)
            else:
                logger.warning(f"Unsupported video file type: {data_source.file_type}")
                profile_result = {"error": f"Unsupported video file type: {data_source.file_type}"}
        
        else:
            logger.warning(f"Unsupported analysis category: {data_source.analysis_category}")
            raise ValueError(f"Unsupported analysis category: {data_source.analysis_category}")

        # --- Step 3: Save results to the database ---
        if profile_result:
            # Save analysis results to MongoDB based on analysis type
            if data_source.analysis_category == AnalysisCategory.TEXTUAL and "error" not in profile_result:
                mongo_service.save_text_analysis_results(data_source_id, profile_result)
            elif data_source.analysis_category == AnalysisCategory.TABULAR and "error" not in profile_result:
                mongo_service.save_tabular_analysis_results(data_source_id, profile_result)
            elif data_source.analysis_category == AnalysisCategory.AUDIO and "error" not in profile_result:
                mongo_service.save_audio_analysis_results(data_source_id, profile_result)
            elif data_source.analysis_category == AnalysisCategory.VIDEO and "error" not in profile_result:
                mongo_service.save_video_analysis_results(data_source_id, profile_result)
            
            # For image analysis, save image hash to the main database
            if data_source.analysis_category == AnalysisCategory.IMAGE and "error" not in profile_result:
                data_source.image_hash = profile_result.get("image_hash")
            
            data_source.profiling_result = profile_result
        
        data_source.profile_status = ProfileStatusEnum.completed
        db.commit()

        logger.info(f"Profiling task completed successfully for data source {data_source_id}.")
        return {"status": "completed", "report_json": profile_result}

    except Exception as e:
        logger.error(f"A critical error occurred in profiling task for {data_source_id}: {e}", exc_info=True)
        if data_source:
             data_source.profile_status = ProfileStatusEnum.failed
             db.commit()

        if hasattr(self, 'request') and self.request.id:
            self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        
        raise
    finally:
        if db:
            db.close() 

@celery_app.task(
    bind=True,
    autoretry_for=(),  # 不自动重试任何错误，手动控制重试逻辑
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 0},  # 🔥 禁用自动重试，防止重复执行
    acks_late=True,  # 任务完成后才确认，避免中断导致重投递
    reject_on_worker_lost=False,  # worker丢失时不重新投递
    task_ignore_result=False,  # 保留结果用于幂等性检查
)
def run_video_deep_analysis_task(self, video_analysis_id: int):
    """
    运行视频深度分析任务（GPU加速版本）
    """
    logger.info(f"Starting video deep analysis task for video_analysis_id: {video_analysis_id}")
    db = next(get_sync_db())
    
    try:
        # 导入视频分析相关模块
        from backend.models.video_analysis import VideoAnalysis, VideoAnalysisStatus
        from backend.services.video_analysis_service import VideoAnalysisService
        
        # 获取视频分析记录
        video_analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == video_analysis_id).first()
        if not video_analysis:
            logger.error(f"VideoAnalysis with id {video_analysis_id} not found.")
            return {"status": "failed", "error": "VideoAnalysis not found"}
        
        # 获取关联的数据源
        data_source = db.query(DataSource).filter(DataSource.id == video_analysis.data_source_id).first()
        if not data_source:
            logger.error(f"DataSource with id {video_analysis.data_source_id} not found.")
            return {"status": "failed", "error": "DataSource not found"}
        
        # 更新状态为进行中
        video_analysis.status = VideoAnalysisStatus.IN_PROGRESS
        db.commit()
        
        # 创建视频分析服务实例
        analysis_service = VideoAnalysisService()
        
        # 执行深度分析
        logger.info(f"Starting enhanced video analysis for: {data_source.name}")
        
        # 使用asyncio运行异步分析
        import asyncio
        
        # 创建新的事件循环（在Celery worker中需要）
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 执行增强分析，添加进度更新回调
        def update_progress(phase: str, progress: float, message: str = ""):
            """更新分析进度"""
            try:
                # 更新数据库中的进度信息
                video_analysis.current_phase = phase
                video_analysis.progress_percentage = progress
                video_analysis.progress_message = message
                video_analysis.updated_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"进度更新: {phase} - {progress:.1f}% - {message}")
            except Exception as e:
                logger.error(f"进度更新失败: {e}")
        
        # 执行增强分析
        analysis_result = loop.run_until_complete(
            analysis_service.perform_enhanced_analysis(data_source, video_analysis, update_progress)
        )
        
        # 检查分析结果
        if "error" in analysis_result:
            # 分析失败
            video_analysis.status = VideoAnalysisStatus.FAILED
            video_analysis.error_message = analysis_result.get("error", "Unknown error")
            db.commit()
            
            logger.error(f"Video deep analysis failed for {video_analysis_id}: {analysis_result['error']}")
            return {
                "status": "failed", 
                "error": analysis_result["error"],
                "video_analysis_id": video_analysis_id
            }
        
        # 分析成功，更新数据库
        video_analysis.status = VideoAnalysisStatus.COMPLETED
        
        # 保存分析结果到各个字段
        visual_analysis = analysis_result.get("visual_analysis", {})
        audio_analysis = analysis_result.get("audio_analysis", {})
        multimodal_fusion = analysis_result.get("multimodal_fusion", {})
        
        # 更新视频分析字段
        if visual_analysis.get("scene_detection"):
            video_analysis.scene_count = len(visual_analysis["scene_detection"].get("scene_changes", []))
        
        if visual_analysis.get("frame_extraction"):
            key_frames_info = visual_analysis["frame_extraction"].get("key_frames_info", [])
            # 确保key_frames是字典格式
            if isinstance(key_frames_info, list):
                video_analysis.key_frames = {"frames": key_frames_info, "count": len(key_frames_info)}
            else:
                video_analysis.key_frames = key_frames_info
        
        if visual_analysis.get("visual_themes"):
            video_analysis.visual_themes = list(visual_analysis["visual_themes"])
        
        if visual_analysis.get("detected_objects"):
            # 转换为字典列表格式
            detected_objects = visual_analysis["detected_objects"]
            if isinstance(detected_objects, list) and detected_objects:
                if isinstance(detected_objects[0], str):
                    # 如果是字符串列表，转换为字典列表
                    video_analysis.visual_objects = [
                        {"name": obj, "confidence": 1.0, "category": "detected"} 
                        for obj in detected_objects
                    ]
                else:
                    # 如果已经是字典列表，直接使用
                    video_analysis.visual_objects = detected_objects
            else:
                video_analysis.visual_objects = []
        
        if visual_analysis.get("scene_changes"):
            scene_changes = visual_analysis["scene_changes"]
            # 确保scene_changes是字典列表格式
            if isinstance(scene_changes, list):
                video_analysis.scene_changes = [
                    {"timestamp": change, "type": "scene_change"} if isinstance(change, (int, float))
                    else change for change in scene_changes
                ]
            else:
                video_analysis.scene_changes = scene_changes
        
        if audio_analysis.get("enhanced_speech", {}).get("segments"):
            video_analysis.speech_segments = audio_analysis["enhanced_speech"]["segments"]
        
        if audio_analysis.get("semantic_analysis", {}).get("topics"):
            video_analysis.audio_themes = audio_analysis["semantic_analysis"]["topics"]
        
        if audio_analysis.get("semantic_analysis", {}).get("emotion_timeline"):
            video_analysis.emotion_timeline = audio_analysis["semantic_analysis"]["emotion_timeline"]
        
        if audio_analysis.get("enhanced_speech", {}).get("full_text"):
            video_analysis.transcription = audio_analysis["enhanced_speech"]["full_text"]
        
        if multimodal_fusion.get("story_analysis", {}).get("story_segments"):
            video_analysis.story_segments = multimodal_fusion["story_analysis"]["story_segments"]
        
        if multimodal_fusion.get("story_analysis", {}).get("key_moments"):
            video_analysis.key_moments = multimodal_fusion["story_analysis"]["key_moments"]
        
        if multimodal_fusion.get("comprehensive_understanding", {}).get("summary"):
            video_analysis.comprehensive_summary = multimodal_fusion["comprehensive_understanding"]["summary"]
        
        # 合并所有标签
        content_tags = set()
        if visual_analysis.get("visual_themes"):
            content_tags.update(visual_analysis["visual_themes"])
        if audio_analysis.get("semantic_analysis", {}).get("topics"):
            content_tags.update(audio_analysis["semantic_analysis"]["topics"])
        if multimodal_fusion.get("semantic_correlation", {}).get("cross_modal_tags"):
            content_tags.update(multimodal_fusion["semantic_correlation"]["cross_modal_tags"])
        
        video_analysis.content_tags = list(content_tags)
        
        # 记录处理时间和模型版本
        video_analysis.processing_time = analysis_result.get("analysis_metadata", {}).get("total_processing_time", 0)
        video_analysis.model_versions = {
            "qwen_vl": "2.5-VL-7B",
            "whisper": "large-v3",
            "analysis_version": "1.0"
        }
        
        # 保存完整结果到MongoDB
        mongo_service.save_video_deep_analysis_results(video_analysis_id, analysis_result)

        # 🔥 新增：将关键结果同步到PostgreSQL
        try:
            # 从分析结果中提取关键信息用于PostgreSQL
            final_integration = analysis_result.get("multimodal_fusion", {}).get("final_integration", {})
            visual_analysis = analysis_result.get("visual_analysis", {})
            audio_analysis = analysis_result.get("audio_analysis", {})
            scene_detection = analysis_result.get("scene_detection", {})
            
            # 更新PostgreSQL中的video_analyses表关键字段
            comprehensive_summary = final_integration.get("story_narrative", "分析完成")
            if comprehensive_summary and comprehensive_summary != "多模态整合失败":
                video_analysis.comprehensive_summary = comprehensive_summary[:2000]  # 限制长度
            else:
                video_analysis.comprehensive_summary = "视频深度分析已完成，包含场景分析、语音识别和多模态融合。"
            
            # 处理content_tags - 从key_moments提取
            key_moments_data = final_integration.get("key_moments", [])
            if isinstance(key_moments_data, list) and key_moments_data:
                video_analysis.content_tags = key_moments_data[:20]  # 限制数量
            else:
                video_analysis.content_tags = ["视频分析", "场景检测", "语音识别", "多模态融合"]
            
            # 构建故事片段数据
            story_segments = []
            temporal_segments = analysis_result.get("multimodal_fusion", {}).get("timeline_alignment", {}).get("temporal_segments", [])
            for i, segment in enumerate(temporal_segments[:10]):  # 限制数量
                story_segments.append({
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "content": segment.get("audio_content", "")[:500],  # 限制长度
                    "visual_objects": segment.get("detected_objects", [])[:5],
                    "segment_type": segment.get("segment_type", "mixed")
                })
            video_analysis.story_segments = story_segments if story_segments else []
            
            # 构建关键时刻数据
            key_moments = []
            sync_events = analysis_result.get("multimodal_fusion", {}).get("timeline_alignment", {}).get("sync_events", [])
            for event in sync_events[:10]:  # 限制数量
                key_moments.append({
                    "timestamp": event.get("timestamp", 0),
                    "event_type": event.get("sync_type", "unknown"),
                    "description": f"同步事件: {event.get('sync_type', 'N/A')}",
                    "confidence": event.get("sync_confidence", 0.5)
                })
            video_analysis.key_moments = key_moments if key_moments else []
            
            # 更新分析统计
            video_analysis.scene_count = scene_detection.get("total_scenes", 0) or len(scene_detection.get("scene_sequences", []))
            
            # 处理key_frames
            frame_numbers = [frame.get("frame_number") for frame in visual_analysis.get("frame_analyses", []) if frame.get("frame_number") is not None]
            video_analysis.key_frames = frame_numbers[:20] if frame_numbers else []
            
            # 处理visual_themes和visual_objects
            video_analysis.visual_themes = visual_analysis.get("visual_themes", [])[:10] if visual_analysis.get("visual_themes") else []
            video_analysis.visual_objects = visual_analysis.get("detected_objects", [])[:20] if visual_analysis.get("detected_objects") else []
            
            # 处理speech_segments
            speech_segments = []
            enhanced_recognition = audio_analysis.get("enhanced_recognition", {})
            if enhanced_recognition and enhanced_recognition.get("speech_segments"):
                for seg in enhanced_recognition.get("speech_segments", [])[:15]:
                    speech_segments.append({
                        "start_time": seg.get("start_time", 0),
                        "end_time": seg.get("end_time", 0), 
                        "text": seg.get("text", "")[:200],
                        "confidence": seg.get("confidence", 0)
                    })
            video_analysis.speech_segments = speech_segments
            
            # 更新处理元数据
            video_analysis.processing_time = analysis_result.get("analysis_metadata", {}).get("total_processing_time", 0)
            video_analysis.model_versions = {
                "vision": "qwen2.5vl:7b",
                "audio": "whisper-large-v3", 
                "llm": "deepseek-r1:8b"
            }
            
            logger.info(f"Successfully synchronized video deep analysis results to PostgreSQL for video_analysis_id: {video_analysis_id}")
            logger.info(f"Synced data: scene_count={video_analysis.scene_count}, key_frames_count={len(video_analysis.key_frames)}, visual_themes_count={len(video_analysis.visual_themes)}, speech_segments_count={len(video_analysis.speech_segments)}")
            
        except Exception as sync_error:
            logger.error(f"Failed to synchronize results to PostgreSQL for video_analysis_id {video_analysis_id}: {sync_error}", exc_info=True)
            # 继续执行，不因同步失败而中断整个任务

        # 提交数据库更改
        db.commit()
        
        logger.info(f"Video deep analysis completed successfully for video_analysis_id: {video_analysis_id}")
        return {
            "status": "completed", 
            "video_analysis_id": video_analysis_id,
            "analysis_result": {
                "scene_count": video_analysis.scene_count,
                "key_frames_count": len(video_analysis.key_frames) if video_analysis.key_frames else 0,
                "visual_themes_count": len(video_analysis.visual_themes) if video_analysis.visual_themes else 0,
                "speech_segments_count": len(video_analysis.speech_segments) if video_analysis.speech_segments else 0,
                "story_segments_count": len(video_analysis.story_segments) if video_analysis.story_segments else 0,
                "analysis_phases": analysis_result.get("analysis_metadata", {}).get("phases_completed", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Video deep analysis task failed for {video_analysis_id}: {e}", exc_info=True)
        
        # 判断是否应该重试
        error_message = str(e)
        should_retry = False
        
        # 只对网络相关或临时性错误进行重试
        if any(keyword in error_message.lower() for keyword in [
            'connection', 'timeout', 'network', 'temporary', 'retry'
        ]):
            should_retry = True
        
        # 对于数据序列化错误、模型错误等，不进行重试
        if any(keyword in error_message.lower() for keyword in [
            'documents must have only string keys', 'serialization', 'bson.errors',
            'invalid document', 'model not found', 'cuda out of memory'
        ]):
            should_retry = False
        
        # 更新失败状态
        try:
            video_analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == video_analysis_id).first()
            if video_analysis:
                video_analysis.status = VideoAnalysisStatus.FAILED
                video_analysis.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update video analysis status: {db_error}")
        
        # 如果应该重试且还有重试次数
        if should_retry and self.request.retries < self.max_retries:
            logger.info(f"Retrying video analysis task for {video_analysis_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1), exc=e)
        
        return {
            "status": "failed",
            "error": str(e),
            "video_analysis_id": video_analysis_id
        }
    finally:
        db.close() 