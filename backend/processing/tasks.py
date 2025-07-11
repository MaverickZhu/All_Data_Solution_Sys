import logging
from pathlib import Path
import json
import pandas as pd
import numpy as np
import asyncio # 引入asyncio

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
from backend.models.data_source import DataSource, ProfileStatusEnum
from backend.core.config import settings
from backend.semantic_processing.embedding_service import EmbeddingService
from backend.services.mongo_service import mongo_service
from backend.services.llm_service import LLMService # 引入LLMService

logger = logging.getLogger("ml")

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

def perform_image_analysis(image_path: Path) -> dict:
    """
    Performs basic image analysis, generating a perceptual hash.
    """
    try:
        with Image.open(image_path) as img:
            img_hash = imagehash.phash(img)
            return {
                "analysis_type": "image",
                "image_hash": str(img_hash),
                "resolution": {
                    "width": img.width,
                    "height": img.height
                },
                "format": img.format
            }
    except Exception as e:
        logger.warning(f"Image analysis failed for {image_path}: {e}")
        return {
            "analysis_type": "image",
            "error": "Failed to analyze image.",
            "details": str(e)
        }

def convert_to_serializable(obj):
    """Convert numpy/pandas types to Python native types for JSON serialization."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
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
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={'max_retries': 3}
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

        # Extended text-based file handling
        if data_source.file_type in ['csv', 'txt', 'docx', 'pdf', 'md']:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found at {file_path}")

            if data_source.file_type == 'docx':
                text_content_for_analysis = extract_text_from_docx(file_path)
            elif data_source.file_type == 'pdf':
                text_content_for_analysis = extract_text_from_pdf(file_path)
            elif data_source.file_type == 'md':
                text_content_for_analysis = extract_text_from_md(file_path)
            elif data_source.file_type == 'csv':
                df = pd.read_csv(file_path)
                # For CSV, we'll use the first column for text analysis by default
                if not df.empty:
                    text_content_for_analysis = " ".join(df.iloc[:, 0].astype(str).tolist())
            elif data_source.file_type == 'txt':
                text_content_for_analysis = file_path.read_text(encoding='utf-8')

            if text_content_for_analysis:
                # We need to wrap the text content in a DataFrame for perform_text_analysis
                df_for_analysis = pd.DataFrame({'text': [text_content_for_analysis]})
                profile_result = perform_text_analysis(df_for_analysis)
            else:
                logger.warning(f"No text content extracted from {file_path}. Skipping text analysis.")

        # Image file handling
        elif data_source.file_type in ['jpg', 'jpeg', 'png']:
            profile_result = perform_image_analysis(file_path)
        
        else:
            logger.warning(f"Unsupported data source type: {data_source.file_type}")
            raise ValueError(f"Unsupported file type: {data_source.file_type}")

        # --- Step 3: Save results to the database ---
        if profile_result:
            # For text analysis, save to MongoDB
            if data_source.file_type == 'txt':
                 mongo_service.save_text_analysis_results(data_source_id, profile_result)
            
            if data_source.file_type in ['jpg', 'jpeg', 'png'] and "error" not in profile_result:
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