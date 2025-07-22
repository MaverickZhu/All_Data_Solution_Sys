"""
Service for interacting with MongoDB for analysis results.
"""
import logging
from pymongo import MongoClient
from backend.core.config import settings

logger = logging.getLogger(__name__)

class MongoService:
    _client = None
    _db = None

    @classmethod
    def _get_db(cls):
        """Initializes and returns the database connection."""
        if cls._client is None:
            try:
                cls._client = MongoClient(settings.mongodb_url)
                cls._db = cls._client.get_database("multimodal_analysis")
                logger.info("Successfully connected to MongoDB.")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
                raise
        return cls._db
    
    @staticmethod
    def _sanitize_for_mongodb(obj):
        """
        递归清理数据以确保MongoDB兼容性：
        1. 转换numpy类型为Python原生类型
        2. 确保字典键为字符串并移除NULL字节
        3. 处理字符串中的NULL字节
        4. 处理其他MongoDB不支持的类型
        """
        import numpy as np
        
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            # 处理NaN和无穷大值
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            # 确保所有字典键都是字符串，移除NULL字节，这对MongoDB很重要
            sanitized_dict = {}
            for key, value in obj.items():
                # 清理键名：转为字符串并移除NULL字节
                clean_key = str(key).replace('\x00', '').replace('\0', '')
                if not clean_key:  # 如果键为空，使用默认键
                    clean_key = 'unknown_key'
                sanitized_dict[clean_key] = MongoService._sanitize_for_mongodb(value)
            return sanitized_dict
        elif isinstance(obj, list):
            return [MongoService._sanitize_for_mongodb(item) for item in obj]
        elif isinstance(obj, str):
            # 移除字符串中的NULL字节
            return obj.replace('\x00', '').replace('\0', '')
        elif obj is None:
            return None
        elif isinstance(obj, (int, float, bool)):
            return obj
        else:
            # 对于其他类型，转换为字符串并清理NULL字节
            try:
                return str(obj).replace('\x00', '').replace('\0', '')
            except:
                return None

    @classmethod
    def save_text_analysis_results(cls, data_source_id: int, analysis_data: dict):
        """
        Saves or updates text analysis results in the 'text_analysis_results' collection.

        Args:
            data_source_id: The ID of the data source from PostgreSQL.
            analysis_data: A dictionary containing keywords, summary, sentiment, etc.
        """
        try:
            db = cls._get_db()
            collection = db.text_analysis_results # Using a dedicated collection for clarity

            # 清理数据以确保MongoDB兼容性
            sanitized_data = cls._sanitize_for_mongodb(analysis_data)

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": sanitized_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new text analysis result for data_source_id: {data_source_id}")
            elif result.modified_count > 0:
                logger.info(f"Updated text analysis result for data_source_id: {data_source_id}")
            else:
                logger.info(f"No changes made to text analysis result for data_source_id: {data_source_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to save analysis results for data_source_id {data_source_id} to MongoDB: {e}", exc_info=True)
            return False

    @classmethod
    def get_text_analysis_results(cls, data_source_id: int) -> dict:
        """
        Retrieves text analysis results for a given data source ID.
        """
        try:
            db = cls._get_db()
            collection = db.text_analysis_results
            result = collection.find_one({"data_source_id": data_source_id})
            
            if result:
                # Remove the internal MongoDB '_id' before returning
                result.pop('_id', None)
                logger.debug(f"Found text analysis result for data_source_id: {data_source_id}")
                return result
            else:
                logger.debug(f"No text analysis result found for data_source_id: {data_source_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get analysis results for data_source_id {data_source_id} from MongoDB: {e}", exc_info=True)
            return {}

    @classmethod
    def save_tabular_analysis_results(cls, data_source_id: int, analysis_data: dict):
        """
        Saves or updates tabular analysis results in the 'tabular_analysis_results' collection.

        Args:
            data_source_id: The ID of the data source from PostgreSQL.
            analysis_data: A dictionary containing statistical analysis, data quality metrics, etc.
        """
        try:
            db = cls._get_db()
            collection = db.tabular_analysis_results

            # 清理数据以确保MongoDB兼容性
            sanitized_data = cls._sanitize_for_mongodb(analysis_data)

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": sanitized_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new tabular analysis result for data_source_id: {data_source_id}")
            elif result.modified_count > 0:
                logger.info(f"Updated tabular analysis result for data_source_id: {data_source_id}")
            else:
                logger.info(f"No changes made to tabular analysis result for data_source_id: {data_source_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to save tabular analysis results for data_source_id {data_source_id} to MongoDB: {e}", exc_info=True)
            return False

    @classmethod
    def get_tabular_analysis_results(cls, data_source_id: int) -> dict:
        """
        Retrieves tabular analysis results for a given data source ID.
        """
        try:
            db = cls._get_db()
            collection = db.tabular_analysis_results
            result = collection.find_one({"data_source_id": data_source_id})
            
            if result:
                # Remove the internal MongoDB '_id' before returning
                result.pop('_id', None)
                logger.debug(f"Found tabular analysis result for data_source_id: {data_source_id}")
                return result
            else:
                logger.debug(f"No tabular analysis result found for data_source_id: {data_source_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get tabular analysis results for data_source_id {data_source_id} from MongoDB: {e}", exc_info=True)
            return {}

    @classmethod
    def save_audio_analysis_results(cls, data_source_id: int, analysis_data: dict):
        """
        Saves or updates audio analysis results in the 'audio_analysis_results' collection.

        Args:
            data_source_id: The ID of the data source from PostgreSQL.
            analysis_data: A dictionary containing audio features, speech recognition, metadata, etc.
        """
        try:
            db = cls._get_db()
            collection = db.audio_analysis_results

            # 清理数据以确保MongoDB兼容性
            sanitized_data = cls._sanitize_for_mongodb(analysis_data)

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": sanitized_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new audio analysis result for data_source_id: {data_source_id}")
            elif result.modified_count > 0:
                logger.info(f"Updated audio analysis result for data_source_id: {data_source_id}")
            else:
                logger.info(f"No changes made to audio analysis result for data_source_id: {data_source_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to save audio analysis results for data_source_id {data_source_id} to MongoDB: {e}", exc_info=True)
            return False

    @classmethod
    def get_audio_analysis_results(cls, data_source_id: int) -> dict:
        """
        Retrieves audio analysis results for a given data source ID.
        """
        try:
            db = cls._get_db()
            collection = db.audio_analysis_results
            result = collection.find_one({"data_source_id": data_source_id})
            
            if result:
                # Remove the internal MongoDB '_id' before returning
                result.pop('_id', None)
                logger.debug(f"Found audio analysis result for data_source_id: {data_source_id}")
                return result
            else:
                logger.debug(f"No audio analysis result found for data_source_id: {data_source_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get audio analysis results for data_source_id {data_source_id} from MongoDB: {e}", exc_info=True)
            return {}

    @classmethod
    def save_video_analysis_results(cls, data_source_id: int, analysis_data: dict):
        """
        Saves or updates video analysis results in the 'video_analysis_results' collection.

        Args:
            data_source_id: The ID of the data source from PostgreSQL.
            analysis_data: A dictionary containing video properties, metadata, content analysis, etc.
        """
        try:
            db = cls._get_db()
            collection = db.video_analysis_results

            # 清理数据以确保MongoDB兼容性
            sanitized_data = cls._sanitize_for_mongodb(analysis_data)

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": sanitized_data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new video analysis result for data_source_id: {data_source_id}")
            elif result.modified_count > 0:
                logger.info(f"Updated video analysis result for data_source_id: {data_source_id}")
            else:
                logger.info(f"No changes made to video analysis result for data_source_id: {data_source_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to save video analysis results for data_source_id {data_source_id} to MongoDB: {e}", exc_info=True)
            return False

    @classmethod
    def get_video_analysis_results(cls, data_source_id: int) -> dict:
        """
        Retrieves video analysis results for a given data source ID.
        """
        try:
            db = cls._get_db()
            collection = db.video_analysis_results
            result = collection.find_one({"data_source_id": data_source_id})
            
            if result:
                # Remove the internal MongoDB '_id' before returning
                result.pop('_id', None)
                logger.debug(f"Found video analysis result for data_source_id: {data_source_id}")
                return result
            else:
                logger.debug(f"No video analysis result found for data_source_id: {data_source_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get video analysis results for data_source_id {data_source_id} from MongoDB: {e}", exc_info=True)
            return {}

    @classmethod
    def save_video_deep_analysis_results(cls, video_analysis_id: int, analysis_data: dict):
        """
        Saves video deep analysis results in the 'video_deep_analysis_results' collection.

        Args:
            video_analysis_id: The ID of the video analysis record from PostgreSQL.
            analysis_data: A dictionary containing comprehensive multimodal analysis results.
        """
        try:
            db = cls._get_db()
            collection = db.video_deep_analysis_results

            # 清理数据以确保MongoDB兼容性
            analysis_data = cls._sanitize_for_mongodb(analysis_data)

            # Prepare analysis data with metadata
            analysis_document = {
                "video_analysis_id": video_analysis_id,
                "analysis_type": "deep_multimodal",
                "analysis_timestamp": analysis_data.get("analysis_metadata", {}).get("processing_timestamp"),
                "visual_analysis": analysis_data.get("visual_analysis", {}),
                "scene_detection": analysis_data.get("scene_detection", {}),
                "frame_extraction": analysis_data.get("frame_extraction", {}),
                "audio_analysis": analysis_data.get("audio_analysis", {}),
                "multimodal_fusion": analysis_data.get("multimodal_fusion", {}),
                "analysis_metadata": analysis_data.get("analysis_metadata", {}),
                "errors": analysis_data.get("errors", [])
            }

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the video_analysis_id.
            result = collection.update_one(
                {"video_analysis_id": video_analysis_id},
                {"$set": analysis_document},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new video deep analysis result for video_analysis_id: {video_analysis_id}")
            elif result.modified_count > 0:
                logger.info(f"Updated video deep analysis result for video_analysis_id: {video_analysis_id}")
            else:
                logger.info(f"No changes made to video deep analysis result for video_analysis_id: {video_analysis_id}")

            return True
        except Exception as e:
            logger.error(f"Failed to save video deep analysis results for video_analysis_id {video_analysis_id} to MongoDB: {e}", exc_info=True)
            return False

    @classmethod
    def get_video_deep_analysis_results(cls, video_analysis_id: int) -> dict:
        """
        Retrieves video deep analysis results for a given video analysis ID.
        """
        try:
            db = cls._get_db()
            collection = db.video_deep_analysis_results
            result = collection.find_one({"video_analysis_id": video_analysis_id})
            
            if result:
                # Remove the internal MongoDB '_id' before returning
                result.pop('_id', None)
                logger.debug(f"Found video deep analysis result for video_analysis_id: {video_analysis_id}")
                return result
            else:
                logger.debug(f"No video deep analysis result found for video_analysis_id: {video_analysis_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get video deep analysis results for video_analysis_id {video_analysis_id} from MongoDB: {e}", exc_info=True)
            return {}

mongo_service = MongoService() 