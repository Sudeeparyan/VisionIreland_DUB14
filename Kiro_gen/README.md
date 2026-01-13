# Comic Audio Narrator

Transform comic books into engaging audio narratives for blind and visually impaired users using AWS Bedrock and Polly.

## Project Structure

```
comic-audio-narrator/
├── backend/                 # Python FastAPI backend service
│   ├── src/
│   │   ├── pdf_processing/  # PDF extraction and panel processing
│   │   ├── bedrock_analysis/# Vision-based panel analysis
│   │   ├── polly_generation/# Text-to-speech audio generation
│   │   ├── storage/         # S3 and local storage management
│   │   ├── api/             # FastAPI endpoints
│   │   ├── config.py        # Configuration management
│   │   └── aws_clients.py   # AWS SDK client initialization
│   ├── tests/               # Backend tests
│   ├── config/              # Configuration files
│   ├── pyproject.toml       # Python dependencies
│   └── .env.example         # Environment variables template
│
├── frontend/                # React/Next.js web interface
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Next.js pages
│   │   ├── lib/             # Utility functions
│   │   └── styles/          # CSS/styling
│   ├── public/              # Static assets
│   ├── tests/               # Frontend tests
│   ├── package.json         # Node.js dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   ├── next.config.js       # Next.js configuration
│   └── .env.example         # Environment variables template
│
├── shared/                  # Shared types and models
│   └── models/
│       └── types.ts         # TypeScript type definitions
│
└── .kiro/specs/             # Feature specifications
    └── comic-audio-narrator/
        ├── requirements.md  # Feature requirements
        ├── design.md        # System design
        └── tasks.md         # Implementation tasks
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS Account with Bedrock, Polly, and S3 access
- AWS CLI configured with credentials

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Configure AWS credentials in .env
# Edit .env with your AWS settings

# Run tests
pytest

# Start development server
uvicorn src.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Configure API URL in .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run tests
npm test

# Start development server
npm run dev
```

## Development

### Backend Development

- **Framework**: FastAPI
- **Testing**: pytest with hypothesis for property-based testing
- **Code Quality**: black, ruff, mypy
- **AWS Services**: Bedrock, Polly, S3

### Frontend Development

- **Framework**: Next.js with React
- **Language**: TypeScript
- **Testing**: Vitest with fast-check for property-based testing
- **Styling**: Tailwind CSS
- **Accessibility**: WCAG 2.2 Level AA compliance

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_pdf_processing.py

# Run property-based tests
pytest tests/test_properties.py -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- tests/components/Upload.test.tsx

# Run property-based tests
npm test -- tests/properties/
```

## Configuration

### Environment Variables

See `.env.example` files in backend and frontend directories for all available configuration options.

**Key Variables**:

- `AWS_REGION`: AWS region for services
- `BEDROCK_MODEL_ID_VISION`: Bedrock model for vision analysis
- `S3_BUCKET_NAME`: S3 bucket for audio storage
- `NEXT_PUBLIC_API_URL`: Backend API URL for frontend

## Architecture

The system follows a modular architecture:

1. **PDF Processing**: Extract panels from PDFs as high-quality images
2. **Bedrock Analysis**: Analyze panel images for characters, scenes, and narrative
3. **Polly Generation**: Convert narrative to audio with character-specific voices
4. **Storage**: Store audio locally and in S3 with metadata
5. **Web Interface**: React/Next.js UI for upload, playback, and library management

## Accessibility

The web interface meets WCAG 2.2 Level AA compliance standards:

- Keyboard navigation support
- Screen reader compatibility
- Color contrast ratios ≥ 4.5:1
- Text resizing support (up to 200%)
- Semantic HTML structure
- ARIA labels and roles

## Documentation

- [Requirements](./kiro/specs/comic-audio-narrator/requirements.md)
- [Design](./kiro/specs/comic-audio-narrator/design.md)
- [Implementation Tasks](./kiro/specs/comic-audio-narrator/tasks.md)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
