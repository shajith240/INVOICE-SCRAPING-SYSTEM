import requests
import time
from pathlib import Path
from unittest.mock import patch

@patch('requests.post')
def test_batch_processing(mock_post):
    # API endpoint
    BASE_URL = "http://localhost:8000"
    
    # Mock successful response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "job_id": "test-job-123",
        "status": "success"
    }

    # Prepare files for upload
    invoice_dir = Path("test_data/invoices")
    files = []
    for invoice_file in invoice_dir.glob("*.pdf"):
        files.append(
            ("files", (invoice_file.name, open(invoice_file, "rb"), "application/pdf"))
        )

    # Start batch processing
    response = requests.post(f"{BASE_URL}/api/v1/batch-process/", files=files)
    
    # Assert the response
    assert response.status_code == 200
    assert "job_id" in response.json()

if __name__ == "__main__":
    test_batch_processing()

