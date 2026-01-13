"""Job status API endpoints for tracking processing progress."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

jobs_router = APIRouter()


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    message: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    audio_url: Optional[str] = None
    error_details: Optional[str] = None
    processing_stats: Optional[Dict[str, Any]] = None


@jobs_router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, request: Request):
    """Get processing status for a job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Job status information
    """
    try:
        # Get pipeline orchestrator from app state
        pipeline_orchestrator = request.app.state.pipeline_orchestrator
        
        if not pipeline_orchestrator:
            raise HTTPException(
                status_code=503,
                detail="Pipeline orchestrator not available"
            )
        
        # Get job status from batch processor
        batch_processor = pipeline_orchestrator.batch_processor
        job_info = batch_processor.get_job_status(job_id)
        
        if not job_info:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Map internal status to API status
        status_mapping = {
            'queued': 'pending',
            'processing': 'processing',
            'completed': 'completed',
            'failed': 'failed',
            'cancelled': 'failed'
        }
        
        api_status = status_mapping.get(job_info.status, 'unknown')
        
        # Calculate progress based on panels processed
        progress = 0
        if job_info.total_panels > 0:
            progress = min(100, int((job_info.panels_processed / job_info.total_panels) * 100))
        
        # Generate message based on status
        message = ""
        if api_status == 'pending':
            message = "Job is queued for processing"
        elif api_status == 'processing':
            message = f"Processing panels ({job_info.panels_processed}/{job_info.total_panels})"
        elif api_status == 'completed':
            message = "Processing completed successfully"
            progress = 100
        elif api_status == 'failed':
            message = "Processing failed"
        
        # Get audio URL if completed
        audio_url = None
        if api_status == 'completed' and job_info.result:
            library_manager = request.app.state.library_manager
            if library_manager:
                # Try to find the audio in the library
                library_items = await library_manager.get_library_index()
                for item in library_items:
                    if item.metadata.get('job_id') == job_id:
                        audio_url = f"/api/audio/{item.id}"
                        break
        
        return JobStatus(
            job_id=job_id,
            status=api_status,
            progress=progress,
            message=message,
            created_at=job_info.created_at,
            updated_at=job_info.updated_at,
            audio_url=audio_url,
            error_details=job_info.error_message if job_info.error_message else None,
            processing_stats=job_info.result if job_info.result else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job status: {str(e)}"
        )


@jobs_router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, request: Request):
    """Cancel a processing job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Cancellation confirmation
    """
    try:
        # Get pipeline orchestrator from app state
        pipeline_orchestrator = request.app.state.pipeline_orchestrator
        
        if not pipeline_orchestrator:
            raise HTTPException(
                status_code=503,
                detail="Pipeline orchestrator not available"
            )
        
        # Cancel job in batch processor
        batch_processor = pipeline_orchestrator.batch_processor
        success = batch_processor.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found or cannot be cancelled"
            )
        
        logger.info(f"Cancelled job {job_id}")
        
        return {
            "job_id": job_id,
            "message": "Job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling job: {str(e)}"
        )


@jobs_router.get("/jobs")
async def list_jobs(request: Request, limit: int = 50, offset: int = 0):
    """List all jobs with pagination.
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        
    Returns:
        List of jobs with pagination info
    """
    try:
        # Get pipeline orchestrator from app state
        pipeline_orchestrator = request.app.state.pipeline_orchestrator
        
        if not pipeline_orchestrator:
            raise HTTPException(
                status_code=503,
                detail="Pipeline orchestrator not available"
            )
        
        # Get jobs from batch processor
        batch_processor = pipeline_orchestrator.batch_processor
        all_jobs = batch_processor.list_jobs()
        
        # Apply pagination
        total_jobs = len(all_jobs)
        jobs_page = all_jobs[offset:offset + limit]
        
        # Convert to API format
        job_statuses = []
        for job_info in jobs_page:
            status_mapping = {
                'queued': 'pending',
                'processing': 'processing',
                'completed': 'completed',
                'failed': 'failed',
                'cancelled': 'failed'
            }
            
            api_status = status_mapping.get(job_info.status, 'unknown')
            progress = 0
            if job_info.total_panels > 0:
                progress = min(100, int((job_info.panels_processed / job_info.total_panels) * 100))
            
            job_statuses.append({
                "job_id": job_info.job_id,
                "status": api_status,
                "progress": progress,
                "created_at": job_info.created_at,
                "updated_at": job_info.updated_at
            })
        
        return {
            "jobs": job_statuses,
            "pagination": {
                "total": total_jobs,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_jobs
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing jobs: {str(e)}"
        )