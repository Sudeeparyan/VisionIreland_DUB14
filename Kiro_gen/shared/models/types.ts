/**
 * Shared type definitions for Comic Audio Narrator
 * Used by both frontend and backend
 */

// Character representation
export interface Character {
  id: string;
  name: string;
  visualDescription: string;
  personality: string;
  voiceProfile: VoiceProfile;
  firstIntroduced: number;
  lastSeen: number;
  visualSignatures: string[];
}

// Voice profile for character
export interface VoiceProfile {
  voiceId: string;
  gender: 'male' | 'female' | 'neutral';
  age: 'child' | 'young-adult' | 'adult' | 'senior';
  tone: string;
}

// Scene representation
export interface Scene {
  id: string;
  location: string;
  visualDescription: string;
  timeOfDay?: string;
  atmosphere?: string;
  colorPalette?: string[];
  lighting?: string;
  firstIntroduced: number;
  lastSeen: number;
}

// Panel representation
export interface Panel {
  id: string;
  sequenceNumber: number;
  imageData: Buffer;
  imageFormat: 'png' | 'jpeg';
  imageResolution: { width: number; height: number };
  extractedText?: string;
  metadata?: Record<string, string>;
}

// Panel narrative
export interface PanelNarrative {
  panelId: string;
  visualAnalysis: {
    characters: string[];
    objects: string[];
    spatialLayout: string;
    colors: string[];
    mood: string;
  };
  sceneDescription?: string;
  actionDescription: string;
  dialogue: DialogueLine[];
  characterUpdates?: Character[];
  audioDescription: string;
}

// Dialogue line
export interface DialogueLine {
  characterId: string;
  text: string;
  emotion?: string;
}

// Audio segment
export interface AudioSegment {
  panelId: string;
  audioData: Buffer;
  duration: number;
  voiceId: string;
}

// Composite audio
export interface CompositeAudio {
  segments: AudioSegment[];
  totalDuration: number;
  metadata: AudioMetadata;
}

// Audio metadata
export interface AudioMetadata {
  title: string;
  characters: Character[];
  scenes: Scene[];
  generatedAt: Date;
  modelUsed: string;
}

// Stored audio
export interface StoredAudio {
  id: string;
  s3Key: string;
  localPath?: string;
  metadata: AudioMetadata;
  fileSize: number;
  uploadedAt: Date;
}

// Library index
export interface LibraryIndex {
  items: StoredAudio[];
  lastUpdated: Date;
  totalSize: number;
}

// Upload request
export interface UploadRequest {
  file: File;
  title?: string;
  metadata?: Record<string, string>;
}

// Processing status
export interface ProcessingStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  audioUrl?: string;
}

// Audio library item
export interface AudioLibraryItem {
  id: string;
  title: string;
  uploadDate: Date;
  duration: number;
  characters: string[];
  audioUrl: string;
  localPath?: string;
}
