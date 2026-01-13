import type { Metadata } from 'next';
import Link from 'next/link';
import { NotificationSystem } from '@/components/NotificationSystem';
import './globals.css';

export const metadata: Metadata = {
  title: 'Comic Audio Narrator',
  description: 'Transform comics into accessible audio narratives',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          {/* Skip to main content link for screen readers */}
          <a 
            href="#main-content" 
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
          >
            Skip to main content
          </a>
          
          <nav className="bg-white shadow" role="navigation" aria-label="Main navigation">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <Link href="/" className="text-2xl font-bold text-gray-900 hover:text-blue-600 focus:text-blue-600">
                    Comic Audio Narrator
                  </Link>
                </div>
                <div className="flex items-center space-x-8">
                  <Link 
                    href="/upload" 
                    className="text-gray-700 hover:text-blue-600 focus:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                    aria-label="Upload a comic PDF"
                  >
                    Upload
                  </Link>
                  <Link 
                    href="/library" 
                    className="text-gray-700 hover:text-blue-600 focus:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                    aria-label="Browse audio library"
                  >
                    Library
                  </Link>
                  <Link 
                    href="/playback" 
                    className="text-gray-700 hover:text-blue-600 focus:text-blue-600 px-3 py-2 rounded-md text-sm font-medium"
                    aria-label="Audio playback controls"
                  >
                    Playback
                  </Link>
                </div>
              </div>
            </div>
          </nav>
          
          <main 
            id="main-content" 
            className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8"
            role="main"
          >
            {children}
          </main>
          
          <footer className="bg-white border-t mt-12" role="contentinfo">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-gray-500">
                Comic Audio Narrator - Making comics accessible through AI-powered audio narratives
              </p>
            </div>
          </footer>
          
          {/* Notification System */}
          <NotificationSystem />
        </div>
      </body>
    </html>
  );
}
