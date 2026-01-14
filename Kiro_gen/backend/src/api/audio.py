"""Audio API endpoints for streaming and downloading audio files."""

import logging
import os
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import FileResponse, StreamingResponse
import aiofiles

logger = logging.getLogger(__name__)

audio_router = APIRouter()

# Get the backend directory for resolving relative paths
BACKEND_DIR = Path(__file__).parent.parent.parent.resolve()


async def stream_audio_file(file_path: str, start: int = 0, end: Optional[int] = None):
    """Stream audio file with range support."""
    file_size = os.path.getsize(file_path)
    
    if end is None:
        end = file_size - 1
    
    # Ensure valid range
    start = max(0, start)
    end = min(file_size - 1, end)
    
    chunk_size = 8192
    
    async with aiofiles.open(file_path, 'rb') as f:
        await f.seek(start)
        remaining = end - start + 1
        
        while remaining > 0:
            chunk_size_to_read = min(chunk_size, remaining)
            chunk = await f.read(chunk_size_to_read)
            
            if not chunk:
                break
                
            remaining -= len(chunk)
            yield chunk


@audio_router.get("/audio/{audio_id}")
async def get_audio(
    audio_id: str,
    request: Request,
    download: bool = Query(False, description="Force download instead of streaming"),
    range_header: Optional[str] = None
):
    """Get audio file by ID with streaming support.
    
    Args:
        audio_id: Unique audio identifier
        download: Force download instead of streaming
        range_header: HTTP Range header for partial content
        
    Returns:
        Audio file stream or download
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Find audio item in library
        library_index = await library_manager.get_library_index()
        audio_item = None
        
        for item in library_index:
            if item.id == audio_id:
                audio_item = item
                break
        
        if not audio_item:
            raise HTTPException(
                status_code=404,
                detail=f"Audio {audio_id} not found"
            )
        
        # Get local file path
        local_path = audio_item.local_path
        
        # Resolve relative path to absolute path from backend directory
        if local_path:
            # Convert to Path object and resolve relative to backend directory
            local_path_obj = Path(local_path)
            if not local_path_obj.is_absolute():
                local_path = str(BACKEND_DIR / local_path_obj)
        
        if not local_path or not os.path.exists(local_path):
            # Try to download from S3 if not available locally
            try:
                local_path = await library_manager.download_from_s3(audio_id)
                if not local_path:
                    raise HTTPException(
                        status_code=404,
                        detail="Audio file not available - S3 download failed"
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to download audio {audio_id} from S3: {e}")
                raise HTTPException(
                    status_code=404,
                    detail="Audio file not available"
                )
        
        # Get file info
        file_size = os.path.getsize(local_path)
        # Generate filename from metadata title or use audio_id
        if audio_item.metadata and hasattr(audio_item.metadata, 'title') and audio_item.metadata.title:
            file_name = f"{audio_item.metadata.title}.mp3"
        else:
            file_name = f"{audio_id}.mp3"
        
        # Handle range requests for streaming
        range_header = request.headers.get('range')
        if range_header and not download:
            # Parse range header
            try:
                range_match = range_header.replace('bytes=', '').split('-')
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] else file_size - 1
            except (ValueError, IndexError):
                start = 0
                end = file_size - 1
            
            # Validate range
            if start >= file_size or end >= file_size or start > end:
                raise HTTPException(
                    status_code=416,
                    detail="Range not satisfiable",
                    headers={"Content-Range": f"bytes */{file_size}"}
                )
            
            # Stream partial content
            content_length = end - start + 1
            
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": "audio/mpeg"
            }
            
            return StreamingResponse(
                stream_audio_file(local_path, start, end),
                status_code=206,
                headers=headers,
                media_type="audio/mpeg"
            )
        
        # Handle download or full streaming
        if download:
            # Force download
            return FileResponse(
                path=local_path,
                filename=file_name,
                media_type="audio/mpeg",
                headers={"Content-Disposition": f"attachment; filename={file_name}"}
            )
        else:
            # Stream full file
            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Type": "audio/mpeg"
            }
            
            return StreamingResponse(
                stream_audio_file(local_path),
                headers=headers,
                media_type="audio/mpeg"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio {audio_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error serving audio: {str(e)}"
        )


@audio_router.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str, request: Request):
    """Delete audio file by ID.
    
    Args:
        audio_id: Unique audio identifier
        
    Returns:
        Deletion confirmation
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Delete audio from library
        success = await library_manager.delete_audio(audio_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Audio {audio_id} not found"
            )
        
        logger.info(f"Deleted audio {audio_id}")
        
        return {
            "audio_id": audio_id,
            "message": "Audio deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audio {audio_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting audio: {str(e)}"
        )


@audio_router.get("/audio/{audio_id}/metadata")
async def get_audio_metadata(audio_id: str, request: Request):
    """Get audio metadata by ID.
    
    Args:
        audio_id: Unique audio identifier
        
    Returns:
        Audio metadata
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Find audio item in library
        library_index = await library_manager.get_library_index()
        audio_item = None
        
        for item in library_index:
            if item.id == audio_id:
                audio_item = item
                break
        
        if not audio_item:
            raise HTTPException(
                status_code=404,
                detail=f"Audio {audio_id} not found"
            )
        
        # Return metadata
        return {
            "id": audio_item.id,
            "title": audio_item.title,
            "filename": audio_item.filename,
            "upload_date": audio_item.upload_date,
            "duration": audio_item.duration,
            "file_size": audio_item.file_size,
            "metadata": audio_item.metadata or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio metadata {audio_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving audio metadata: {str(e)}"
        )