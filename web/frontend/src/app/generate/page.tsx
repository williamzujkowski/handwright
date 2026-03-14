"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ProgressStepper } from "@/components/progress-stepper";
import { useToast } from "@/components/toast";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface FontGenerateResponse {
  download_url: string;
  woff2_url: string;
  css_snippet: string;
  glyph_count: number;
  variant_count: number;
}

interface RenderResponse {
  image_url: string;
  width: number;
  height: number;
}

/* ------------------------------------------------------------------ */
/* Main Content                                                        */
/* ------------------------------------------------------------------ */

function GeneratePageContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");
  const { toast } = useToast();

  const [familyName, setFamilyName] = useState("My Handwriting");
  const [designer, setDesigner] = useState("");
  const [generating, setGenerating] = useState(false);
  const [fontError, setFontError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [woff2Url, setWoff2Url] = useState<string | null>(null);
  const [cssSnippet, setCssSnippet] = useState<string | null>(null);
  const [glyphCount, setGlyphCount] = useState<number | null>(null);
  const [variantCount, setVariantCount] = useState<number | null>(null);

  const [renderText, setRenderText] = useState(
    "The quick brown fox jumps over the lazy dog",
  );
  const [fontSize, setFontSize] = useState(48);
  const [rendering, setRendering] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [renderedImageUrl, setRenderedImageUrl] = useState<string | null>(null);

  if (!sessionId) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <ProgressStepper />
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
    setWoff2Url(null);
    setCssSnippet(null);
    setGlyphCount(null);
    setVariantCount(null);

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
      setWoff2Url(data.woff2_url);
      setCssSnippet(data.css_snippet);
      setGlyphCount(data.glyph_count);
      setVariantCount(data.variant_count);
      toast(`Font generated with ${data.glyph_count} glyphs!`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Font generation failed";
      setFontError(message);
      toast(message, "error");
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

  const handleDownloadWoff2 = () => {
    if (!woff2Url) return;
    const a = document.createElement("a");
    a.href = `${API_URL}${woff2Url}`;
    a.download = `${familyName.replace(/\s+/g, "_")}.woff2`;
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
          font_size: fontSize,
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
      setRenderError(
        err instanceof Error ? err.message : "Rendering failed",
      );
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

  const fontGenerated = !!downloadUrl && !fontError;

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <ProgressStepper />

      <h1 className="text-3xl font-bold text-white mb-2">
        Generate Your Font
      </h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Turn your handwriting samples into a downloadable font file, then
        preview it with any text you like.
      </p>

      {/* ---------------------------------------------------------- */}
      {/* Step 1 — Font Generation                                    */}
      {/* ---------------------------------------------------------- */}
      <section className="rounded-xl border border-gray-800 bg-gray-900 p-6 mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600/20 text-indigo-400 text-xs font-bold">
            1
          </span>
          <h2 className="text-xl font-semibold text-white">
            Build Your Font
          </h2>
        </div>
        <p className="text-gray-400 text-sm mb-5">
          Choose a name for your font family and optionally credit a designer.
          We will package your glyphs into TTF and WOFF2 files.
        </p>

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

          <div className="pt-2">
            <button
              onClick={() => void handleGenerateFont()}
              disabled={generating || !familyName.trim()}
              className={`inline-flex items-center justify-center rounded-lg text-white font-semibold px-6 py-2.5 text-sm transition-colors ${
                generating || !familyName.trim()
                  ? "bg-indigo-600 opacity-50 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500"
              }`}
            >
              {generating ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Generating...
                </>
              ) : (
                "Generate Font"
              )}
            </button>
          </div>
        </div>

        {fontError && (
          <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm">
            {fontError}
          </div>
        )}

        {/* Success state with download buttons */}
        {fontGenerated && (
          <div className="mt-6 rounded-xl border border-green-800/50 bg-green-950/30 p-5">
            <div className="flex items-start gap-3 mb-4">
              <svg
                className="w-5 h-5 text-green-400 mt-0.5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="text-green-300 font-semibold text-sm">
                  Font generated successfully!
                </p>
                <p className="text-green-400/70 text-xs mt-0.5">
                  {glyphCount} glyph{glyphCount !== 1 ? "s" : ""}
                  {variantCount
                    ? ` with ${variantCount} variant${variantCount !== 1 ? "s" : ""}`
                    : ""}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleDownloadFont}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 text-sm transition-colors"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                  />
                </svg>
                Download .ttf
              </button>
              <button
                onClick={handleDownloadWoff2}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 text-sm transition-colors"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                  />
                </svg>
                Download .woff2
              </button>
            </div>
          </div>
        )}

        {/* CSS snippet */}
        {cssSnippet && !fontError && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-sm font-medium text-gray-300">
                CSS snippet — use this to load your font on the web
              </p>
              <button
                onClick={() => {
                  void navigator.clipboard.writeText(cssSnippet).then(() => {
                    toast("CSS copied to clipboard!", "info");
                  });
                }}
                className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-indigo-400 transition-colors px-2 py-1 rounded hover:bg-gray-800"
                title="Copy to clipboard"
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"
                  />
                </svg>
                Copy
              </button>
            </div>
            <pre className="rounded-lg bg-gray-800 border border-gray-700 text-gray-300 text-xs px-4 py-3 overflow-x-auto whitespace-pre">
              {cssSnippet}
            </pre>
          </div>
        )}
      </section>

      {/* ---------------------------------------------------------- */}
      {/* Step 2 — Try Your Font (appears after generation)           */}
      {/* ---------------------------------------------------------- */}
      {fontGenerated && (
        <section className="rounded-xl border border-gray-800 bg-gray-900 p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600/20 text-indigo-400 text-xs font-bold">
              2
            </span>
            <h2 className="text-xl font-semibold text-white">
              Try Your Font
            </h2>
          </div>
          <p className="text-gray-400 text-sm mb-5">
            Type anything below to see it rendered in your handwriting. Adjust
            the font size with the slider and hit Preview.
          </p>

          <div className="space-y-4">
            {/* Text input */}
            <div>
              <label
                htmlFor="render-text"
                className="block text-sm font-medium text-gray-300 mb-1.5"
              >
                Preview text
              </label>
              <textarea
                id="render-text"
                rows={4}
                value={renderText}
                onChange={(e) => setRenderText(e.target.value)}
                placeholder="Type something to preview your handwriting..."
                className="w-full rounded-lg bg-gray-800 border border-gray-700 text-white placeholder-gray-500 px-3 py-2 text-sm resize-y focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {/* Font size slider */}
            <div>
              <label
                htmlFor="font-size"
                className="block text-sm font-medium text-gray-300 mb-1.5"
              >
                Font size:{" "}
                <span className="text-indigo-400 font-semibold">
                  {fontSize}px
                </span>
              </label>
              <input
                id="font-size"
                type="range"
                min={16}
                max={96}
                step={2}
                value={fontSize}
                onChange={(e) => setFontSize(Number(e.target.value))}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gray-700 accent-indigo-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>16px</span>
                <span>96px</span>
              </div>
            </div>

            {/* Preview button */}
            <button
              onClick={() => void handleRender()}
              disabled={rendering || !renderText.trim()}
              className={`inline-flex items-center justify-center gap-2 rounded-lg text-white font-semibold px-6 py-2.5 text-sm transition-colors ${
                rendering || !renderText.trim()
                  ? "bg-indigo-600 opacity-50 cursor-not-allowed"
                  : "bg-indigo-600 hover:bg-indigo-500"
              }`}
            >
              {rendering ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Rendering...
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth="2"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  Preview
                </>
              )}
            </button>
          </div>

          {renderError && (
            <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm">
              {renderError}
            </div>
          )}

          {/* Rendered preview image */}
          {renderedImageUrl && (
            <div className="mt-6 space-y-4">
              <div className="rounded-xl border border-gray-700 bg-white p-4 overflow-hidden">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={
                    renderedImageUrl.startsWith("http")
                      ? renderedImageUrl
                      : `${API_URL}${renderedImageUrl}`
                  }
                  alt="Rendered handwriting preview"
                  className="w-full rounded-lg"
                />
              </div>
              <button
                onClick={handleDownloadImage}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-indigo-500 text-indigo-400 hover:bg-indigo-950/50 font-semibold px-5 py-2.5 text-sm transition-colors"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="2"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                  />
                </svg>
                Download Image
              </button>
            </div>
          )}
        </section>
      )}

      {/* ---------------------------------------------------------- */}
      {/* Navigation                                                  */}
      {/* ---------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row gap-3 justify-between items-center">
        <a
          href={`/review?session=${sessionId}`}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-5 py-2.5 text-sm transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
            />
          </svg>
          Back to Review
        </a>

        {fontGenerated && (
          <p className="text-gray-500 text-xs">
            Your font files are ready for download above.
          </p>
        )}
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
