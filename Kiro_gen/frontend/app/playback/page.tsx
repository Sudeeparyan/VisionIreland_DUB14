"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useAppStore } from "@/lib/store";
import { AudioPlayer } from "@/components/AudioPlayer";

export default function PlaybackPage() {
  const { currentAudio, library, setCurrentAudio } = useAppStore();

  // If no audio is selected but we have library items, show a selection prompt
  const hasLibraryItems = library.length > 0;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Audio Playback</h1>
        <p className="text-gray-600 mt-2">
          Listen to your comic audio narratives with accessible playback
          controls
        </p>
      </header>

      {/* Main player section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <AudioPlayer />
      </div>

      {/* No audio selected - show options */}
      {!currentAudio && (
        <div className="bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">
            Getting Started
          </h2>
          <p className="text-blue-800 mb-4">
            Select an audio narrative from your library to start listening.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/library"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
              Browse Library
            </Link>
            {!hasLibraryItems && (
              <Link
                href="/upload"
                className="inline-flex items-center px-4 py-2 bg-white text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                Upload Comic
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Current audio details */}
      {currentAudio && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Now Playing
          </h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Title</h3>
              <p className="text-lg text-gray-900">{currentAudio.title}</p>
            </div>

            {currentAudio.characters && currentAudio.characters.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Characters
                </h3>
                <div className="flex flex-wrap gap-2">
                  {currentAudio.characters.map((character) => (
                    <span
                      key={character}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
                    >
                      {character}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {currentAudio.scenes && currentAudio.scenes.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Scenes
                </h3>
                <div className="flex flex-wrap gap-2">
                  {currentAudio.scenes.map((scene) => (
                    <span
                      key={scene}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800"
                    >
                      {scene}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {currentAudio.metadata && (
              <div className="pt-4 border-t">
                <h3 className="text-sm font-medium text-gray-500 mb-2">
                  Details
                </h3>
                <dl className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-gray-500">Original File</dt>
                    <dd className="text-gray-900">
                      {currentAudio.metadata.originalFilename}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Processing Time</dt>
                    <dd className="text-gray-900">
                      {currentAudio.metadata.processingTime}s
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">AI Model</dt>
                    <dd className="text-gray-900">
                      {currentAudio.metadata.modelUsed}
                    </dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Playback tips */}
      <section
        className="bg-white rounded-lg shadow-sm border p-6"
        aria-labelledby="tips-heading"
      >
        <h2
          id="tips-heading"
          className="text-lg font-semibold text-gray-900 mb-4"
        >
          Keyboard Shortcuts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Play/Pause</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                Space
              </kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Skip forward 5s</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                Right Arrow
              </kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Skip forward 10s</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                Shift + Right
              </kbd>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Skip back 5s</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                Left Arrow
              </kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Skip back 10s</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                Shift + Left
              </kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Mute/Unmute</span>
              <kbd className="px-2 py-1 bg-gray-100 rounded text-gray-700">
                M
              </kbd>
            </div>
          </div>
        </div>
      </section>

      {/* Recent items from library */}
      {hasLibraryItems && (
        <section
          className="bg-white rounded-lg shadow-sm border p-6"
          aria-labelledby="recent-heading"
        >
          <div className="flex items-center justify-between mb-4">
            <h2
              id="recent-heading"
              className="text-lg font-semibold text-gray-900"
            >
              Quick Play
            </h2>
            <Link
              href="/library"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {library.slice(0, 3).map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentAudio(item)}
                className={`text-left p-4 rounded-lg border transition-colors ${
                  currentAudio?.id === item.id
                    ? "bg-blue-50 border-blue-500"
                    : "hover:bg-gray-50 border-gray-200"
                }`}
              >
                <h3 className="font-medium text-gray-900 line-clamp-1">
                  {item.title}
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  {Math.floor(item.duration / 60)}:
                  {(item.duration % 60).toString().padStart(2, "0")}
                </p>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
