"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { getGlyphs, type GlyphData } from "@/lib/api";
import { ProgressStepper } from "@/components/progress-stepper";

/** Extract the display character from a glyph label like "a_1" → "a", "cell_0" → "?" */
function getDisplayChar(label: string): string {
  // Labels are formatted as "char_variant" (e.g., "a_1", "B_2", "!_1")
  // or "cell_N" for fallback sequential labels
  if (label.startsWith("cell_")) return "?";
  const underscoreIdx = label.lastIndexOf("_");
  if (underscoreIdx > 0) return label.slice(0, underscoreIdx);
  return label;
}

function ReviewContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const session = searchParams.get("session");

  const [glyphs, setGlyphs] = useState<GlyphData[]>([]);
  const [loading, setLoading] = useState(!!session);
  const [error, setError] = useState<string | null>(
    session ? null : "No session parameter provided. Please upload a worksheet first."
  );
  const [extractionDetail, setExtractionDetail] = useState<string | null>(null);
  const [rejected, setRejected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!session) return;

    getGlyphs(session)
      .then((data) => {
        setGlyphs(data.glyphs);
        if (data.glyph_count === 0 && data.detail) {
          setExtractionDetail(data.detail);
        }
        setLoading(false);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Failed to fetch glyphs";
        setError(message);
        setLoading(false);
      });
  }, [session]);

  const toggleRejected = (label: string) => {
    setRejected((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const approvedCount = glyphs.length - rejected.size;

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16">
        <ProgressStepper />
        <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
        <div className="py-12">
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-3">
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
                <div className="w-full aspect-square bg-gray-800 animate-pulse" />
                <div className="h-4 mx-2 my-1 bg-gray-800 rounded animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16">
        <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
        <div className="rounded-lg border border-red-800 bg-red-950 px-4 py-3 text-red-300 mt-6">
          {error}
        </div>
        <div className="mt-6">
          <a
            href="/upload"
            className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-5 py-2.5 text-sm transition-colors"
          >
            Back to Upload
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-16">
      <ProgressStepper />
      <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Each character extracted from your worksheet is shown below. Click any
        glyph to reject it. Rejected glyphs will not be included in your font.
      </p>

      {/* Status bar */}
      <div className="sticky top-14 z-40 flex items-center justify-between mb-6 py-3 px-4 rounded-lg border border-gray-800 bg-gray-900/95 backdrop-blur-sm text-sm">
        <span className="text-gray-400">
          <span className="text-white font-medium">{approvedCount}</span> of{" "}
          <span className="text-white font-medium">{glyphs.length}</span> glyphs
          approved
        </span>
        {rejected.size > 0 && (
          <button
            onClick={() => setRejected(new Set())}
            className="text-indigo-400 hover:text-indigo-300 text-sm transition-colors"
          >
            Reset selections
          </button>
        )}
      </div>

      {/* Glyph grid */}
      {glyphs.length === 0 ? (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-8">
          <p className="text-gray-300 text-lg font-semibold mb-2 text-center">No glyphs extracted</p>

          {extractionDetail && (
            <div className="mb-4 p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-amber-300 text-sm">
              {extractionDetail}
            </div>
          )}

          <div className="mb-6 text-sm text-gray-400 space-y-3">
            <p className="font-medium text-gray-300">Troubleshooting checklist:</p>
            <ul className="list-disc list-inside space-y-1.5 text-gray-400">
              <li>Did you <strong className="text-gray-300">print</strong> the worksheet, <strong className="text-gray-300">fill it in with dark ink</strong>, and then photograph or scan it?</li>
              <li>Do not upload the blank PDF itself — upload a <strong className="text-gray-300">photo of the filled pages</strong></li>
              <li>Use <strong className="text-gray-300">PNG or JPG</strong> format (not PDF)</li>
              <li>Ensure the image is <strong className="text-gray-300">well-lit, flat, and shows the full page</strong> including corner markers</li>
              <li>Use a <strong className="text-gray-300">dark pen</strong> (ballpoint or felt-tip) — pencil may be too faint</li>
            </ul>
          </div>

          <div className="text-center">
            <a
              href="/upload"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 text-sm transition-colors"
            >
              Re-upload Worksheet
            </a>
          </div>
        </div>
      ) : (
      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-3" role="group" aria-label="Extracted glyphs">
        {glyphs.map((glyph) => {
          const isRejected = rejected.has(glyph.label);
          const displayChar = getDisplayChar(glyph.label);
          return (
            <button
              key={glyph.label}
              onClick={() => toggleRejected(glyph.label)}
              aria-pressed={!isRejected}
              className={`group relative rounded-lg border flex flex-col items-center overflow-hidden transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-950 ${
                isRejected
                  ? "border-red-800 bg-red-950/30 opacity-40"
                  : "border-gray-800 bg-gray-900 hover:border-gray-600"
              }`}
              title={isRejected ? `Rejected: ${displayChar}` : `Approve: ${displayChar}`}
            >
              <div className="px-1 pt-1 w-full flex items-center justify-between">
                <span className={`text-xs font-bold font-mono ${isRejected ? "text-red-400" : "text-indigo-400"}`}>
                  {displayChar}
                </span>
                <span className="text-[10px] text-gray-600 font-mono">
                  {glyph.label.includes("_") ? glyph.label.split("_").pop() : ""}
                </span>
              </div>
              <div className="w-full aspect-square relative bg-gray-950 flex items-center justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={glyph.image_url}
                  alt={`Glyph: ${displayChar}`}
                  className={`max-w-full max-h-full object-contain ${
                    isRejected ? "grayscale" : ""
                  }`}
                />
                {isRejected && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-red-500 text-3xl font-bold">×</span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
      )}

      {/* Action bar */}
      <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-end">
        <a
          href="/upload"
          className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-5 py-2.5 text-sm transition-colors"
        >
          Back to Upload
        </a>
        <button
          onClick={() => router.push(`/generate?session=${session}`)}
          disabled={approvedCount === 0}
          className={`inline-flex items-center justify-center rounded-lg text-white font-semibold px-5 py-2.5 text-sm transition-colors ${
            approvedCount === 0
              ? "bg-indigo-600 opacity-50 cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-500"
          }`}
        >
          Proceed to Generate
        </button>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto px-4 py-16">
          <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
          <div className="flex items-center justify-center py-20">
            <div className="text-gray-400 text-lg">Loading...</div>
          </div>
        </div>
      }
    >
      <ReviewContent />
    </Suspense>
  );
}
