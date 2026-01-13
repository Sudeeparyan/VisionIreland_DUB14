import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to Comic Audio Narrator
        </h2>
        <p className="text-lg text-gray-600 mb-6">
          Transform your comic books into accessible audio narratives with AI-powered analysis and professional voice synthesis.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            href="/upload"
            className="block p-6 bg-blue-50 rounded-lg hover:bg-blue-100 transition"
          >
            <h3 className="text-xl font-semibold text-blue-900 mb-2">
              Upload Comic
            </h3>
            <p className="text-blue-700">
              Upload a PDF comic to generate audio narratives
            </p>
          </Link>
          <Link
            href="/library"
            className="block p-6 bg-green-50 rounded-lg hover:bg-green-100 transition"
          >
            <h3 className="text-xl font-semibold text-green-900 mb-2">
              Library
            </h3>
            <p className="text-green-700">
              Browse and manage your generated audio narratives
            </p>
          </Link>
          <Link
            href="/playback"
            className="block p-6 bg-purple-50 rounded-lg hover:bg-purple-100 transition"
          >
            <h3 className="text-xl font-semibold text-purple-900 mb-2">
              Playback
            </h3>
            <p className="text-purple-700">
              Listen to your audio narratives with full controls
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
