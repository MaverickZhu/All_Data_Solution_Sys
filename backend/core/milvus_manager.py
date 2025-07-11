"""
Milvus Connection and Collection Management
"""
import logging
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

from backend.core.config import settings

logger = logging.getLogger("database")

class MilvusManager:
    COLLECTION_NAME = "document_embeddings"
    # This should match the output dimension of your embedding model
    EMBEDDING_DIM = 768 # Example for BAAI/bge-base-zh-v1.5 which is 768

    _alias = "default"

    @classmethod
    def connect(cls):
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias=cls._alias,
                host=settings.milvus_host,
                port=settings.milvus_port
            )
            logger.info(f"Successfully connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}", exc_info=True)
            raise

    @classmethod
    def disconnect(cls):
        """Disconnect from Milvus."""
        try:
            connections.disconnect(cls._alias)
            logger.info("Disconnected from Milvus.")
        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {e}", exc_info=True)

    @classmethod
    def get_or_create_collection(cls) -> Collection:
        """
        Get the collection if it exists, otherwise create it with the correct schema and index.
        """
        if utility.has_collection(cls.COLLECTION_NAME, using=cls._alias):
            logger.info(f"Collection '{cls.COLLECTION_NAME}' already exists.")
            return Collection(cls.COLLECTION_NAME, using=cls._alias)
        
        logger.info(f"Collection '{cls.COLLECTION_NAME}' not found. Creating new collection...")
        
        # 1. Define fields
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="data_source_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=2000), # Adjust max_length as needed
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=cls.EMBEDDING_DIM)
        ]

        # 2. Create schema
        schema = CollectionSchema(fields, description="Stores text embeddings for RAG")
        
        # 3. Create collection
        collection = Collection(
            name=cls.COLLECTION_NAME,
            schema=schema,
            using=cls._alias,
            consistency_level="Strong" # Ensures data is immediately queryable
        )
        logger.info(f"Successfully created collection: {cls.COLLECTION_NAME}")

        # 4. Create an index on the embedding field for efficient search
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        logger.info(f"Successfully created index on 'embedding' field.")
        
        return collection

milvus_manager = MilvusManager() 