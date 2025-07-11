import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
load_dotenv(dotenv_path=project_root / ".env")

from backend.core.milvus_manager import MilvusManager
from backend.core.config import settings
from pymilvus import utility

def check_milvus_data(data_source_id: int):
    """
    Connects to Milvus and checks for embeddings for a specific data_source_id.
    """
    print("--- Starting Milvus Check ---")
    try:
        # Manually override settings for local script execution
        # In Docker, these would be set correctly via environment variables
        settings.milvus_host = os.getenv("MILVUS_HOST_LOCAL", "localhost")
        settings.milvus_port = os.getenv("MILVUS_PORT_LOCAL", "19531")
        
        MilvusManager.connect()

        collection_name = MilvusManager.COLLECTION_NAME
        
        if not utility.has_collection(collection_name):
            print(f"Error: Collection '{collection_name}' does not exist.")
            return

        collection = MilvusManager.get_or_create_collection()
        collection.load() # Load collection into memory for searching

        # Query for the number of entities for the given data_source_id
        expr = f"data_source_id == {data_source_id}"
        result = collection.query(expr=expr, output_fields=["data_source_id"])
        
        count = len(result)
        
        print(f"\n>>> Querying for data_source_id: {data_source_id}")
        print(f">>> Found {count} embedding(s) in Milvus collection '{collection_name}'.")

        if count > 0:
            print("\nConclusion: SUCCESS! Vectorization occurred for this data source.")
        else:
            print("\nConclusion: FAILED. No vectors found for this data source.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("--- Milvus Check Finished ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check Milvus for data source embeddings.")
    parser.add_argument("--data-source-id", type=int, required=True, help="The ID of the data source to check.")
    args = parser.parse_args()
    
    check_milvus_data(args.data_source_id) 