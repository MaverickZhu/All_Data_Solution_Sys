import logging
import os
from typing import List, Union
import numpy as np
import ollama
from backend.core.milvus_manager import MilvusManager
from backend.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating and storing text embeddings using Ollama.
    This implementation uses a fixed-size chunking strategy, which is a
    best practice for many retrieval-focused embedding models like BGE-M3.
    """

    @staticmethod
    def get_ollama_client() -> ollama.Client:
        """
        Creates an Ollama client, configuring the host based on the environment.
        """
        ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11435")
        logger.info(f"Connecting to Ollama at: {ollama_host}")
        return ollama.Client(host=ollama_host)

    @staticmethod
    def chunk_text_by_size(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> List[str]:
        """
        Splits text into fixed-size chunks with a specified overlap.
        This is a robust method for preparing text for retrieval models.
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
            
        logger.info(f"Split text into {len(chunks)} chunks with size={chunk_size} and overlap={chunk_overlap}.")
        return chunks

    @staticmethod
    def generate_and_store_embeddings(
        data_source_id: int,
        text_content: str,
        collection_name: str = "document_embeddings",
    ) -> bool:
        """
        Generates and stores embeddings for the given text content using Ollama.
        """
        logger.info(f"Starting embedding generation for data source ID: {data_source_id}")
        
        try:
            chunks = EmbeddingService.chunk_text_by_size(text_content)
            if not chunks:
                logger.warning("Text content resulted in zero chunks. Skipping embedding.")
                return False

            logger.info(f"Initializing Ollama client and generating embeddings...")
            client = EmbeddingService.get_ollama_client()
            
            response = client.embed(model='bge-m3:latest', input=chunks)
            embeddings = [res['embedding'] for res in response]
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings.")

            if embeddings:
                try:
                    # BGE-M3's dimension is 1024
                    collection = MilvusManager.get_or_create_collection(collection_name, dim=1024)
                    
                    # We need a unique ID for each chunk within Milvus. 
                    # A simple approach is to combine data_source_id with the chunk index.
                    # Note: This is not globally unique if you have other entity types.
                    # For production, a more robust UID generation (e.g., UUID) is recommended.
                    entities = [
                        {
                            "data_source_id": data_source_id, 
                            "text_chunk": chunk, 
                            "embedding": emb
                        }
                        for chunk, emb in zip(chunks, embeddings)
                    ]
                    
                    collection.insert(entities)
                    collection.flush()
                    logger.info(f"Successfully inserted {len(entities)} embeddings into Milvus for data source {data_source_id}.")
                    return True
                except Exception as e:
                    logger.error(f"Milvus insertion failed for data source {data_source_id}: {e}", exc_info=True)
                    return False
            else:
                logger.warning(f"Ollama returned no embeddings for data source {data_source_id}.")
                return False

        except Exception as e:
            logger.error(f"An unexpected error occurred during embedding generation for data source {data_source_id}: {e}", exc_info=True)
            return False

        return False 