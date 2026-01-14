"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useAppStore, AudioItem } from "@/lib/store";
import { apiClient } from "@/lib/api-client";
import { LibraryGridSkeleton, InlineLoading } from "@/components/LoadingStates";

export default function LibraryPage() {
  const {
    library,
    isLoadingLibrary,
    libraryError,
    searchQuery,
    searchResults,
    isSearching,
    setLibrary,
    setLoadingLibrary,
    setLibraryError,
    setSearchQuery,
    setSearchResults,
    setSearching,
    removeFromLibrary,
    setCurrentAudio,
  } = useAppStore();

  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"date" | "title" | "duration">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Load library on mount
  useEffect(() => {
    const loadLibrary = async () => {
      setLoadingLibrary(true);
      setLibraryError(null);
      try {
        const response = await apiClient.getLibrary({ page: 1, limit: 50 });
        setLibrary(response.items);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load library";
        setLibraryError(message);
      } finally {
        setLoadingLibrary(false);
      }
    };

    loadLibrary();
  }, [setLibrary, setLoadingLibrary, setLibraryError]);

  // Search handler with debounce
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setSearching(true);
      try {
        const response = await apiClient.searchLibrary(searchQuery);
        setSearchResults(response.items);
      } catch (err) {
        console.error("Search failed:", err);
        // Fall back to client-side search
        const filtered = library.filter(
          (item) =>
            item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.characters?.some((c) =>
              c.toLowerCase().includes(searchQuery.toLowerCase())
            ) ||
            item.scenes?.some((s) =>
              s.toLowerCase().includes(searchQuery.toLowerCase())
            )
        );
        setSearchResults(filtered);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, library, setSearchResults, setSearching]);

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await apiClient.deleteFromLibrary(id);
        removeFromLibrary(id);
        setDeleteConfirm(null);
      } catch (err) {
        console.error("Delete failed:", err);
        // Still remove from local state for demo purposes
        removeFromLibrary(id);
        setDeleteConfirm(null);
      }
    },
    [removeFromLibrary]
  );

  const handlePlay = useCallback(
    (item: AudioItem) => {
      setCurrentAudio(item);
      // Navigate to playback page
      window.location.href = "/playback";
    },
    [setCurrentAudio]
  );

  // Sort items
  const sortItems = useCallback(
    (items: AudioItem[]) => {
      return [...items].sort((a, b) => {
        let comparison = 0;
        switch (sortBy) {
          case "date":
            comparison =
              new Date(a.uploadedAt).getTime() -
              new Date(b.uploadedAt).getTime();
            break;
          case "title":
            comparison = a.title.localeCompare(b.title);
            break;
          case "duration":
            comparison = a.duration - b.duration;
            break;
        }
        return sortOrder === "asc" ? comparison : -comparison;
      });
    },
    [sortBy, sortOrder]
  );

  const displayItems = sortItems(searchQuery.trim() ? searchResults : library);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Audio Library</h1>
        <p className="text-gray-600 mt-2">
          Browse and manage your generated audio narratives
        </p>
      </header>

      {/* Search and filters */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search input */}
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">
              Search library
            </label>
            <div className="relative">
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                id="search"
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, characters, or scenes..."
                className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {isSearching && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <InlineLoading message="" />
                </div>
              )}
            </div>
          </div>

          {/* Sort controls */}
          <div className="flex gap-2">
            <div>
              <label htmlFor="sortBy" className="sr-only">
                Sort by
              </label>
              <select
                id="sortBy"
                value={sortBy}
                onChange={(e) =>
                  setSortBy(e.target.value as "date" | "title" | "duration")
                }
                className="px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="date">Sort by Date</option>
                <option value="title">Sort by Title</option>
                <option value="duration">Sort by Duration</option>
              </select>
            </div>
            <button
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              className="px-3 py-2 border rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label={`Sort ${
                sortOrder === "asc" ? "descending" : "ascending"
              }`}
            >
              {sortOrder === "asc" ? (
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
                    d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
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
                    d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Error state */}
      {libraryError && (
        <div
          className="bg-red-50 border border-red-200 rounded-lg p-4"
          role="alert"
        >
          <div className="flex items-center">
            <svg
              className="w-5 h-5 text-red-600 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-red-800">{libraryError}</span>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoadingLibrary && <LibraryGridSkeleton count={6} />}

      {/* Empty state */}
      {!isLoadingLibrary && displayItems.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          {searchQuery.trim() ? (
            <>
              <svg
                className="w-16 h-16 text-gray-300 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No results found
              </h3>
              <p className="text-gray-600 mb-4">
                No items match your search for "{searchQuery}"
              </p>
              <button
                onClick={() => setSearchQuery("")}
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear search
              </button>
            </>
          ) : (
            <>
              <svg
                className="w-16 h-16 text-gray-300 mx-auto mb-4"
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Your library is empty
              </h3>
              <p className="text-gray-600 mb-4">
                Upload a comic to generate your first audio narrative
              </p>
              <Link
                href="/upload"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Upload Comic
              </Link>
            </>
          )}
        </div>
      )}

      {/* Library grid */}
      {!isLoadingLibrary && displayItems.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayItems.map((item) => (
            <article
              key={item.id}
              className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
                  {item.title}
                </h3>
                <span className="text-sm text-gray-500 whitespace-nowrap ml-2">
                  {formatDuration(item.duration)}
                </span>
              </div>

              <p className="text-sm text-gray-600 mb-3">
                Uploaded {formatDate(item.uploadedAt)}
              </p>

              {/* Characters */}
              {item.characters && item.characters.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {item.characters.slice(0, 3).map((character) => (
                    <span
                      key={character}
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {character}
                    </span>
                  ))}
                  {item.characters.length > 3 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      +{item.characters.length - 3} more
                    </span>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t">
                <button
                  onClick={() => handlePlay(item)}
                  className="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  Play
                </button>

                {deleteConfirm === item.id ? (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-red-600">Delete?</span>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="px-2 py-1 text-sm text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      Yes
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(null)}
                      className="px-2 py-1 text-sm text-gray-600 bg-gray-100 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                    >
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(item.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 rounded"
                    aria-label={`Delete ${item.title}`}
                  >
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
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Results count */}
      {!isLoadingLibrary && displayItems.length > 0 && (
        <p className="text-sm text-gray-500 text-center">
          Showing {displayItems.length} item
          {displayItems.length !== 1 ? "s" : ""}
          {searchQuery.trim() && ` matching "${searchQuery}"`}
        </p>
      )}
    </div>
  );
}
