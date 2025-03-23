import pytest
import tempfile
from pathlib import Path

@pytest.fixture(scope="session")
def test_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="session")
def sample_config(test_dir):
    """Create a sample configuration"""
    return {
        "supported_extensions": [".pdf", ".tiff", ".jpg"],
        "max_file_size_mb": 10,
        "processing_directory": str(test_dir / "processed_documents"),
        "processing_records_path": str(test_dir / "records/processing_records.json"),
        "error_directory": str(test_dir / "errors"),
        "backup_directory": str(test_dir / "backups"),
        "processing_options": {
            "create_backup": True,
            "validate_content": True,
            "extract_metadata": True,
            "compress_files": False
        }
    }

