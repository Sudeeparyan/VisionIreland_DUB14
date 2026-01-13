'use client';

import { useState, useEffect } from 'react';
import { AudioPlayer } from '@/components/AudioPlayer';
import { useAppStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';

export default function PlaybackPage() {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { currentAudio, library } = useAppStore();

  // Load audio when currentAudio changes
  useEffect(() => {
    if (currentAudio) {
      loadAudio(currentAudio.id);
    }
  }, [currentAudio]);

  const loadAudio = async (audioId: string) => {
    setIsLoadingAudio(true);
    setError(null);
    
    try {
      const audioBlob = await apiClient.getAudio(audioId);
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audio');
    } finally {
      setIsLoadingAudio(false);
    }
  };

  const handleAudioSelect = async (audioId: string) => {
    const audio = library.find(item => item.id === audioId);
    if (audio) {
      useAppStore.getState().setCurrentAudio(audio);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Audio Playback</h1>
        <p className="text-gray-600 mt-2">
          Listen to your generated audio narratives with full playback controls
        </p>
      </header>

      {/* Audio selection */}
      {library.length > 0 && (
        <section className="bg-white rounded-lg shadow-sm border p-6" aria-labelledby="audio-selection-heading">
          <h2 id="audio-selection-heading" className="text-lg font-semibold text-gray-900 mb-4">
            Select Audio Narrative
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {library.map((audio) => (
              <button
                key={audio.id}
                onClick={() => handleAudioSelect(audio.id)}
                className={`p-4 text-left border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  currentAudio?.id === audio.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                aria-pressed={currentAudio?.id === audio.id}
              >
                <h3 className="font-medium text-gray-900 mb-2">{audio.title}</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Duration: {Math.floor(audio.duration / 60)}:{(audio.duration % 60).toString().padStart(2, '0')}</p>
                  <p>Characters: {audio.characters.length}</p>
                  <p>Uploaded: {new Date(audio.uploadedAt).toLocaleDateString()}</p>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Audio player */}
      <section aria-labelledby="player-heading">
        <h2 id="player-heading" className="sr-only">Audio Player</h2>
        
        {isLoadingAudio && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <div className="flex items-center justify-center space-x-3">
              <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
              </svg>
              <span className="text-gray-600">Loading audio...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800 mb-1">Audio Loading Error</h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {currentAudio && audioUrl && !isLoadingAudio && (
          <div className="space-y-4">
            <AudioPlayer
              audioUrl={audioUrl}
              title={currentAudio.title}
              duration={currentAudio.duration}
              onPlay={() => console.log('Audio started playing')}
              onPause={() => console.log('Audio paused')}
              onEnded={() => console.log('Audio ended')}
            />
            
            {/* Audio metadata */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Audio Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Characters</h4>
                  <div className="flex flex-wrap gap-2">
                    {currentAudio.characters.map((character, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                      >
                        {character}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Scenes</h4>
                  <div className="flex flex-wrap gap-2">
                    {currentAudio.scenes.map((scene, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full"
                      >
                        {scene}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Uploaded:</span> {new Date(currentAudio.uploadedAt).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Duration:</span> {Math.floor(currentAudio.duration / 60)}:{(currentAudio.duration % 60).toString().padStart(2, '0')}
                </p>
              </div>
            </div>
          </div>
        )}

        {!currentAudio && library.length > 0 && !isLoadingAudio && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Select an Audio Narrative</h3>
            <p className="text-gray-600">
              Choose an audio narrative from the list above to start listening.
            </p>
          </div>
        )}

        {library.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Audio Narratives Available</h3>
            <p className="text-gray-600 mb-4">
              Upload a comic to generate your first audio narrative.
            </p>
            <a
              href="/upload"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Upload Comic
            </a>
          </div>
        )}
      </section>

      {/* Accessibility information */}
      <section className="bg-blue-50 rounded-lg p-6" aria-labelledby="accessibility-info-heading">
        <h2 id="accessibility-info-heading" className="text-lg font-semibold text-blue-900 mb-3">
          Accessibility Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h3 className="font-medium mb-2">Keyboard Controls</h3>
            <ul className="space-y-1">
              <li>• Spacebar: Play/Pause</li>
              <li>• Left/Right arrows: Skip 10 seconds</li>
              <li>• Up/Down arrows: Volume control</li>
              <li>• M: Mute/Unmute</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium mb-2">Player Features</h3>
            <ul className="space-y-1">
              <li>• Variable playback speed (0.5x - 2x)</li>
              <li>• Precise seeking and time display</li>
              <li>• Screen reader compatible</li>
              <li>• High contrast focus indicators</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
