import pytest
from pathlib import Path

def test_process_single_invoice(test_client, sample_pdf):
    """Test single invoice processing endpoint"""
    with open(sample_pdf, "rb") as f:
        response = test_client.post(
            "/api/v1/process-invoice/",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "invoice_number" in data["data"]
    assert "total_amount" in data["data"]

def test_batch_processing(test_client, sample_pdf, sample_dirs):
    """Test batch processing endpoint"""
    # Create multiple test files
    files = []
    with open(sample_pdf, "rb") as f:
        content = f.read()
        files = [
            ("files", (f"invoice_{i}.pdf", content, "application/pdf"))
            for i in range(3)
        ]
    
    # Start batch processing
    response = test_client.post("/api/v1/batch-process/", files=files)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Check status
    status_response = test_client.get(f"/api/v1/batch-status/{job_id}")
    assert status_response.status_code == 200
    
    # Get results
    results_response = test_client.get(f"/api/v1/batch-results/{job_id}")
    assert results_response.status_code == 200
    assert len(results_response.json()["results"]) == 3