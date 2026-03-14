export default function WorksheetPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">
        Generate Worksheet
      </h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Download a printable worksheet containing all the characters we need to
        build your font. Fill it in with your natural handwriting, then head to
        the Upload step.
      </p>

      {/* Placeholder worksheet preview */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-10 flex flex-col items-center gap-6 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center text-3xl">
          📄
        </div>
        <div>
          <p className="text-gray-300 font-medium mb-1">
            Worksheet generation coming soon
          </p>
          <p className="text-gray-500 text-sm">
            The PDF will include all 96 printable ASCII characters laid out in
            clearly defined boxes.
          </p>
        </div>
        <button
          disabled
          className="inline-flex items-center justify-center rounded-lg bg-indigo-600 opacity-50 cursor-not-allowed text-white font-semibold px-6 py-2.5 text-sm"
        >
          Download Worksheet (PDF)
        </button>
      </div>

      {/* Next step hint */}
      <p className="mt-6 text-sm text-gray-500">
        Once you have filled in the worksheet, go to{" "}
        <a href="/upload" className="text-indigo-400 hover:underline">
          Upload
        </a>{" "}
        to submit your scan or photo.
      </p>
    </div>
  );
}
