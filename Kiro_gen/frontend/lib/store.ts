import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface AudioItem {
  id: string;
  title: string;
  characters: string[];
  scenes: string[];
  duration: number;
  uploadedAt: string;
  fileSize?: number;
  audioUrl?: string;
  localPath?: string;
  metadata?: {
    originalFilename: string;
    processingTime: number;
    modelUsed: string;
    voiceProfiles: Record<string, string>;
  };
}

export interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  result?: any;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

interface AppState {
  // Upload state
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
  currentJobId: string | null;
  jobStatus: JobStatus | null;

  // Library state
  library: AudioItem[];
  isLoadingLibrary: boolean;
  libraryError: string | null;
  libraryPage: number;
  libraryTotal: number;
  searchQuery: string;
  searchResults: AudioItem[];
  isSearching: boolean;

  // Playback state
  currentAudio: AudioItem | null;
  isPlaying: boolean;
  currentTime: number;
  volume: number;
  isMuted: boolean;
  playbackRate: number;

  // UI state
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  notifications: Notification[];

  // Actions - Upload
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setUploadError: (error: string | null) => void;
  setCurrentJobId: (jobId: string | null) => void;
  setJobStatus: (status: JobStatus | null) => void;
  clearUploadState: () => void;

  // Actions - Library
  setLibrary: (items: AudioItem[]) => void;
  setLoadingLibrary: (loading: boolean) => void;
  setLibraryError: (error: string | null) => void;
  setLibraryPage: (page: number) => void;
  setLibraryTotal: (total: number) => void;
  addToLibrary: (item: AudioItem) => void;
  removeFromLibrary: (id: string) => void;
  updateLibraryItem: (id: string, updates: Partial<AudioItem>) => void;
  clearLibrary: () => void;

