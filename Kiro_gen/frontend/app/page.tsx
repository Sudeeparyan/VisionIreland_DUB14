import Link from 'next/link';
import TeamSection from '../components/TeamSection';

export default function Home() {
  return (
    <div className="space-y-8">
      <header className="bg-white rounded-lg shadow p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to Comic Audio Narrator
        </h1>
        <p className="text-lg text-gray-600 mb-6">
          Transform your comic books into accessible audio narratives with AI-powered analysis and professional voice synthesis.
        </p>
        <p className="text-base text-gray-600">
          Our service uses advanced AI to analyze comic panels, identify characters and scenes, and generate engaging audio descriptions with character-appropriate voices, making comics accessible to blind and visually impaired readers.
        </p>
      </header>

      <section aria-labelledby="features-heading">
        <h2 id="features-heading" className="sr-only">Main Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            href="/upload"
            className="block p-6 bg-blue-50 rounded-lg hover:bg-blue-100 focus:bg-blue-100 transition-colors border-2 border-transparent hover:border-blue-200 focus:border-blue-500"
            aria-describedby="upload-description"
          >
            <div className="flex items-center mb-3">
              <svg 
                className="w-6 h-6 text-blue-600 mr-2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <h3 className="text-xl font-semibold text-blue-900">
                Upload Comic
              </h3>
            </div>
            <p id="upload-description" className="text-blue-700">
              Upload a PDF comic to generate audio narratives with AI-powered character voices and scene descriptions
            </p>
          </Link>

          <Link
            href="/library"
            className="block p-6 bg-green-50 rounded-lg hover:bg-green-100 focus:bg-green-100 transition-colors border-2 border-transparent hover:border-green-200 focus:border-green-500"
            aria-describedby="library-description"
          >
            <div className="flex items-center mb-3">
              <svg 
                className="w-6 h-6 text-green-600 mr-2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="text-xl font-semibold text-green-900">
                Library
              </h3>
            </div>
            <p id="library-description" className="text-green-700">
              Browse and manage your generated audio narratives with search and filtering capabilities
            </p>
          </Link>

          <Link
            href="/playback"
            className="block p-6 bg-purple-50 rounded-lg hover:bg-purple-100 focus:bg-purple-100 transition-colors border-2 border-transparent hover:border-purple-200 focus:border-purple-500"
            aria-describedby="playback-description"
          >
            <div className="flex items-center mb-3">
              <svg 
                className="w-6 h-6 text-purple-600 mr-2" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-9-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-xl font-semibold text-purple-900">
                Playback
              </h3>
            </div>
            <p id="playback-description" className="text-purple-700">
              Listen to your audio narratives with accessible playback controls and volume adjustment
            </p>
          </Link>
        </div>
      </section>

      <section className="bg-white rounded-lg shadow p-8" aria-labelledby="accessibility-heading">
        <h2 id="accessibility-heading" className="text-2xl font-bold text-gray-900 mb-4">
          Accessibility Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">WCAG 2.2 Compliant</h3>
            <p className="text-gray-600">
              Full keyboard navigation, screen reader support, and proper color contrast ratios for all users.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Professional Audio Descriptions</h3>
            <p className="text-gray-600">
              Following industry standards for audio descriptions used in film and television.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Character Voice Consistency</h3>
            <p className="text-gray-600">
              AI-powered character identification ensures consistent voices throughout the story.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Responsive Design</h3>
            <p className="text-gray-600">
              Works seamlessly across all devices with text resizing support up to 200%.
            </p>
          </div>
        </div>
      </section>

      <TeamSection />
    </div>
  );
}
