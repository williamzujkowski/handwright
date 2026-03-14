export default function UploadPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">
        Upload Handwriting
      </h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Upload a photo or scan of your completed worksheet. For best results,
        use good lighting and keep the page flat.
      </p>

      {/* Drag-and-drop placeholder */}
      <div
        className="rounded-xl border-2 border-dashed border-gray-700 bg-gray-900 hover:border-indigo-600 transition-colors p-16 flex flex-col items-center gap-4 text-center cursor-pointer"
        role="button"
        aria-label="Upload worksheet image"
      >
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center text-3xl">
          📁
        </div>
        <div>
          <p className="text-gray-200 font-medium mb-1">
            Drag and drop your worksheet here
          </p>
          <p className="text-gray-500 text-sm">
            Or click to browse — PNG, JPG, TIFF, or PDF accepted
          </p>
        </div>
        <button
          disabled
          className="mt-2 inline-flex items-center justify-center rounded-lg bg-indigo-600 opacity-50 cursor-not-allowed text-white font-semibold px-6 py-2.5 text-sm"
        >
          Choose File
        </button>
      </div>

      <p className="mt-4 text-xs text-gray-600 text-center">
        Maximum file size: 20 MB. Images are processed server-side and not
        retained after your session.
      </p>

      {/* Next step hint */}
      <p className="mt-8 text-sm text-gray-500">
        After uploading, you will be taken to{" "}
        <a href="/review" className="text-indigo-400 hover:underline">
          Review
        </a>{" "}
        to inspect each extracted glyph before generating your font.
      </p>
    </div>
  );
}
