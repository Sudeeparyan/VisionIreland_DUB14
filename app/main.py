"""
Comic Voice Agent - Main FastAPI Application
Brings comic books to life through voice for blind people and children
"""

import asyncio
import base64
import json
import os
import uuid
from pathlib import Path
from typing import AsyncIterable, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Query, UploadFile, WebSocket, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.events.event import Event
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from .config import (
    APP_NAME,
    UPLOAD_DIR,
    PROCESSED_DIR,
    MAX_UPLOAD_SIZE_BYTES,
    ALLOWED_EXTENSIONS,
    VOICE_NAME,
    CHILD_MODE,
    validate_config,
)
from .agents.storyteller import create_storyteller_agent
from .pdf_processor import PDFExtractor, ComicAnalyzer, ComicParser
from .tools.navigation import (
    navigate_to_page,
    get_current_page,
    go_to_next_page,
    go_to_previous_page,
)
from .tools.description import describe_current_scene, get_character_info
from .tools.storytelling import get_page_narration, get_welcome_message

# Load environment variables
load_dotenv()

# Validate configuration
config_errors = validate_config()
if config_errors:
    print("Configuration errors:")
    for error in config_errors:
        print(f"  - {error}")

# ==========================================
# Application Setup
# ==========================================
app = FastAPI(
    title="Comic Voice Agent",
    description="An accessible voice-powered platform for experiencing comic books",
    version="1.0.0",
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Session management
session_service = InMemorySessionService()

# Store for comic data and session state
comic_sessions: Dict[str, Dict] = {}


# ==========================================
# Helper Functions
# ==========================================
def get_or_create_session(session_id: str) -> Dict:
    """Get or create a session state dictionary."""
    if session_id not in comic_sessions:
        comic_sessions[session_id] = {
            "session_id": session_id,
            "comic_loaded": False,
            "comic_data": {},
            "current_page": 1,
            "total_pages": 0,
            "settings": {
                "speech_rate": 1.0,
                "voice": VOICE_NAME,
                "child_mode": CHILD_MODE,
                "auto_advance": False,
            },
        }
    return comic_sessions[session_id]


async def process_comic_pdf(file_path: Path, session_id: str) -> Dict:
    """
    Process a comic PDF file:
    1. Extract pages and images
    2. Analyze with Gemini Vision (with graceful fallback)
    3. Parse into structured format
    """
    session = get_or_create_session(session_id)
    output_dir = PROCESSED_DIR / session_id

    # Step 1: Extract PDF content
    print(f"Extracting PDF: {file_path}")
    with PDFExtractor(str(file_path)) as extractor:
        pages = extractor.extract_all_pages(output_dir=output_dir)
        metadata = extractor.metadata

    # Step 2: Try to analyze with Gemini Vision (with fallback)
    print("Analyzing comic with AI...")
    analysis_results = []
    ai_analysis_available = False

    try:
        analyzer = ComicAnalyzer()
        child_mode = session["settings"].get("child_mode", False)

        # Analyze all pages but with AI for first few
        for idx, page in enumerate(pages):
            if idx < 10 and page.get("image_base64"):  # AI analyze first 10 pages
                try:
                    result = await analyzer.analyze_page(
                        image_base64=page["image_base64"],
                        page_number=page["page_number"],
                        child_mode=child_mode,
                    )
                    analysis_results.append(result)
                    ai_analysis_available = True
                except Exception as e:
                    print(f"AI analysis failed for page {page['page_number']}: {e}")
                    # Create fallback result from extracted text
                    analysis_results.append(
                        {
                            "success": True,
                            "page_number": page["page_number"],
                            "parsed": {
                                "scene_setting": f"Comic book page {page['page_number']}",
                                "narration_script": page.get(
                                    "text",
                                    "This page contains comic panels with visual storytelling.",
                                )
                                or f"Page {page['page_number']} - A visual comic page with illustrations.",
                                "action_summary": "Visual storytelling in comic format",
                                "characters": "",
                                "panels": "",
                            },
                        }
                    )
            else:
                # For pages beyond the first 10, use text-only fallback
                analysis_results.append(
                    {
                        "success": True,
                        "page_number": page["page_number"],
                        "parsed": {
                            "scene_setting": f"Comic book page {page['page_number']}",
                            "narration_script": page.get(
                                "text",
                                "This page contains comic panels with visual storytelling.",
                            )
                            or f"Page {page['page_number']} - A visual comic page with illustrations.",
                            "action_summary": "Visual storytelling in comic format",
                            "characters": "",
                            "panels": "",
                        },
                    }
                )
    except Exception as e:
        print(f"AI analyzer initialization failed: {e}")
        # Create basic results from extracted text for ALL pages
        for page in pages:
            analysis_results.append(
                {
                    "success": True,
                    "page_number": page["page_number"],
                    "parsed": {
                        "scene_setting": f"Comic book page {page['page_number']}",
                        "narration_script": page.get(
                            "text",
                            "This page contains comic panels with visual storytelling.",
                        )
                        or f"Page {page['page_number']} - A visual comic page with illustrations.",
                        "action_summary": "Visual storytelling in comic format",
                        "characters": "",
                        "panels": "",
                    },
                }
            )

    # Step 3: Parse into structured format
    print("Parsing comic structure...")
    parser = ComicParser()
    comic = parser.parse_from_analysis(metadata, pages, analysis_results)

    # Save parsed data
    parsed_file = output_dir / "comic_data.json"
    parser.save_to_file(str(parsed_file))

    # Update session
    comic_dict = parser.to_dict()
    session["comic_loaded"] = True
    session["comic_data"] = comic_dict
    session["current_page"] = 1
    session["total_pages"] = comic_dict.get("page_count", len(pages))

    return {
        "success": True,
        "title": comic_dict.get("title", "Comic Book"),
        "author": comic_dict.get("author", "Unknown"),
        "page_count": session["total_pages"],
        "synopsis": comic_dict.get("synopsis", ""),
        "comic_loaded": True,
        "ai_enhanced": ai_analysis_available,
    }


def start_agent_session(session_id: str, is_audio: bool = False):
    """Start an ADK agent session for a user."""
    session_state = get_or_create_session(session_id)

    # Create session in ADK
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    # Create agent with current context
    agent = create_storyteller_agent(session_state)

    # Create runner
    runner = Runner(
        app_name=APP_NAME,
        agent=agent,
        session_service=session_service,
    )

    # Configure response modality
    modality = "AUDIO" if is_audio else "TEXT"

    # Voice configuration
    voice_name = session_state["settings"].get("voice", VOICE_NAME)
    speech_config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
        )
    )

    config = {"response_modalities": [modality], "speech_config": speech_config}

    if is_audio:
        config["output_audio_transcription"] = {}

    run_config = RunConfig(**config)

    # Create request queue
    live_request_queue = LiveRequestQueue()

    # Start live session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    return live_events, live_request_queue


