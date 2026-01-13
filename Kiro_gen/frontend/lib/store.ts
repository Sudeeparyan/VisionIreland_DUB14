import { create } from 'zustand';

interface AudioItem {
  id: string;
  title: string;
  characters: string[];
  scenes: string[];
  duration: number;
  uploadedAt: string;
}

interface AppState {
  // Upload state
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;

  // Library state
  library: AudioItem[];
  isLoadingLibrary: boolean;
  libraryError: string | null;

  // Playback state
  currentAudio: AudioItem | null;
  isPlaying: boolean;
  currentTime: number;

  // Actions
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setUploadError: (error: string | null) => void;
  setLibrary: (items: AudioItem[]) => void;
  setLoadingLibrary: (loading: boolean) => void;
  setLibraryError: (error: string | null) => void;
  setCurrentAudio: (audio: AudioItem | null) => void;
  setPlaying: (playing: boolean) => void;
  setCurrentTime: (time: number) => void;
  addToLibrary: (item: AudioItem) => void;
  removeFromLibrary: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  isUploading: false,
  uploadProgress: 0,
  uploadError: null,
  library: [],
  isLoadingLibrary: false,
  libraryError: null,
  currentAudio: null,
  isPlaying: false,
  currentTime: 0,

  // Actions
  setUploading: (uploading) => set({ isUploading: uploading }),
  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setUploadError: (error) => set({ uploadError: error }),
  setLibrary: (items) => set({ library: items }),
  setLoadingLibrary: (loading) => set({ isLoadingLibrary: loading }),
  setLibraryError: (error) => set({ libraryError: error }),
  setCurrentAudio: (audio) => set({ currentAudio: audio }),
  setPlaying: (playing) => set({ isPlaying: playing }),
  setCurrentTime: (time) => set({ currentTime: time }),
  addToLibrary: (item) =>
    set((state) => ({
      library: [...state.library, item],
    })),
  removeFromLibrary: (id) =>
    set((state) => ({
      library: state.library.filter((item) => item.id !== id),
    })),
}));
