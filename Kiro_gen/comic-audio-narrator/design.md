# Design Document: Comic Audio Narrator

## Overview

The Comic Audio Narrator transforms PDF comic books into engaging audio narratives for blind and visually impaired users. The system leverages AWS Bedrock (Nova Pro, Claude) for intelligent panel analysis and narrative generation, AWS Polly for high-quality text-to-speech synthesis, and AWS S3 for distributed storage. The architecture emphasizes modularity, cost efficiency, and accessibility, with a web-based interface for user interaction and a backend processing pipeline that maintains character consistency, scene context, and professional audio description standards.

### Integration with Vision Ireland

This design builds upon and formalizes the Vision Ireland project (https://github.com/Sudeeparyan/VisionIreland_DUB14.git). The Vision Ireland repository contains foundational implementation work. This spec provides:
- Formal requirements and acceptance criteria
- Comprehensive design patterns and interfaces
- Correctness properties with property-based testing strategy
- WCAG 2.2 accessibility compliance framework
- Cost-optimized AWS service integration patterns
- Production-ready implementation tasks

## Architecture

The system follows a modular, event-driven architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Interface                             │
│                    (React/Next.js + WCAG 2.2)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Lambda                          │
│              (Request validation, orchestration)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PDF Extract  │  │ Bedrock      │  │ Polly Audio  │
│ (PyPDF2)     │  │ Vision       │  │ Generation   │
│ Extract      │  │ Analysis     │  │              │
│ Panel Images │  │ (Image-based)│  │              │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                 │
│         (S3 for audio, metadata, library management)            │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Visual-First Analysis**: Panel images are the primary input to Bedrock; visual content drives narrative generation
2. **Modularity**: Each component (PDF processing, visual analysis, audio generation, storage) operates independently
3. **Stateful Processing**: Character and scene context maintained throughout comic processing based on visual analysis
4. **Cost Optimization**: Batch processing, caching, and model selection for efficiency
5. **Accessibility First**: WCAG 2.2 compliance throughout, audio description standards
6. **User Control**: Local storage + cloud library options for flexibility

## Components and Interfaces

### 1. Web Interface Component

**Responsibility**: User interaction, file upload, library management, playback

**Key Features**:
- PDF file upload with validation (format, size limits)
- Progress tracking during processing
- Audio playback with accessible controls
- Library browsing with search/filter
- Metadata display (title, upload date, character list)

**Accessibility Requirements**:
- WCAG 2.2 Level AA compliance
- Keyboard navigation support
- Screen reader compatibility with ARIA labels
- Color contrast ratios ≥ 4.5:1
- Text resizing support (up to 200%)

**Interfaces**:
```typescript
interface UploadRequest {
  file: File;
  title?: string;
  metadata?: Record<string, string>;
}

interface ProcessingStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  message: string;
  audioUrl?: string;
}

interface AudioLibraryItem {
  id: string;
  title: string;
  uploadDate: Date;
  duration: number;
  characters: string[];
  audioUrl: string;
  localPath?: string;
}
```

### 2. PDF Processing Component

**Responsibility**: Extract panels from PDF as images, maintain sequential order, prepare visual content for analysis

**Key Features**:
- PDF parsing and validation
- Panel extraction as high-quality images (preserving visual content)
- OCR for text detection (supplementary to visual analysis)
- Sequential ordering preservation
- Metadata extraction (title, author if available)
- Image optimization for Bedrock vision analysis

**Critical Design Note**: Panels are extracted as images, not text. The visual content (artwork, character appearance, scene composition, spatial relationships, colors, expressions) is preserved and sent to Bedrock for analysis. OCR-extracted text is supplementary only.

**Interfaces**:
```typescript
interface Panel {
  id: string;
  sequenceNumber: number;
  imageData: Buffer; // High-quality image of the panel
  imageFormat: 'png' | 'jpeg';
  imageResolution: { width: number; height: number };
  extractedText?: string; // Supplementary text from OCR
  metadata?: Record<string, string>;
}

interface ComicMetadata {
  title: string;
  author?: string;
  totalPanels: number;
  extractedAt: Date;
  imageQuality: 'high' | 'standard';
}
```

### 3. Bedrock Analysis Component

**Responsibility**: Analyze panel images using vision capabilities, generate narrative content, maintain character/scene context

**Key Features**:
- **Vision-based panel analysis**: Bedrock models analyze the actual visual content of each panel image
- Visual element detection: Characters, objects, environments, spatial relationships, colors, expressions
- Character identification and tracking from visual appearance
- Scene context maintenance from visual composition
- Narrative generation following audio description standards
- Character voice profile assignment based on visual personality cues
- Dialogue extraction from speech bubbles and text in images

**Visual Analysis Process**:
1. Send panel image to Bedrock vision model
2. Model analyzes: character appearance, positioning, expressions, environment, colors, composition
3. Model identifies: new characters, scene changes, action sequences, emotional tone
4. Model generates: detailed audio description incorporating all visual elements
5. System maintains context: character registry, scene tracking, story state

**Critical Design Note**: The Bedrock model receives the actual panel image and analyzes its visual content. This includes:
- Character appearance, clothing, expressions, body language
- Scene composition, lighting, colors, atmosphere
- Spatial relationships and positioning of elements
- Action and movement depicted visually
- Emotional tone conveyed through visual elements
- Visual storytelling techniques (panel layout, perspective, etc.)

**Context Management**:
- Maintains character registry (visual appearance, personality inferred from visuals, voice profile)
- Tracks scene locations and visual descriptions
- Preserves story continuity across panels
- Detects significant visual changes requiring re-introduction

**Interfaces**:
```typescript
interface Character {
  id: string;
  name: string;
  visualDescription: string; // Based on visual analysis
  personality: string; // Inferred from visual cues
  voiceProfile: VoiceProfile;
  firstIntroduced: number; // panel number
  lastSeen: number;
  visualSignatures: string[]; // Distinctive visual features
}

interface VoiceProfile {
  voiceId: string; // Polly voice ID
  gender: 'male' | 'female' | 'neutral';
  age: 'child' | 'young-adult' | 'adult' | 'senior';
  tone: string; // e.g., "heroic", "comedic", "mysterious"
}

interface Scene {
  id: string;
  location: string;
  visualDescription: string; // Based on visual analysis
  timeOfDay?: string;
  atmosphere?: string;
  colorPalette?: string[];
  lighting?: string;
  firstIntroduced: number;
  lastSeen: number;
}

interface PanelNarrative {
  panelId: string;
  visualAnalysis: {
    characters: string[]; // Characters visible in panel
    objects: string[]; // Objects and elements
    spatialLayout: string; // Spatial relationships
    colors: string[]; // Color palette
    mood: string; // Emotional tone
  };
  sceneDescription?: string; // Only if scene is new/changed
  actionDescription: string; // Based on visual action
  dialogue: DialogueLine[];
  characterUpdates?: Character[]; // Only if significant visual changes
  audioDescription: string; // Full narrative for this panel
}

interface DialogueLine {
  characterId: string;
  text: string;
  emotion?: string;
}

interface BedrockAnalysisContext {
  characters: Map<string, Character>;
  scenes: Map<string, Scene>;
  storyState: Record<string, any>;
}
```

### 4. Polly Audio Generation Component

**Responsibility**: Convert narrative text to audio with character-appropriate voices

**Key Features**:
- Text-to-speech synthesis using Polly
- Character voice profile application
- Audio quality optimization for cost
- Batch processing for efficiency
- Audio file management

**Interfaces**:
```typescript
interface AudioGenerationRequest {
  text: string;
  voiceId: string;
  engine: 'neural' | 'standard'; // neural for quality, standard for cost
  outputFormat: 'mp3' | 'ogg_vorbis';
}

interface AudioSegment {
  panelId: string;
  audioData: Buffer;
  duration: number;
  voiceId: string;
}

interface CompositeAudio {
  segments: AudioSegment[];
  totalDuration: number;
  metadata: AudioMetadata;
}

interface AudioMetadata {
  title: string;
  characters: Character[];
  scenes: Scene[];
  generatedAt: Date;
  modelUsed: string;
}
```

### 5. Storage Component

**Responsibility**: Manage local and cloud storage, library organization, metadata persistence

**Key Features**:
- S3 storage for audio files and metadata
- Local device storage management
- Library indexing and search
- Metadata persistence (JSON)
- Cost-optimized storage classes

**Interfaces**:
```typescript
interface StorageConfig {
  s3Bucket: string;
  localStoragePath: string;
  storageClass: 'STANDARD' | 'INTELLIGENT_TIERING' | 'GLACIER';
}

interface StoredAudio {
  id: string;
  s3Key: string;
  localPath?: string;
  metadata: AudioMetadata;
  fileSize: number;
  uploadedAt: Date;
}

interface LibraryIndex {
  items: StoredAudio[];
  lastUpdated: Date;
  totalSize: number;
}
```

## Data Models

### Comic Processing Pipeline

```
PDF Input
   ↓
[PDF Extraction] → Panels + Metadata
   ↓
[Bedrock Analysis] → Narratives + Character/Scene Context
   ↓
[Polly Generation] → Audio Segments
   ↓
[Audio Composition] → Complete Audio File
   ↓
[Storage] → S3 + Local + Library Index
```

### Character Lifecycle

```
Panel 1: Character appears
   ↓
[First Introduction] → Full description + voice assignment
   ↓
Panels 2-N: Character appears
   ↓
[Consistency Check] → Use same voice, minimal description
   ↓
[Significant Change] → Update description if appearance/role changes
   ↓
[Final Appearance] → Conclude character arc
```

### Scene Lifecycle

```
Panel 1: New location
   ↓
[Scene Introduction] → Full description + atmosphere
   ↓
Panels 2-N: Same location
   ↓
[Scene Reference] → Use location name, avoid repetition
   ↓
[Scene Change] → New location description
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.


### Correctness Properties

Based on the acceptance criteria analysis, here are the key properties that the system must satisfy:

**Property 1: Panel Extraction Completeness**
*For any* valid PDF comic, extracting panels SHALL result in all panels being present and in sequential order matching the original PDF
**Validates: Requirements 1.2**

**Property 2: Character Voice Consistency**
*For any* character appearing in multiple panels, the system SHALL use the same voice profile for all appearances of that character
**Validates: Requirements 2.3, 2.5**

**Property 3: Character Description Non-Repetition**
*For any* character that has been previously introduced, subsequent appearances SHALL not include the full character description unless significant changes have occurred
**Validates: Requirements 7.1**

**Property 4: Scene Reference Consistency**
*For any* scene that has been established, subsequent panels in the same scene SHALL reference the location by name rather than re-describing it
**Validates: Requirements 7.2, 3.2**

**Property 5: Story Continuity Preservation**
*For any* sequence of panels, the generated narrative SHALL maintain character state, scene context, and story flow across all panels
**Validates: Requirements 7.3**

**Property 6: Audio Description Spatial Details**
*For any* panel describing action or movement, the generated audio description SHALL include specific details about character positions, directions, and spatial relationships
**Validates: Requirements 9.1**

**Property 7: Audio Description Tense and Voice**
*For any* visual element being narrated, the generated description SHALL use present tense and active voice
**Validates: Requirements 9.2**

**Property 8: Audio Description Context**
*For any* object or environment being described, the generated description SHALL include relevant details that establish context and atmosphere
**Validates: Requirements 9.3**

**Property 9: Dialogue Integration**
*For any* panel containing dialogue, the generated narrative SHALL integrate character dialogue naturally with action descriptions rather than separating them
**Validates: Requirements 9.4**

**Property 10: Emotional Conveyance**
*For any* panel expressing emotions or expressions, the generated description SHALL convey these through descriptive language matching professional audio description standards
**Validates: Requirements 9.5**

**Property 11: Local Audio Storage**
*For any* completed audio generation, the system SHALL store the audio file locally on the user's device
**Validates: Requirements 4.1**

**Property 12: S3 Audio Upload**
*For any* completed audio generation, the system SHALL upload the audio file to the S3 library bucket
**Validates: Requirements 4.2**

**Property 13: Library Metadata Preservation**
*For any* stored audio file, the system SHALL preserve and retrieve all metadata including comic title, upload date, and character information
**Validates: Requirements 4.5**

**Property 14: Library Completeness**
*For any* user accessing the library, the system SHALL display all previously generated audio narratives with complete metadata
**Validates: Requirements 4.3**

**Property 15: File Validation**
*For any* file upload attempt, the system SHALL validate the file format and size, rejecting invalid files before processing
**Validates: Requirements 5.2**

**Property 16: Library Search and Filter**
*For any* library search or filter operation, the system SHALL return only audio narratives matching the specified criteria
**Validates: Requirements 5.6**

**Property 17: Batch Processing Optimization**
*For any* large PDF processing, the system SHALL implement batch processing and caching to minimize API calls to Bedrock and Polly
**Validates: Requirements 6.4**

**Property 18: WCAG 2.2 Compliance**
*For any* web interface interaction, the system SHALL meet WCAG 2.2 Level AA compliance standards
**Validates: Requirements 10.1**

**Property 19: Keyboard Navigation**
*For any* web interface functionality, the system SHALL provide full access via keyboard navigation without requiring a mouse
**Validates: Requirements 10.2**

**Property 20: Screen Reader Compatibility**
*For any* web interface element, the system SHALL provide appropriate ARIA labels and semantic HTML structure for screen reader compatibility
**Validates: Requirements 10.3**

**Property 21: Color Contrast**
*For any* text element in the web interface, the system SHALL maintain color contrast ratios of at least 4.5:1
**Validates: Requirements 10.4**

**Property 22: Form Accessibility**
*For any* form element in the web interface, the system SHALL provide clear labels and error messages
**Validates: Requirements 10.5**

**Property 23: Text Resizing Support**
*For any* web interface interaction, the system SHALL remain fully functional when text is resized up to 200%
**Validates: Requirements 10.6**

**Property 24: Audio Control Accessibility**
*For any* audio playback control, the system SHALL be accessible and clearly labeled for all users
**Validates: Requirements 10.7**

## Error Handling

### PDF Processing Errors
- Invalid PDF format: Return clear error message, suggest supported formats
- Corrupted PDF: Attempt recovery, fall back to manual panel specification
- Unsupported PDF features: Log warning, continue with available content
- File size exceeded: Return error with size limit information

### Bedrock Analysis Errors
- API rate limiting: Implement exponential backoff and queuing
- Model unavailability: Fall back to alternative model (Nova Pro ↔ Claude)
- Analysis timeout: Retry with smaller batch size
- Invalid response: Log error, retry with adjusted parameters

### Polly Audio Generation Errors
- Voice unavailability: Fall back to alternative voice with similar profile
- Audio generation timeout: Retry with standard engine instead of neural
- Invalid text input: Sanitize and retry
- Output format error: Convert to alternative format

### Storage Errors
- S3 upload failure: Retry with exponential backoff, queue for later
- Local storage full: Prompt user, offer cloud-only option
- Metadata corruption: Rebuild from audio file properties
- Library index inconsistency: Rebuild index from S3 inventory

### Web Interface Errors
- File upload failure: Display user-friendly error message
- Processing timeout: Show progress, allow retry
- Audio playback failure: Offer alternative formats
- Library access failure: Suggest troubleshooting steps

## Testing Strategy

### Unit Testing Approach

Unit tests verify specific examples and edge cases:
- PDF extraction with various comic formats
- Character identification and voice profile assignment
- Scene detection and context management
- Audio file storage and retrieval
- Form validation and error handling
- WCAG compliance for individual components

### Property-Based Testing Approach

Property-based tests verify universal properties using the **fast-check** library (JavaScript) or **hypothesis** (Python):
- Minimum 100 iterations per property test
- Random input generation constrained to valid input space
- Each property test tagged with requirement reference
- Format: `**Feature: comic-audio-narrator, Property {N}: {property_text}**`

**Property-Based Testing Framework**: fast-check (JavaScript) or hypothesis (Python)

**Configuration Requirements**:
- Minimum 100 iterations per test
- Seed-based reproducibility for failures
- Timeout: 30 seconds per test
- Failure reporting with minimal failing example

### Test Coverage Strategy

**Core Functionality Tests**:
- Panel extraction and ordering
- Character consistency across panels
- Scene context preservation
- Audio generation and storage
- Library management

**Accessibility Tests**:
- WCAG 2.2 compliance validation
- Keyboard navigation verification
- Screen reader compatibility
- Color contrast verification
- Text resizing functionality

**Integration Tests**:
- End-to-end PDF to audio workflow
- Bedrock → Polly integration
- Local + S3 storage synchronization
- Library search and retrieval

**Edge Case Tests**:
- Empty PDFs
- Single-panel comics
- Very large PDFs (100+ panels)
- Special characters in titles/descriptions
- Concurrent uploads
- Storage quota scenarios

### Test Execution Strategy

1. Run unit tests on every code change
2. Run property-based tests before each release
3. Run integration tests in staging environment
4. Run accessibility tests with automated tools (axe, WAVE)
5. Manual accessibility testing with screen readers

