export default function ReviewPage() {
  // Placeholder glyph characters for layout preview
  const placeholderGlyphs = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".split(
    ""
  );

  return (
    <div className="max-w-5xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Each character extracted from your worksheet is shown below. Click any
        glyph to inspect or re-crop it before generating your font.
      </p>

      {/* Status bar placeholder */}
      <div className="flex items-center justify-between mb-6 py-3 px-4 rounded-lg border border-gray-800 bg-gray-900 text-sm">
        <span className="text-gray-400">
          <span className="text-white font-medium">0</span> of{" "}
          <span className="text-white font-medium">{placeholderGlyphs.length}</span> glyphs
          extracted
        </span>
        <span className="text-gray-600 italic">Upload a worksheet to begin</span>
      </div>

      {/* Glyph grid placeholder */}
      <div className="grid grid-cols-8 sm:grid-cols-10 md:grid-cols-12 gap-2">
        {placeholderGlyphs.map((char) => (
          <div
            key={char}
            className="aspect-square rounded-lg border border-gray-800 bg-gray-900 flex items-center justify-center text-gray-700 text-lg font-mono select-none"
            title={`Glyph: ${char}`}
          >
            {char}
          </div>
        ))}
      </div>

      {/* Action bar */}
      <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-end">
        <a
          href="/upload"
          className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-5 py-2.5 text-sm transition-colors"
        >
          Back to Upload
        </a>
        <button
          disabled
          className="inline-flex items-center justify-center rounded-lg bg-indigo-600 opacity-50 cursor-not-allowed text-white font-semibold px-5 py-2.5 text-sm"
        >
          Proceed to Generate
        </button>
      </div>
    </div>
  );
}
