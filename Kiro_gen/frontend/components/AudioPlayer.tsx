"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAppStore, AudioItem } from "@/lib/store";

interface AudioPlayerProps {
  audioItem?: AudioItem;
  onEnded?: () => void;
}

export function AudioPlayer({ audioItem, onEnded }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  const {
    currentAudio,
    isPlaying,
    currentTime,
    volume,
    isMuted,
    playbackRate,
    setCurrentAudio,
    setPlaying,
    setCurrentTime,
    setVolume,
    setMuted,
    setPlaybackRate,
  } = useAppStore();

  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audio = audioItem || currentAudio;

  // Reset error state when audio source changes
  useEffect(() => {
    setError(null);
  }, [audio?.id]);

  // Sync audio element with store state - handle pause from external sources
  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    // Only handle pause - play is handled directly in togglePlay for user gesture context
    if (!isPlaying && !audioElement.paused) {
      audioElement.pause();
    }
  }, [isPlaying]);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;
    audioElement.volume = isMuted ? 0 : volume;
  }, [volume, isMuted]);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;
    audioElement.playbackRate = playbackRate;
  }, [playbackRate]);

  const handleTimeUpdate = useCallback(() => {
    const audioElement = audioRef.current;
    if (audioElement) {
      setCurrentTime(audioElement.currentTime);
    }
  }, [setCurrentTime]);

  const handleLoadedMetadata = useCallback(() => {
    const audioElement = audioRef.current;
    if (audioElement) {
      setDuration(audioElement.duration);
      setIsLoading(false);
    }
  }, []);

  const handleEnded = useCallback(() => {
    setPlaying(false);
    setCurrentTime(0);
    onEnded?.();
  }, [setPlaying, setCurrentTime, onEnded]);

  const handleError = useCallback((e: React.SyntheticEvent<HTMLAudioElement, Event>) => {
    const audioElement = e.currentTarget;
    const errorCode = audioElement.error?.code;
    const errorMessage = audioElement.error?.message;
    
    console.error("Audio error:", { 
      code: errorCode, 
      message: errorMessage,
      src: audioElement.src,
      networkState: audioElement.networkState,
      readyState: audioElement.readyState
    });
    
    let userMessage = "Failed to load audio. ";
    if (errorCode === 1) {
      userMessage += "The audio loading was aborted.";
    } else if (errorCode === 2) {
      userMessage += "A network error occurred.";
    } else if (errorCode === 3) {
      userMessage += "The audio format is not supported.";
    } else if (errorCode === 4) {
      userMessage += "The audio source is not available.";
    } else {
      userMessage += "Please check your connection and try again.";
    }
    
    setError(userMessage);
    setIsLoading(false);
    setPlaying(false);
  }, [setPlaying]);

  const handleLoadStart = useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const togglePlay = useCallback(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;
    
    if (error) {
      setError(null);
      audioElement.load();
    }
    
    if (isPlaying) {
      audioElement.pause();
      setPlaying(false);
    } else {
      // Play directly in the user gesture context to avoid autoplay blocking
      audioElement.play()
        .then(() => {
          setPlaying(true);
        })
        .catch((err: DOMException) => {
          console.error("Playback failed:", {
            name: err.name,
            message: err.message,
            src: audioElement.src,
            readyState: audioElement.readyState
          });
          setPlaying(false);
          
          if (err.name === 'NotAllowedError') {
            setError("Playback blocked by browser. Please try again.");
          } else if (err.name === 'NotSupportedError') {
            setError("Audio format not supported.");
          } else {
            setError(`Playback failed: ${err.message || 'Please try again.'}`);
          }
        });
    }
  }, [isPlaying, setPlaying, error]);

  const handleSeek = useCallback(
    (
      e: React.MouseEvent<HTMLDivElement> | React.KeyboardEvent<HTMLDivElement>
    ) => {
      const progressBar = progressRef.current;
      const audioElement = audioRef.current;
      if (!progressBar || !audioElement || !duration) return;

      let clientX: number;
      if ("clientX" in e) {
        clientX = e.clientX;
      } else if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        const step = e.shiftKey ? 10 : 5;
        const newTime =
          e.key === "ArrowRight"
            ? Math.min(currentTime + step, duration)
            : Math.max(currentTime - step, 0);
        audioElement.currentTime = newTime;
        setCurrentTime(newTime);
        return;
      } else {
        return;
      }

      const rect = progressBar.getBoundingClientRect();
      const percent = (clientX - rect.left) / rect.width;
      const newTime = percent * duration;
      audioElement.currentTime = newTime;
      setCurrentTime(newTime);
    },
    [duration, currentTime, setCurrentTime]
  );

  const handleVolumeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newVolume = parseFloat(e.target.value);
      setVolume(newVolume);
      if (newVolume > 0 && isMuted) {
        setMuted(false);
      }
    },
    [setVolume, setMuted, isMuted]
  );

  const toggleMute = useCallback(() => {
    setMuted(!isMuted);
  }, [isMuted, setMuted]);

  const handlePlaybackRateChange = useCallback(
    (rate: number) => {
      setPlaybackRate(rate);
    },
    [setPlaybackRate]
  );

  const skipBackward = useCallback(() => {
    const audioElement = audioRef.current;
    if (audioElement) {
      audioElement.currentTime = Math.max(0, audioElement.currentTime - 10);
    }
  }, []);

  const skipForward = useCallback(() => {
    const audioElement = audioRef.current;
    if (audioElement && duration) {
      audioElement.currentTime = Math.min(
        duration,
        audioElement.currentTime + 10
      );
    }
  }, [duration]);

  const formatTime = (time: number): string => {
    if (isNaN(time) || !isFinite(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  if (!audio) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6 text-center text-gray-500">
        <p>No audio selected. Choose an item from your library to play.</p>
      </div>
    );
  }

  // Construct proper audio URL - handle relative API paths
  const getAudioSrc = () => {
    if (audio.audioUrl) {
      let result: string;
      // If it's a relative path starting with /api, prepend the API base URL
      if (audio.audioUrl.startsWith('/api/')) {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
        // Remove /api from the base URL since audioUrl already includes it
        const baseUrl = apiBase.replace(/\/api\/?$/, '');
        result = `${baseUrl}${audio.audioUrl}`;
      }
      // If it's already a full URL, use it directly
      else if (audio.audioUrl.startsWith('http://') || audio.audioUrl.startsWith('https://')) {
        result = audio.audioUrl;
      }
      // Otherwise, treat it as a relative path to the API
      else {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
        const baseUrl = apiBase.replace(/\/api\/?$/, '');
        result = `${baseUrl}/api/audio/${audio.audioUrl}`;
      }
      console.log('Audio URL constructed:', { original: audio.audioUrl, result });
      return result;
    }
    console.warn('No audioUrl found for audio:', audio?.id, audio?.title);
    return '';
  };

  const audioSrc = getAudioSrc();

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-4">
      {/* Audio element */}
      <audio
        ref={audioRef}
        src={audioSrc}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={handleError}
        onLoadStart={handleLoadStart}
        preload="metadata"
      />

      {/* Title */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-900">{audio.title}</h3>
        {audio.characters && audio.characters.length > 0 && (
          <p className="text-sm text-gray-600">
            Characters: {audio.characters.join(", ")}
          </p>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div
          className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* Progress bar */}
      <div className="space-y-2">
        <div
          ref={progressRef}
          onClick={handleSeek}
          onKeyDown={handleSeek}
          tabIndex={0}
          role="slider"
          aria-label="Audio progress"
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={currentTime}
          aria-valuetext={`${formatTime(currentTime)} of ${formatTime(
            duration
          )}`}
          className="w-full h-2 bg-gray-200 rounded-full cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <div
            className="h-2 bg-blue-600 rounded-full transition-all duration-100"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex justify-between text-sm text-gray-500">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      {/* Main controls */}
      <div className="flex items-center justify-center gap-4">
        {/* Skip backward */}
        <button
          onClick={skipBackward}
          disabled={isLoading}
          className="p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full disabled:opacity-50"
          aria-label="Skip backward 10 seconds"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z"
            />
          </svg>
        </button>

        {/* Play/Pause */}
        <button
          onClick={togglePlay}
          disabled={isLoading && !error}
          className="p-4 bg-blue-600 text-white rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isLoading && !error ? (
            <svg
              className="w-8 h-8 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : isPlaying ? (
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Skip forward */}
        <button
          onClick={skipForward}
          disabled={isLoading}
          className="p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full disabled:opacity-50"
          aria-label="Skip forward 10 seconds"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z"
            />
          </svg>
        </button>
      </div>

      {/* Secondary controls */}
      <div className="flex items-center justify-between pt-2 border-t">
        {/* Volume control */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className="p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted || volume === 0 ? (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                  clipRule="evenodd"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
              </svg>
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            aria-label="Volume"
          />
        </div>

        {/* Playback speed */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Speed:</span>
          <select
            value={playbackRate}
            onChange={(e) =>
              handlePlaybackRateChange(parseFloat(e.target.value))
            }
            className="text-sm border rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Playback speed"
          >
            <option value={0.5}>0.5x</option>
            <option value={0.75}>0.75x</option>
            <option value={1}>1x</option>
            <option value={1.25}>1.25x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>
        </div>
      </div>
    </div>
  );
}
