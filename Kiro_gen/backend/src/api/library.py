"""Library API endpoints for audio file management."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

library_router = APIRouter()


class LibraryItem(BaseModel):
    """Library item response model."""
    id: str
    title: str
    filename: str
    upload_date: datetime
    duration: Optional[float] = None
    file_size: Optional[int] = None
    characters: List[str] = []
    scenes: List[str] = []
    audio_url: str
    download_url: str
    metadata: Dict[str, Any] = {}


class LibraryResponse(BaseModel):
    """Library response with items and pagination."""
    items: List[LibraryItem]
    pagination: Dict[str, Any]


@library_router.get("/library", response_model=LibraryResponse)
async def get_library(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("upload_date", pattern="^(upload_date|title|duration)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Get library items with pagination and sorting.
    
    Args:
        limit: Maximum number of items to return (1-100)
        offset: Number of items to skip
        sort_by: Field to sort by (upload_date, title, duration)
        sort_order: Sort order (asc, desc)
        
    Returns:
        Library items with pagination info
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Get library index
        library_index = await library_manager.get_library_index()
        
        # Sort items - StoredAudio uses 'uploaded_at' not 'upload_date'
        reverse_sort = sort_order == "desc"
        if sort_by == "upload_date":
            library_index.sort(key=lambda x: x.uploaded_at, reverse=reverse_sort)
        elif sort_by == "title":
            library_index.sort(key=lambda x: (x.metadata.title if x.metadata else '').lower(), reverse=reverse_sort)
        elif sort_by == "duration":
            library_index.sort(key=lambda x: (x.metadata.total_duration if x.metadata else 0) or 0, reverse=reverse_sort)
        
        # Apply pagination
        total_items = len(library_index)
        items_page = library_index[offset:offset + limit]
        
        # Convert to API format
        library_items = []
        for item in items_page:
            # Extract info from metadata - StoredAudio.metadata is AudioMetadata
            title = ""
            duration = None
            characters = []
            scenes = []
            metadata_dict = {}
            
            if item.metadata:
                # AudioMetadata is a dataclass with direct attributes
                title = getattr(item.metadata, 'title', '') or ''
                duration = getattr(item.metadata, 'total_duration', None)
                characters = getattr(item.metadata, 'characters', []) or []
                scenes = getattr(item.metadata, 'scenes', []) or []
                # Convert metadata to dict if it has to_dict method
                if hasattr(item.metadata, 'to_dict'):
                    metadata_dict = item.metadata.to_dict()
                elif hasattr(item.metadata, '__dict__'):
                    metadata_dict = vars(item.metadata)
            
            # Ensure characters and scenes are lists
            if isinstance(characters, str):
                characters = [characters]
            if isinstance(scenes, str):
                scenes = [scenes]
            
            # Generate filename from title or ID
            filename = f"{title}.mp3" if title else f"{item.id}.mp3"
            
            library_items.append(LibraryItem(
                id=item.id,
                title=title,
                filename=filename,
                upload_date=item.uploaded_at,
                duration=duration,
                file_size=item.file_size,
                characters=characters if characters else [],
                scenes=scenes if scenes else [],
                audio_url=f"/api/audio/{item.id}",
                download_url=f"/api/audio/{item.id}?download=true",
                metadata=metadata_dict
            ))
        
        return LibraryResponse(
            items=library_items,
            pagination={
                "total": total_items,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_items,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting library: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving library: {str(e)}"
        )


@library_router.get("/library/search", response_model=LibraryResponse)
async def search_library(
    request: Request,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search library items by title, characters, or scenes.
    
    Args:
        q: Search query
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        Matching library items
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Search library
        search_results = await library_manager.search_library(
            query=q,
            limit=limit,
            offset=offset
        )
        
        # Convert to API format
        library_items = []
        for item in search_results:
            # Extract characters and scenes from metadata
            characters = []
            scenes = []
            if item.metadata:
                characters = item.metadata.get('characters', [])
                scenes = item.metadata.get('scenes', [])
                if isinstance(characters, str):
                    characters = [characters]
                if isinstance(scenes, str):
                    scenes = [scenes]
            
            library_items.append(LibraryItem(
                id=item.id,
                title=item.title,
                filename=item.filename,
                upload_date=item.upload_date,
                duration=item.duration,
                file_size=item.file_size,
                characters=characters,
                scenes=scenes,
                audio_url=f"/api/audio/{item.id}",
                download_url=f"/api/audio/{item.id}?download=true",
                metadata=item.metadata or {}
            ))
        
        return LibraryResponse(
            items=library_items,
            pagination={
                "total": len(library_items),  # Search doesn't return total count
                "limit": limit,
                "offset": offset,
                "has_more": len(library_items) == limit,  # Estimate
                "query": q
            }
        )
        
    except Exception as e:
        logger.error(f"Error searching library: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching library: {str(e)}"
        )


@library_router.get("/library/stats")
async def get_library_stats(request: Request):
    """Get library statistics.
    
    Returns:
        Library statistics including total items, total duration, etc.
    """
    try:
        # Get library manager from app state
        library_manager = request.app.state.library_manager
        
        if not library_manager:
            raise HTTPException(
                status_code=503,
                detail="Library manager not available"
            )
        
        # Get library index
        library_index = await library_manager.get_library_index()
        
        # Calculate statistics
        total_items = len(library_index)
        total_duration = sum(item.duration or 0 for item in library_index)
        total_size = sum(item.file_size or 0 for item in library_index)
        
        # Get unique characters and scenes
        all_characters = set()
        all_scenes = set()
        
        for item in library_index:
            if item.metadata:
                characters = item.metadata.get('characters', [])
                scenes = item.metadata.get('scenes', [])
                
                if isinstance(characters, list):
                    all_characters.update(characters)
                elif isinstance(characters, str):
                    all_characters.add(characters)
                
                if isinstance(scenes, list):
                    all_scenes.update(scenes)
                elif isinstance(scenes, str):
                    all_scenes.add(scenes)
        
        # Get recent uploads (last 7 days)
        from datetime import timedelta
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_uploads = len([
            item for item in library_index 
            if item.upload_date >= recent_cutoff
        ])
        
        return {
            "total_items": total_items,
            "total_duration_seconds": total_duration,
            "total_size_bytes": total_size,
            "unique_characters": len(all_characters),
            "unique_scenes": len(all_scenes),
            "recent_uploads": recent_uploads,
            "average_duration": total_duration / total_items if total_items > 0 else 0,
            "average_size": total_size / total_items if total_items > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting library stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving library statistics: {str(e)}"
        )