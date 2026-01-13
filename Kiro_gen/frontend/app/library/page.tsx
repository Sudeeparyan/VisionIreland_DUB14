'use client';

import { useState, useEffect, useMemo } from 'react';
import { useAppStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';

interface AudioItem {
  id: string;
  title: string;
  characters: string[];
  scenes: string[];
  duration: number;
  uploadedAt: string;
}

export default function LibraryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'title' | 'uploadedAt' | 'duration'>('uploadedAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterBy, setFilterBy] = useState<'all' | 'characters' | 'scenes'>('all');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const {
    library,
    isLoadingLibrary,
    libraryError,
    setLibrary,
    setLoadingLibrary,
    setLibraryError,
    setCurrentAudio,
    removeFromLibrary,
  } = useAppStore();

  // Load library on component mount
  useEffect(() => {
    loadLibrary();
  }, []);

  const loadLibrary = async () => {
    setLoadingLibrary(true);
    setLibraryError(null);
    
    try {
      const response = await apiClient.getLibrary();
      setLibrary(response.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load library';
      setLibraryError(errorMessage);
    } finally {
      setLoadingLibrary(false);
    }
  };

  // Filter and sort library items
  const filteredAndSortedItems = useMemo(() => {
    let filtered = library;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      filtered = library.filter(item =>
        item.title.toLowerCase().includes(query) ||
        item.characters.some(char => char.toLowerCase().includes(query)) ||
        item.scenes.some(scene => scene.toLowerCase().includes(query))
      );
    }

    // Apply category filter
    if (filterBy !== 'all') {
      // This is a placeholder - in a real app, you might filter by specific criteria
      // For now, we'll just return all items
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      switch (sortBy) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'duration':
          aValue = a.duration;
          bValue = b.duration;
          break;
        case 'uploadedAt':
        default:
          aValue = new Date(a.uploadedAt).getTime();
          bValue = new Date(b.uploadedAt).getTime();
          break;
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return sorted;
  }, [library, searchQuery, sortBy, sortOrder, filterBy]);

  const handlePlayAudio = (audio: AudioItem) => {
    setCurrentAudio(audio);
    // Navigate to playback page
    window.location.href = '/playback';
  };

  const handleDownloadAudio = async (audioId: string, title: string) => {
    try {
      const audioBlob = await apiClient.getAudio(audioId);
      const url = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download audio');
    }
  };

  const handleDeleteAudio = async (audioId: string) => {
    if (!confirm('Are you sure you want to delete this audio narrative? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.deleteAudio(audioId);
      removeFromLibrary(audioId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete audio');
    }
  };

  const handleSelectItem = (audioId: string) => {
    setSelectedItems(prev =>
      prev.includes(audioId)
        ? prev.filter(id => id !== audioId)
        : [...prev, audioId]
    );
  };

  const handleSelectAll = () => {
    if (selectedItems.length === filteredAndSortedItems.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredAndSortedItems.map(item => item.id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedItems.length === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedItems.length} audio narrative(s)? This action cannot be undone.`)) {
      return;
    }

    try {
      await Promise.all(selectedItems.map(id => apiClient.deleteAudio(id)));
      selectedItems.forEach(id => removeFromLibrary(id));
      setSelectedItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete selected items');
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoadingLibrary) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-3xl font-bold text-gray-900">Library</h1>
          <p className="text-gray-600 mt-2">Loading your audio narratives...</p>
        </header>
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <div className="flex items-center justify-center space-x-3">
            <svg className="animate-spin h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            <span className="text-gray-600">Loading library...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Audio Library</h1>
        <p className="text-gray-600 mt-2">
          Browse and manage your generated audio narratives
        </p>
      </header>

      {libraryError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 mb-1">Library Error</h3>
              <p className="text-sm text-red-700">{libraryError}</p>
            </div>
            <button
              onClick={() => setLibraryError(null)}
              className="ml-3 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
              aria-label="Dismiss error message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800 mb-1">Error</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="ml-3 text-red-600 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded"
              aria-label="Dismiss error message"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {library.length > 0 ? (
        <>
          {/* Search and filters */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
              {/* Search */}
              <div className="flex-1 max-w-md">
                <label htmlFor="search" className="sr-only">Search audio narratives</label>
                <div className="relative">
                  <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    id="search"
                    type="text"
                    placeholder="Search by title, characters, or scenes..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Sort and filter controls */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label htmlFor="sort-by" className="text-sm font-medium text-gray-700">Sort by:</label>
                  <select
                    id="sort-by"
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'title' | 'uploadedAt' | 'duration')}
                    className="border border-gray-300 rounded px-3 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="uploadedAt">Upload Date</option>
                    <option value="title">Title</option>
                    <option value="duration">Duration</option>
                  </select>
                </div>

                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="p-1 text-gray-600 hover:text-blue-600 focus:text-blue-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {sortOrder === 'asc' ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                    )}
                  </svg>
                </button>

                <button
                  onClick={loadLibrary}
                  className="p-2 text-gray-600 hover:text-blue-600 focus:text-blue-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="Refresh library"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Bulk actions */}
            {selectedItems.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
                  </span>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedItems([])}
                      className="text-sm text-gray-600 hover:text-gray-800 focus:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded px-2 py-1"
                    >
                      Clear selection
                    </button>
                    <button
                      onClick={handleBulkDelete}
                      className="text-sm text-red-600 hover:text-red-800 focus:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 rounded px-2 py-1"
                    >
                      Delete selected
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results summary */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {filteredAndSortedItems.length} of {library.length} audio narrative{library.length !== 1 ? 's' : ''}
            </p>
            
            {filteredAndSortedItems.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800 focus:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
              >
                {selectedItems.length === filteredAndSortedItems.length ? 'Deselect all' : 'Select all'}
              </button>
            )}
          </div>

          {/* Audio library grid */}
          {filteredAndSortedItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAndSortedItems.map((audio) => (
                <div
                  key={audio.id}
                  className={`bg-white rounded-lg shadow-sm border transition-all duration-200 ${
                    selectedItems.includes(audio.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:shadow-md'
                  }`}
                >
                  <div className="p-6">
                    {/* Selection checkbox */}
                    <div className="flex items-start justify-between mb-4">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(audio.id)}
                        onChange={() => handleSelectItem(audio.id)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        aria-label={`Select ${audio.title}`}
                      />
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                          {formatDuration(audio.duration)}
                        </span>
                      </div>
                    </div>

                    {/* Title */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                      {audio.title}
                    </h3>

                    {/* Metadata */}
                    <div className="space-y-3 mb-4">
                      <div>
                        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                          Characters ({audio.characters.length})
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {audio.characters.slice(0, 3).map((character, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                            >
                              {character}
                            </span>
                          ))}
                          {audio.characters.length > 3 && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                              +{audio.characters.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                          Scenes ({audio.scenes.length})
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {audio.scenes.slice(0, 2).map((scene, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                            >
                              {scene}
                            </span>
                          ))}
                          {audio.scenes.length > 2 && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                              +{audio.scenes.length - 2} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Upload date */}
                    <p className="text-xs text-gray-500 mb-4">
                      Uploaded {formatDate(audio.uploadedAt)}
                    </p>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handlePlayAudio(audio)}
                        className="flex-1 bg-blue-600 text-white text-sm font-medium py-2 px-3 rounded-md hover:bg-blue-700 focus:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                      >
                        Play
                      </button>
                      <button
                        onClick={() => handleDownloadAudio(audio.id, audio.title)}
                        className="p-2 text-gray-600 hover:text-blue-600 focus:text-blue-600 border border-gray-300 rounded-md hover:border-blue-300 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        aria-label={`Download ${audio.title}`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteAudio(audio.id)}
                        className="p-2 text-gray-600 hover:text-red-600 focus:text-red-600 border border-gray-300 rounded-md hover:border-red-300 focus:border-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                        aria-label={`Delete ${audio.title}`}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search terms or filters.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setFilterBy('all');
                }}
                className="text-blue-600 hover:text-blue-800 focus:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
              >
                Clear filters
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Audio Narratives Yet</h3>
          <p className="text-gray-600 mb-4">
            Upload your first comic to generate an accessible audio narrative.
          </p>
          <a
            href="/upload"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload Comic
          </a>
        </div>
      )}
    </div>
  );
}
