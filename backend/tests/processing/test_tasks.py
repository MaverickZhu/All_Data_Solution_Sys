import pytest
import pandas as pd
from pathlib import Path
from PIL import Image
import numpy as np
from unittest.mock import MagicMock

from backend.models.data_source import DataSource, ProfileStatusEnum
from backend.processing.tasks import run_profiling_task, generate_fallback_profile
from backend.core.config import settings

@pytest.fixture
def test_data_source(sync_db_session):
    """Fixture to create a test data source in the mock DB."""
    ds = DataSource(
        name="test_csv.csv",
        file_path="test_csv.csv",
        data_source_type="csv",
        profile_status=ProfileStatusEnum.pending,
        project_id=1
    )
    sync_db_session.add(ds)
    sync_db_session.commit()
    sync_db_session.refresh(ds)
    return ds

@pytest.fixture
def create_test_csv(tmp_path: Path) -> Path:
    """Fixture to create a temporary CSV file for testing."""
    csv_content = "col1,col2\n1,a\n2,b\n3,c"
    csv_path = tmp_path / "test_csv.csv"
    csv_path.write_text(csv_content)
    return csv_path

@pytest.fixture(params=[
    ("en", "Hello world. This is a test file for keyword extraction."),
    ("zh-cn", "这是一个用于测试关键词提取的中文文件。")
])
def create_test_txt(request, tmp_path: Path) -> Path:
    """Fixture to create a temporary TXT file for testing, parameterized for different languages."""
    lang, content = request.param
    txt_path = tmp_path / f"test_{lang}.txt"
    txt_path.write_text(content, encoding='utf-8')
    return txt_path

