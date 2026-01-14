"""Upload API endpoints for PDF file processing."""

import logging
import tempfile
import os
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

upload_router = APIRouter()

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = ["application/pdf"]
ALLOWED_EXTENSIONS = [".pdf"]


class UploadResponse(BaseModel):
    """Response model for file upload."""
    job_id: str
    message: str
    file_size: int
    filename: str


async def process_comic_background(
    job_id: str,
    pdf_path: str,
    comic_title: str,
    pipeline_orchestrator,
    cost_monitor,
    metrics_collector
):
    """Background task to process comic PDF."""
    try:
        logger.info(f"Starting background processing for job {job_id}")
        logger.info(f"PDF path: {pdf_path}, Title: {comic_title}")
        
        # Start cost tracking
        if cost_monitor:
            await cost_monitor.start_job_tracking(job_id)
        
        # Start metrics tracking
        if metrics_collector:
            await metrics_collector.start_job_tracking(job_id)
        
        # Process the comic
        logger.info(f"Calling pipeline_orchestrator.process_comic for job {job_id}")
        result = await pipeline_orchestrator.process_comic(
            pdf_path=pdf_path,
            comic_title=comic_title,
            job_id=job_id
        )
        
        logger.info(f"Completed processing for job {job_id}, result: {result}")
        
        # Update cost tracking
        if cost_monitor:
            await cost_monitor.complete_job_tracking(job_id, result)
        
        # Update metrics
        if metrics_collector:
            await metrics_collector.complete_job_tracking(job_id, result)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error processing job {job_id}: {e}")
        logger.error(f"Full traceback: {error_traceback}")
        
        # Update error tracking
        if cost_monitor:
            await cost_monitor.error_job_tracking(job_id, str(e))
        
        if metrics_collector:
            await metrics_collector.error_job_tracking(job_id, str(e))
        
        raise
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
                logger.info(f"Cleaned up temporary file: {pdf_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {pdf_path}: {e}")


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type not supported. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )


@upload_router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = None
):
    """Upload PDF file for processing.
    
    Args:
        file: PDF file to process
        title: Optional title for the comic (defaults to filename)
        
    Returns:
        Upload response with job ID
    """
    # Validate file
    validate_file(file)
    
    # Check file size
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())
    
    # Use filename as title if not provided
    comic_title = title or Path(file.filename).stem
    
    try:
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        logger.info(f"Saved uploaded file to temporary location: {temp_path}")
        
        # Get pipeline orchestrator from app state
        pipeline_orchestrator = request.app.state.pipeline_orchestrator
        cost_monitor = request.app.state.cost_monitor
        metrics_collector = request.app.state.metrics_collector
        
        # Start background processing
        background_tasks.add_task(
            process_comic_background,
            job_id=job_id,
            pdf_path=temp_path,
            comic_title=comic_title,
            pipeline_orchestrator=pipeline_orchestrator,
            cost_monitor=cost_monitor,
            metrics_collector=metrics_collector
        )
        
        logger.info(f"Started background processing for job {job_id}")
        
        return UploadResponse(
            job_id=job_id,
            message="File uploaded successfully. Processing started.",
            file_size=file_size,
            filename=file.filename
        )
        
    except Exception as e:
        logger.error(f"Error handling upload: {e}")
        
        # Clean up temp file if it exists
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except:
            pass
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing upload: {str(e)}"
        )