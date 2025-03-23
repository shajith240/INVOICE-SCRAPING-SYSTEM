import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture(scope="session")
def test_config():
    """Load test configuration"""
    config_path = Path(__file__).parent / "test_config.json"
    with open(config_path) as f:
        return json.load(f)

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(scope="session")
def sample_dirs(test_config):
    """Create and manage test directories"""
    dirs = test_config["test_data"]
    
    # Create directories
    for dir_path in dirs.values():
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    yield dirs
    
    # Cleanup temporary files after tests
    import shutil
    shutil.rmtree(dirs["temp_dir"], ignore_errors=True)

@pytest.fixture(scope="session")
def sample_pdf(sample_dirs):
    """Create a sample PDF for testing"""
    from reportlab.pdfgen import canvas
    
    pdf_path = Path(sample_dirs["input_dir"]) / "sample_invoice.pdf"
    c = canvas.Canvas(str(pdf_path))
    
    # Add some test content
    c.drawString(100, 750, "Test Invoice")
    c.drawString(100, 700, "Invoice #: INV-2024-001")
    c.drawString(100, 650, "Amount: $1,000.00")
    c.drawString(100, 600, "Date: 2024-03-15")
    c.drawString(100, 550, "Vendor: Test Company Ltd")
    
    c.save()
    return pdf_path


