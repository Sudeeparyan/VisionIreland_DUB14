# 🎙️ Comic Book Voice Agent - Vision Ireland

An accessible voice-powered platform that makes comic books interactive and enjoyable for **blind people** and **children**. Built with Google ADK (Agent Development Kit) for intelligent voice interactions.

## 🎯 Project Overview

This platform transforms static PDF comic books into an immersive audio experience:

- **PDF Upload**: Simple drag-and-drop or click-to-upload interface
- **AI-Powered Scene Description**: Detailed descriptions of visual elements for blind users
- **Voice Narration**: Professional storytelling with character voices and sound effects
- **Interactive Q&A**: Ask questions about the story, characters, or what's happening
- **Accessible UI**: WCAG 2.1 AA compliant, screen reader friendly, keyboard navigable

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (Accessible)                  │
│  - PDF Upload        - Voice Controls       - Navigation        │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  - WebSocket for real-time audio    - PDF Processing            │
│  - Session Management               - File Upload Handling      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PDF PROCESSING MODULE                         │
│  - Page Extraction      - Image Analysis     - Text OCR         │
│  - Panel Detection      - Scene Segmentation                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADK VOICE AGENTS                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   STORYTELLER   │  │ SCENE DESCRIBER │  │  GUIDE AGENT    │ │
│  │   - Narration   │  │ - Visual desc   │  │  - Q&A support  │ │
│  │   - Voices      │  │ - Emotions      │  │  - Navigation   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API Key

### Installation

```bash
# Navigate to project directory
cd comic-voice-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API key
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Run the Application

```bash
# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

## 🎤 Voice Commands

The agent understands natural voice commands:

- **"Read the current page"** - Narrates the current comic page
- **"Describe what I see"** - Provides detailed visual descriptions
- **"Who is speaking?"** - Identifies characters in dialogue
- **"Go to the next page"** - Navigate forward
- **"Go back"** - Navigate to previous page
- **"What's happening?"** - Explains the current scene
- **"Start from the beginning"** - Restart the comic
- **"Tell me about [character]"** - Character information

## ♿ Accessibility Features

### WCAG 2.1 AA Compliance

- **Perceivable**
  - Text alternatives for all images
  - Audio descriptions for visual content
  - High contrast mode (4.5:1 ratio minimum)
  - Resizable text (up to 200%)

- **Operable**
  - Full keyboard navigation
  - Large touch targets (44x44px minimum)
  - No time limits on interactions
  - Skip navigation links

- **Understandable**
  - Simple, clear language
  - Consistent navigation
  - Error prevention and correction

- **Robust**
  - Screen reader compatible
  - ARIA labels and live regions
  - Semantic HTML structure

### Screen Reader Support

- NVDA, JAWS, VoiceOver compatible
- Live region announcements for dynamic content
- Proper heading hierarchy

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause narration |
| → | Next page |
| ← | Previous page |
| R | Repeat current narration |
| D | Describe current scene |
| H | Help menu |
| Esc | Stop narration |

## 📁 Project Structure

```
comic-voice-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── storyteller.py   # Main storytelling agent
│   │   ├── scene_describer.py # Visual description agent
│   │   └── guide_agent.py   # Interactive Q&A agent
│   ├── pdf_processor/
│   │   ├── __init__.py
│   │   ├── extractor.py     # PDF extraction utilities
│   │   ├── analyzer.py      # Image/scene analysis
│   │   └── parser.py        # Comic panel parsing
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── navigation.py    # Page navigation tools
│   │   ├── description.py   # Scene description tools
│   │   └── storytelling.py  # Narration tools
│   └── static/
│       ├── index.html       # Accessible web interface
│       ├── css/
│       │   └── styles.css   # Accessible styles
│       └── js/
│           ├── app.js       # Main application logic
│           ├── audio-player.js
│           ├── audio-recorder.js
│           ├── pcm-player-processor.js
│           └── pcm-recorder-processor.js
├── uploads/                  # Uploaded PDFs
├── processed/               # Processed comic data
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

Edit `.env` file:

```env
GOOGLE_API_KEY=your_gemini_api_key
VOICE_NAME=Puck
MAX_UPLOAD_SIZE_MB=50
DEBUG=true
```

## 📖 How It Works

1. **PDF Upload**: User uploads a comic book PDF through the accessible interface
2. **Processing**: The PDF processor extracts pages, images, and text
3. **AI Analysis**: Gemini's vision capabilities analyze each panel for:
   - Character identification
   - Action descriptions
   - Emotional context
   - Speech bubble text
   - Scene setting
4. **Story Structure**: The AI creates a narrative structure with:
   - Character voices
   - Scene transitions
   - Sound effect cues
5. **Interactive Playback**: User controls the experience through:
   - Voice commands
   - Keyboard shortcuts
   - Simple touch controls

## 🎭 Agent Personalities

### Storyteller Agent
- Warm, engaging narrator voice
- Distinct character voices for dialogue
- Expressive sound effect descriptions
- Pace adjusted for comprehension

### Scene Describer Agent
- Detailed visual descriptions
- Focus on important narrative elements
- Describes character expressions and body language
- Environmental and atmospheric details

### Guide Agent
- Patient and helpful
- Answers questions in simple language
- Provides navigation assistance
- Offers contextual help

## 🧒 Child-Friendly Mode

Enable simplified mode for younger audiences:
- Simpler vocabulary
- Shorter descriptions
- More encouraging tone
- Interactive quizzes about the story

## 📜 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Google ADK (Agent Development Kit)
- Vision Ireland for accessibility guidance
- The blind and visually impaired community for feedback
