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

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": analysis_data},
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

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": analysis_data},
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

            # Use update_one with upsert=True to either insert a new document
            # or update an existing one based on the data_source_id.
            result = collection.update_one(
                {"data_source_id": data_source_id},
                {"$set": analysis_data},
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

mongo_service = MongoService() 