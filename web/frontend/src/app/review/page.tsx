"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { getGlyphs, type GlyphData } from "@/lib/api";

function ReviewContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const session = searchParams.get("session");

  const [glyphs, setGlyphs] = useState<GlyphData[]>([]);
  const [loading, setLoading] = useState(!!session);
  const [error, setError] = useState<string | null>(
    session ? null : "No session parameter provided. Please upload a worksheet first."
  );
  const [rejected, setRejected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!session) return;

    getGlyphs(session)
      .then((data) => {
        setGlyphs(data.glyphs);
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
        <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
        <div className="flex items-center justify-center py-20">
          <div className="text-gray-400 text-lg">Loading glyphs...</div>
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
      <h1 className="text-3xl font-bold text-white mb-3">Review Glyphs</h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Each character extracted from your worksheet is shown below. Click any
        glyph to reject it. Rejected glyphs will not be included in your font.
      </p>

      {/* Status bar */}
      <div className="flex items-center justify-between mb-6 py-3 px-4 rounded-lg border border-gray-800 bg-gray-900 text-sm">
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
      <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-3">
        {glyphs.map((glyph) => {
          const isRejected = rejected.has(glyph.label);
          return (
            <button
              key={glyph.label}
              onClick={() => toggleRejected(glyph.label)}
              className={`group relative rounded-lg border flex flex-col items-center overflow-hidden transition-all ${
                isRejected
                  ? "border-red-800 bg-red-950/30 opacity-40"
                  : "border-gray-800 bg-gray-900 hover:border-gray-600"
              }`}
              title={isRejected ? `Rejected: ${glyph.label}` : `Approve: ${glyph.label}`}
            >
              <div className="w-full aspect-square relative bg-gray-950 flex items-center justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={glyph.image_url}
                  alt={`Glyph ${glyph.label}`}
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
              <span
                className={`text-xs py-1 font-mono truncate w-full text-center ${
                  isRejected ? "text-red-400 line-through" : "text-gray-400"
                }`}
              >
                {glyph.label}
              </span>
            </button>
          );
        })}
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
