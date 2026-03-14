export default function Loading() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-gray-800 rounded w-1/3" />
        <div className="h-4 bg-gray-800 rounded w-2/3" />
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-10">
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gray-800" />
            <div className="h-4 bg-gray-800 rounded w-1/2" />
            <div className="h-3 bg-gray-800 rounded w-3/4" />
            <div className="h-10 bg-gray-800 rounded w-48 mt-4" />
          </div>
        </div>
      </div>
    </div>
  );
}