async def agent_to_client_messaging(
    websocket: WebSocket, live_events: AsyncIterable[Event | None], session_id: str
):
    """Handle messages from agent to client."""
    session = get_or_create_session(session_id)

    async for event in live_events:
        if event is None:
            continue

        # Handle turn complete or interrupted
        if event.turn_complete or event.interrupted:
            message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            # Include current page info
            if session.get("comic_loaded"):
                message["current_page"] = session.get("current_page", 1)
                message["total_pages"] = session.get("total_pages", 1)

            await websocket.send_text(json.dumps(message))
            continue

        # Get content part
        part = event.content and event.content.parts and event.content.parts[0]
        if not part or not isinstance(part, types.Part):
            continue

        # Send text (streaming)
        if part.text and event.partial:
            message = {
                "mime_type": "text/plain",
                "data": part.text,
                "role": "model",
            }
            await websocket.send_text(json.dumps(message))

        # Send audio
        is_audio = (
            part.inline_data
            and part.inline_data.mime_type
            and part.inline_data.mime_type.startswith("audio/pcm")
        )
        if is_audio and part.inline_data.data:
            message = {
                "mime_type": "audio/pcm",
                "data": base64.b64encode(part.inline_data.data).decode("ascii"),
                "role": "model",
            }
            await websocket.send_text(json.dumps(message))