@pytest.fixture
def create_test_image(tmp_path: Path) -> Path:
    """Fixture to create a temporary PNG image file for testing."""
    img_path = tmp_path / "test_image.png"
    # Create a simple 10x10 black image
    img_array = np.zeros((10, 10, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    img.save(img_path)
    return img_path

def test_run_profiling_task_success(monkeypatch, sync_db_session, test_data_source, create_test_csv, tmp_path):
    """
    Test the successful execution of the profiling task.
    """
    # Patch get_sync_db to return our mock session
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    # Patch settings.upload_dir to use the temporary directory
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    # Update file path to be relative to the tmp_path
    test_data_source.file_path = create_test_csv.name
    sync_db_session.commit()
    data_source_id = test_data_source.id

    # Run the task directly as a function
    task_result = run_profiling_task(data_source_id)
    
    # Assertions
    assert task_result is not None
    assert task_result["status"] == "completed"
    assert "report_json" in task_result
    
    # Check database state by re-querying
    updated_data_source = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_data_source.profile_status == ProfileStatusEnum.completed
    assert updated_data_source.profiling_result is not None
    assert updated_data_source.profiling_result.get("fallback") is not True

def test_run_profiling_task_file_not_found(monkeypatch, sync_db_session, test_data_source, tmp_path):
    """
    Test profiling task when the source file does not exist.
    """
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    # Ensure the file does not exist
    test_data_source.file_path = "non_existent_file.csv"
    sync_db_session.commit()
    data_source_id = test_data_source.id

    with pytest.raises(FileNotFoundError):
        run_profiling_task(data_source_id)
    
    # Check that status was updated to failed
    updated_data_source = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_data_source.profile_status == ProfileStatusEnum.failed

def test_run_profiling_task_fallback_success(monkeypatch, sync_db_session, test_data_source, create_test_csv, tmp_path):
    """
    Test that the task successfully uses the fallback profiler when ydata-profiling fails.
    """
    # Mock ydata-profiling to raise an exception
    def mock_profile_report(*args, **kwargs):
        raise ValueError("Simulated ydata-profiling failure")
    
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr("backend.processing.tasks.ProfileReport", mock_profile_report)
    
    test_data_source.file_path = create_test_csv.name
    sync_db_session.commit()
    data_source_id = test_data_source.id
    
    task_result = run_profiling_task(data_source_id)
    
    assert task_result is not None
    assert task_result["status"] == "completed"
    
    updated_data_source = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_data_source.profile_status == ProfileStatusEnum.completed
    assert updated_data_source.profiling_result is not None
    assert updated_data_source.profiling_result.get("fallback") is True
    assert "table" in updated_data_source.profiling_result
    assert "variables" in updated_data_source.profiling_result

def test_generate_fallback_profile_failure(monkeypatch):
    """
    Test the failure case of the fallback profiler itself.
    """
    # Mock pandas describe to fail
    def mock_describe(*args, **kwargs):
        raise RuntimeError("Simulated describe failure")
    
    monkeypatch.setattr(pd.DataFrame, "describe", mock_describe)
    
    df = pd.DataFrame({"col1": [1, 2]})
    result = generate_fallback_profile(df)
    
    assert "error" in result
    assert "Both profiling and fallback failed" in result["error"]

def test_run_profiling_task_data_source_not_found(monkeypatch, sync_db_session):
    """
    Test profiling task when the data source ID is invalid.
    """
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    
    invalid_id = 9999
    
    with pytest.raises(ValueError, match="Data source not found"):
        run_profiling_task(invalid_id)

def test_run_profiling_task_csv_parsing_error(monkeypatch, sync_db_session, test_data_source, tmp_path):
    """
    Test profiling task when the CSV file is malformed.
    """
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    # Create a malformed CSV
    malformed_csv_content = '"col1,col2\\n1,"a\\n2,b'
    malformed_csv_path = tmp_path / "malformed.csv"
    malformed_csv_path.write_text(malformed_csv_content)
    
    test_data_source.file_path = malformed_csv_path.name
    sync_db_session.commit()
    data_source_id = test_data_source.id

    with pytest.raises(Exception, match="Failed to parse the data file"):
        run_profiling_task(data_source_id)

    updated_data_source = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_data_source.profile_status == ProfileStatusEnum.failed

@pytest.mark.parametrize("create_test_txt, lang_code", [
    (("en", "Hello world. This is a test file for keyword extraction."), "en"),
    (("zh-cn", "这是一个用于测试关键词提取的中文文件。"), "zh-cn")
], indirect=["create_test_txt"])
def test_run_profiling_task_text_file_success(monkeypatch, sync_db_session, test_data_source, create_test_txt, lang_code, tmp_path):
    """
    Test the successful execution of the profiling task for text files of different languages,
    including the embedding generation step.
    """
    # Mock the embedding service to avoid actual model loading and processing
    mock_embedding = MagicMock(return_value={"status": "success"})
    monkeypatch.setattr(
        "backend.semantic_processing.embedding_service.EmbeddingService.generate_and_store_embeddings",
        mock_embedding
    )
    
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    file_content = create_test_txt.read_text(encoding='utf-8')
    test_data_source.name = create_test_txt.name
    test_data_source.file_path = create_test_txt.name
    test_data_source.data_source_type = 'txt'
    sync_db_session.commit()
    data_source_id = test_data_source.id

    task_result = run_profiling_task(data_source_id)
    
    assert task_result is not None
    assert task_result["status"] == "completed"
    
    updated_ds = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_ds.profile_status == ProfileStatusEnum.completed
    assert updated_ds.profiling_result["analysis_type"] == "text"
    assert updated_ds.profiling_result["detected_language"] == lang_code
    
    # Check that keywords were extracted (don't assert specific keywords, as they might change)
    assert "keywords" in updated_ds.profiling_result
    assert isinstance(updated_ds.profiling_result["keywords"], list)
    
    # Check that sentiment analysis was performed
    assert "sentiment" in updated_ds.profiling_result
    assert isinstance(updated_ds.profiling_result["sentiment"], dict)
    # VADER and SnowNLP both produce different sentiment structures. 
    # Just check that it's a non-empty dictionary.
    assert updated_ds.profiling_result["sentiment"]

    # --- New Assertions for Embedding ---
    # Verify that the embedding service was called correctly
    mock_embedding.assert_called_once()
    # Check the arguments it was called with
    args, kwargs = mock_embedding.call_args
    assert args[0] == data_source_id
    assert args[1] == file_content

def test_run_profiling_task_image_file_success(monkeypatch, sync_db_session, test_data_source, create_test_image, tmp_path):
    """
    Test the successful execution of the profiling task for an image file.
    """
    monkeypatch.setattr("backend.processing.tasks.get_sync_db", lambda: (yield sync_db_session))
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    
    # Configure the data source for the image file
    test_data_source.name = create_test_image.name
    test_data_source.file_path = create_test_image.name
    test_data_source.data_source_type = 'png'
    sync_db_session.commit()
    data_source_id = test_data_source.id

    # Run the task
    task_result = run_profiling_task(data_source_id)
    
    # Assertions
    assert task_result is not None
    assert task_result["status"] == "completed"
    
    updated_ds = sync_db_session.query(DataSource).filter(DataSource.id == data_source_id).first()
    assert updated_ds.profile_status == ProfileStatusEnum.completed
    assert updated_ds.profiling_result["analysis_type"] == "image"
    
    # Check that image hash was generated and stored
    assert "image_hash" in updated_ds.profiling_result
    assert updated_ds.profiling_result["image_hash"] is not None
    assert updated_ds.image_hash == updated_ds.profiling_result["image_hash"]
    assert len(updated_ds.image_hash) > 0 # Hash should be a non-empty string