  // Actions - Search
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: AudioItem[]) => void;
  setSearching: (searching: boolean) => void;
  clearSearch: () => void;

  // Actions - Playback
  setCurrentAudio: (audio: AudioItem | null) => void;
  setPlaying: (playing: boolean) => void;
  setCurrentTime: (time: number) => void;
  setVolume: (volume: number) => void;
  setMuted: (muted: boolean) => void;
  setPlaybackRate: (rate: number) => void;
  clearPlaybackState: () => void;

  // Actions - UI
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // Actions - Bulk operations
  bulkRemoveFromLibrary: (ids: string[]) => void;
  bulkUpdateLibraryItems: (updates: Array<{ id: string; updates: Partial<AudioItem> }>) => void;
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: number;
  duration?: number; // Auto-dismiss after this many ms
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state - Upload
      isUploading: false,
      uploadProgress: 0,
      uploadError: null,
      currentJobId: null,
      jobStatus: null,

      // Initial state - Library
      library: [],
      isLoadingLibrary: false,
      libraryError: null,
      libraryPage: 1,
      libraryTotal: 0,
      searchQuery: '',
      searchResults: [],
      isSearching: false,

      // Initial state - Playback
      currentAudio: null,
      isPlaying: false,
      currentTime: 0,
      volume: 1,
      isMuted: false,
      playbackRate: 1,

      // Initial state - UI
      sidebarOpen: false,
      theme: 'system',
      notifications: [],

      // Actions - Upload
      setUploading: (uploading) => set({ isUploading: uploading }),
      setUploadProgress: (progress) => set({ uploadProgress: progress }),
      setUploadError: (error) => set({ uploadError: error }),
      setCurrentJobId: (jobId) => set({ currentJobId: jobId }),
      setJobStatus: (status) => set({ jobStatus: status }),
      clearUploadState: () => set({
        isUploading: false,
        uploadProgress: 0,
        uploadError: null,
        currentJobId: null,
        jobStatus: null,
      }),

      // Actions - Library
      setLibrary: (items) => set({ library: items }),
      setLoadingLibrary: (loading) => set({ isLoadingLibrary: loading }),
      setLibraryError: (error) => set({ libraryError: error }),
      setLibraryPage: (page) => set({ libraryPage: page }),
      setLibraryTotal: (total) => set({ libraryTotal: total }),
      addToLibrary: (item) => set((state) => ({
        library: [item, ...state.library],
        libraryTotal: state.libraryTotal + 1,
      })),
      removeFromLibrary: (id) => set((state) => ({
        library: state.library.filter((item) => item.id !== id),
        libraryTotal: Math.max(0, state.libraryTotal - 1),
        currentAudio: state.currentAudio?.id === id ? null : state.currentAudio,
      })),
      updateLibraryItem: (id, updates) => set((state) => ({
        library: state.library.map((item) =>
          item.id === id ? { ...item, ...updates } : item
        ),
        currentAudio: state.currentAudio?.id === id
          ? { ...state.currentAudio, ...updates }
          : state.currentAudio,
      })),
      clearLibrary: () => set({
        library: [],
        libraryPage: 1,
        libraryTotal: 0,
        currentAudio: null,
      }),

      // Actions - Search
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchResults: (results) => set({ searchResults: results }),
      setSearching: (searching) => set({ isSearching: searching }),
      clearSearch: () => set({
        searchQuery: '',
        searchResults: [],
        isSearching: false,
      }),

      // Actions - Playback
      setCurrentAudio: (audio) => set({ currentAudio: audio }),
      setPlaying: (playing) => set({ isPlaying: playing }),
      setCurrentTime: (time) => set({ currentTime: time }),
      setVolume: (volume) => set({ volume, isMuted: volume === 0 }),
      setMuted: (muted) => set({ isMuted: muted }),
      setPlaybackRate: (rate) => set({ playbackRate: rate }),
      clearPlaybackState: () => set({
        currentAudio: null,
        isPlaying: false,
        currentTime: 0,
      }),

      // Actions - UI
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      addNotification: (notification) => {
        const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const newNotification: Notification = {
          ...notification,
          id,
          timestamp: Date.now(),
        };

        set((state) => ({
          notifications: [...state.notifications, newNotification],
        }));

        // Auto-dismiss if duration is specified
        if (notification.duration) {
          setTimeout(() => {
            get().removeNotification(id);
          }, notification.duration);
        }
      },
      removeNotification: (id) => set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      })),
      clearNotifications: () => set({ notifications: [] }),

      // Actions - Bulk operations
      bulkRemoveFromLibrary: (ids) => set((state) => ({
        library: state.library.filter((item) => !ids.includes(item.id)),
        libraryTotal: Math.max(0, state.libraryTotal - ids.length),
        currentAudio: ids.includes(state.currentAudio?.id || '') ? null : state.currentAudio,
      })),
      bulkUpdateLibraryItems: (updates) => set((state) => {
        const updatesMap = new Map(updates.map(u => [u.id, u.updates]));
        return {
          library: state.library.map((item) => {
            const itemUpdates = updatesMap.get(item.id);
            return itemUpdates ? { ...item, ...itemUpdates } : item;
          }),
          currentAudio: state.currentAudio && updatesMap.has(state.currentAudio.id)
            ? { ...state.currentAudio, ...updatesMap.get(state.currentAudio.id) }
            : state.currentAudio,
        };
      }),
    }),
    {
      name: 'comic-audio-narrator-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Persist only certain parts of the state
        library: state.library,
        currentAudio: state.currentAudio,
        volume: state.volume,
        isMuted: state.isMuted,
        playbackRate: state.playbackRate,
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);

// Selectors for computed values
export const useLibraryStats = () => {
  return useAppStore((state) => {
    const totalDuration = state.library.reduce((sum, item) => sum + item.duration, 0);
    const totalCharacters = new Set(state.library.flatMap(item => item.characters)).size;
    const totalScenes = new Set(state.library.flatMap(item => item.scenes)).size;
    const averageDuration = state.library.length > 0 ? totalDuration / state.library.length : 0;

    return {
      totalItems: state.library.length,
      totalDuration,
      totalCharacters,
      totalScenes,
      averageDuration,
    };
  });
};

export const useCurrentPlayback = () => {
  return useAppStore((state) => ({
    currentAudio: state.currentAudio,
    isPlaying: state.isPlaying,
    currentTime: state.currentTime,
    volume: state.volume,
    isMuted: state.isMuted,
    playbackRate: state.playbackRate,
  }));
};

export const useUploadState = () => {
  return useAppStore((state) => ({
    isUploading: state.isUploading,
    uploadProgress: state.uploadProgress,
    uploadError: state.uploadError,
    currentJobId: state.currentJobId,
    jobStatus: state.jobStatus,
  }));
};