async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue, session_id: str
):
    """Handle messages from client to agent."""
    session = get_or_create_session(session_id)

    while True:
        message_json = await websocket.receive_text()
        message = json.loads(message_json)

        mime_type = message.get("mime_type", "text/plain")
        data = message.get("data", "")
        role = message.get("role", "user")

        # Handle special commands locally for faster response
        if mime_type == "text/plain":
            lower_data = data.lower().strip()

            # Navigation commands
            if lower_data in ["next", "next page"]:
                result = go_to_next_page(session)
                if result["success"]:
                    # Get narration for new page
                    narration = get_page_narration(
                        session.get("comic_data", {}), session["current_page"]
                    )
                    data = f"Going to page {session['current_page']}. " + narration.get(
                        "narration", ""
                    )

            elif lower_data in ["previous", "previous page", "back", "go back"]:
                result = go_to_previous_page(session)
                if result["success"]:
                    narration = get_page_narration(
                        session.get("comic_data", {}), session["current_page"]
                    )
                    data = (
                        f"Going back to page {session['current_page']}. "
                        + narration.get("narration", "")
                    )

            # Inject context about current state
            if session.get("comic_loaded"):
                context = f"[Context: Page {session['current_page']} of {session['total_pages']}] "
                data = context + data

        # Send to agent
        if mime_type == "text/plain":
            content = types.Content(role=role, parts=[types.Part.from_text(text=data)])
            live_request_queue.send_content(content=content)

        elif mime_type == "audio/pcm":
            decoded_data = base64.b64decode(data)
            live_request_queue.send_realtime(
                types.Blob(data=decoded_data, mime_type=mime_type)
            )


# ==========================================
# API Routes
# ==========================================
@app.get("/")
async def root():
    """Serve the main application page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload")
async def upload_comic(file: UploadFile = File(...)):
    """
    Upload and process a comic book PDF.

    Returns comic metadata and sets up the session for reading.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large")

    # Generate session ID and save file
    session_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{session_id}.pdf"

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # Process the comic
        result = await process_comic_pdf(file_path, session_id)
        result["session_id"] = session_id
        return JSONResponse(content=result)

    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/comic/{session_id}")
async def get_comic_info(session_id: str):
    """Get information about a loaded comic."""
    session = comic_sessions.get(session_id)

    if not session or not session.get("comic_loaded"):
        raise HTTPException(status_code=404, detail="Comic not found")

    comic_data = session.get("comic_data", {})

    return {
        "title": comic_data.get("title", "Unknown"),
        "author": comic_data.get("author", "Unknown"),
        "page_count": session.get("total_pages", 0),
        "current_page": session.get("current_page", 1),
        "synopsis": comic_data.get("synopsis", ""),
    }


@app.get("/api/comic/{session_id}/page/{page_number}")
async def get_page(session_id: str, page_number: int):
    """Get data for a specific page."""
    session = comic_sessions.get(session_id)

    if not session or not session.get("comic_loaded"):
        raise HTTPException(status_code=404, detail="Comic not found")

    result = describe_current_scene(
        {"current_page": page_number, "total_pages": session.get("total_pages", 1)},
        session.get("comic_data", {}),
        detail_level="full",
    )

    return result


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, session_id: str, is_audio: str = Query("false")
):
    """WebSocket endpoint for real-time communication with the agent."""
    await websocket.accept()
    print(f"Client {session_id} connected, audio: {is_audio}")

    try:
        # Start agent session
        is_audio_bool = is_audio.lower() == "true"
        live_events, live_request_queue = start_agent_session(session_id, is_audio_bool)

        # Run both directions concurrently
        agent_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events, session_id)
        )
        client_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue, session_id)
        )

        await asyncio.gather(agent_task, client_task)

    except Exception as e:
        print(f"WebSocket error for {session_id}: {e}")
    finally:
        print(f"Client {session_id} disconnected")


# ==========================================
# Health Check
# ==========================================
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": APP_NAME}


# ==========================================
# Run Application
# ==========================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
