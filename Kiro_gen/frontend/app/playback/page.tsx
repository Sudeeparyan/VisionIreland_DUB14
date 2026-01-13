export default function PlaybackPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Playback</h2>
        <p className="text-gray-600 mt-2">
          Listen to your audio narratives with full controls
        </p>
      </div>
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center py-12">
          <p className="text-gray-600">
            Select an audio narrative from the library to play
          </p>
        </div>
      </div>
    </div>
  );
}
