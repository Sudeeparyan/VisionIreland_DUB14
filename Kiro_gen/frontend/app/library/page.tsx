export default function LibraryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Library</h2>
        <p className="text-gray-600 mt-2">
          Browse and manage your generated audio narratives
        </p>
      </div>
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center py-12">
          <p className="text-gray-600">
            No audio narratives yet. Upload a comic to get started.
          </p>
        </div>
      </div>
    </div>
  );
}
