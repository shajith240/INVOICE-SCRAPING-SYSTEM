from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
import json

from src.pdf_processor import PDFProcessor
from src.document_processor import DocumentProcessor

app = FastAPI(
    title="Invoice Processing API",
    description="API for processing and extracting data from invoices",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store batch processing status
batch_jobs: Dict[str, Dict] = {}

async def process_single_file(file_path: Path, job_id: str, file_index: int, total_files: int) -> dict:
    """Process a single file and update progress"""
    try:
        processor = PDFProcessor()
        result = processor.extract_invoice_data(str(file_path))
        
        # Update progress
        batch_jobs[job_id]["processed"] += 1
        batch_jobs[job_id]["progress"] = (batch_jobs[job_id]["processed"] / total_files) * 100
        batch_jobs[job_id]["results"].append({
            "file_name": file_path.name,
            "status": "success",
            "data": result
        })
        
        return result
    except Exception as e:
        batch_jobs[job_id]["errors"].append({
            "file_name": file_path.name,
            "error": str(e)
        })
        return {"error": str(e)}
    finally:
        # Cleanup temp file
        file_path.unlink(missing_ok=True)

async def process_batch(job_id: str, files: List[Path], parallel: bool):
    """Process batch of files with progress tracking"""
    total_files = len(files)
    
    if parallel:
        # Process files in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            tasks = []
            for idx, file_path in enumerate(files):
                task = asyncio.create_task(
                    process_single_file(file_path, job_id, idx, total_files)
                )
                tasks.append(task)
            await asyncio.gather(*tasks)
    else:
        # Process files sequentially
        for idx, file_path in enumerate(files):
            await process_single_file(file_path, job_id, idx, total_files)
    
    # Mark job as completed
    batch_jobs[job_id]["status"] = "completed"
    
    # Save results to persistent storage
    results_file = Path(f"results/{job_id}.json")
    results_file.parent.mkdir(exist_ok=True)
    with results_file.open("w") as f:
        json.dump(batch_jobs[job_id], f)

@app.post("/api/v1/process-invoice/")
async def process_invoice(
    file: UploadFile = File(...),
    validate: bool = True,
    extract_metadata: bool = True
):
    """
    Process a single invoice file and extract its data
    """
    try:
        # Generate unique filename
        temp_file = Path(f"temp/{uuid.uuid4()}{Path(file.filename).suffix}")
        temp_file.parent.mkdir(exist_ok=True)
        
        # Save uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process invoice
        processor = PDFProcessor()
        result = processor.extract_invoice_data(str(temp_file))
        
        # Cleanup
        temp_file.unlink()
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/batch-process/")
async def batch_process_invoices(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    parallel: bool = True
):
    """
    Process multiple invoice files with progress tracking
    
    Args:
        files: List of invoice files to process
        parallel: Whether to process files in parallel (default: True)
    
    Returns:
        dict: Job ID and initial status
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        batch_jobs[job_id] = {
            "status": "processing",
            "total_files": len(files),
            "processed": 0,
            "progress": 0,
            "results": [],
            "errors": []
        }
        
        # Save files to temp directory
        temp_files = []
        for file in files:
            temp_file = Path(f"temp/{uuid.uuid4()}{Path(file.filename).suffix}")
            temp_file.parent.mkdir(exist_ok=True)
            
            with temp_file.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_files.append(temp_file)
        
        # Start background processing
        background_tasks.add_task(process_batch, job_id, temp_files, parallel)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": f"Processing {len(files)} files"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/batch-status/{job_id}")
async def get_batch_status(job_id: str):
    """
    Get the status of a batch processing job
    """
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return batch_jobs[job_id]

@app.get("/api/v1/batch-results/{job_id}")
async def get_batch_results(job_id: str):
    """
    Get the results of a completed batch processing job
    """
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if batch_jobs[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job still processing")
    
    # Load results from persistent storage
    results_file = Path(f"results/{job_id}.json")
    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    
    with results_file.open() as f:
        return json.load(f)
