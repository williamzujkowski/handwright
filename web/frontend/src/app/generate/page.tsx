"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface FontGenerateResponse {
  download_url: string;
  family_name: string;
}

interface RenderResponse {
  image_url: string;
}

function GeneratePageContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");

  const [familyName, setFamilyName] = useState("My Handwriting");
  const [designer, setDesigner] = useState("");
  const [generating, setGenerating] = useState(false);
  const [fontError, setFontError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const [renderText, setRenderText] = useState("");
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [renderedImageUrl, setRenderedImageUrl] = useState<string | null>(null);

  if (!sessionId) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="rounded-xl border border-red-800 bg-red-950/50 p-8 text-center">
          <h1 className="text-2xl font-bold text-red-300 mb-3">
            No Session Found
          </h1>
          <p className="text-red-400 mb-6">
            A valid session is required to generate a font. Please start by
            uploading a worksheet.
          </p>
          <a
            href="/upload"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 text-sm transition-colors"
          >
            Go to Upload
          </a>
        </div>
      </div>
    );
  }

  const handleGenerateFont = async () => {
    setGenerating(true);
    setFontError(null);
    setDownloadUrl(null);

    try {
      const response = await fetch(`${API_URL}/api/font/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          family_name: familyName,
          designer: designer || undefined,
        }),
      });

      if (!response.ok) {
        const body = await response.text().catch(() => "");
        throw new Error(body || response.statusText);
      }

      const data = (await response.json()) as FontGenerateResponse;
      setDownloadUrl(data.download_url);
    } catch (err) {
      setFontError(err instanceof Error ? err.message : "Font generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadFont = () => {
    if (!downloadUrl) return;
    const a = document.createElement("a");
    a.href = `${API_URL}${downloadUrl}`;
    a.download = `${familyName.replace(/\s+/g, "_")}.ttf`;
    a.click();
  };

  const handleRender = async () => {
    if (!renderText.trim()) return;
    setRendering(true);
    setRenderError(null);
    setRenderedImageUrl(null);

    try {
      const response = await fetch(`${API_URL}/api/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: renderText,
          session_id: sessionId,
          font_size: 48,
          line_spacing: 1.5,
        }),
      });

      if (!response.ok) {
        const body = await response.text().catch(() => "");
        throw new Error(body || response.statusText);
      }

      const data = (await response.json()) as RenderResponse;
      setRenderedImageUrl(data.image_url);
    } catch (err) {
      setRenderError(err instanceof Error ? err.message : "Rendering failed");
    } finally {
      setRendering(false);
    }
  };

  const handleDownloadImage = () => {
    if (!renderedImageUrl) return;
    const a = document.createElement("a");
    a.href = renderedImageUrl.startsWith("http")
      ? renderedImageUrl
      : `${API_URL}${renderedImageUrl}`;
    a.download = "rendered-note.png";
    a.click();
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">Generate</h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Generate a downloadable font from your handwriting, then use it to
        render text as a handwritten note.
      </p>

      {/* Font Generation Section */}
      <section className="rounded-xl border border-gray-800 bg-gray-900 p-6 mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">
          Font Generation
        </h2>

        <div className="space-y-4">
          <div>
            <label
              htmlFor="family-name"
              className="block text-sm font-medium text-gray-300 mb-1.5"
            >
              Font Family Name
            </label>
            <input
              id="family-name"
              type="text"
              value={familyName}
              onChange={(e) => setFamilyName(e.target.value)}
              className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              placeholder="My Handwriting"
            />
          </div>

          <div>
            <label
              htmlFor="designer"
              className="block text-sm font-medium text-gray-300 mb-1.5"
            >
              Designer{" "}
              <span className="text-gray-600 font-normal">(optional)</span>
            </label>
            <input
              id="designer"
              type="text"
              value={designer}
              onChange={(e) => setDesigner(e.target.value)}
              className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              placeholder="Your name"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={() => void handleGenerateFont()}
              disabled={generating || !familyName.trim()}
              className={`inline-flex items-center justify-center rounded-lg text-white font-semibold px-5 py-2.5 text-sm transition-colors ${
                generating || !familyName.trim()
                  ? "bg-indigo-600 opacity-50 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500"
              }`}
            >
              {generating ? (
                <>
                  <span className="animate-spin mr-2">&#9696;</span>
                  Generating...
                </>
              ) : (
                "Generate Font"
              )}
            </button>

            {downloadUrl && (
              <button
                onClick={handleDownloadFont}
                className="inline-flex items-center justify-center rounded-lg border border-indigo-500 text-indigo-400 hover:bg-indigo-950/50 font-semibold px-5 py-2.5 text-sm transition-colors"
              >
                Download .ttf
              </button>
            )}
          </div>
        </div>

        {fontError && (
          <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm">
            {fontError}
          </div>
        )}

        {downloadUrl && !fontError && (
          <div className="mt-4 p-3 rounded-lg bg-green-950/50 border border-green-800 text-green-300 text-sm">
            Font generated successfully. Click &quot;Download .ttf&quot; to save
            your font file.
          </div>
        )}
      </section>

      {/* Text Rendering Section */}
      {downloadUrl && (
        <section className="rounded-xl border border-gray-800 bg-gray-900 p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">
            Render Text
          </h2>

          <div>
            <label
              htmlFor="render-text"
              className="block text-sm font-medium text-gray-300 mb-1.5"
            >
              Enter text to render in your handwriting
            </label>
            <textarea
              id="render-text"
              rows={5}
              value={renderText}
              onChange={(e) => setRenderText(e.target.value)}
              placeholder="Type your text here..."
              className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3 py-2 text-sm resize-y focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <button
            onClick={() => void handleRender()}
            disabled={rendering || !renderText.trim()}
            className={`mt-4 inline-flex items-center justify-center rounded-lg text-white font-semibold px-5 py-2.5 text-sm transition-colors ${
              rendering || !renderText.trim()
                ? "bg-indigo-600 opacity-50 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500"
            }`}
          >
            {rendering ? (
              <>
                <span className="animate-spin mr-2">&#9696;</span>
                Rendering...
              </>
            ) : (
              "Render"
            )}
          </button>

          {renderError && (
            <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm">
              {renderError}
            </div>
          )}

          {renderedImageUrl && (
            <div className="mt-6 space-y-4">
              <div className="rounded-xl border border-gray-700 bg-gray-800 p-4 overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={
                    renderedImageUrl.startsWith("http")
                      ? renderedImageUrl
                      : `${API_URL}${renderedImageUrl}`
                  }
                  alt="Rendered handwriting"
                  className="w-full rounded-lg"
                />
              </div>
              <button
                onClick={handleDownloadImage}
                className="inline-flex items-center justify-center rounded-lg border border-indigo-500 text-indigo-400 hover:bg-indigo-950/50 font-semibold px-5 py-2.5 text-sm transition-colors"
              >
                Download Image
              </button>
            </div>
          )}
        </section>
      )}

      {/* Navigation */}
      <div className="flex flex-col sm:flex-row gap-3 justify-end">
        <a
          href={`/review?session=${sessionId}`}
          className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-5 py-2.5 text-sm transition-colors"
        >
          Back to Review
        </a>
      </div>
    </div>
  );
}

export default function GeneratePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="text-gray-400">Loading...</div>
        </div>
      }
    >
      <GeneratePageContent />
    </Suspense>
  );
}
