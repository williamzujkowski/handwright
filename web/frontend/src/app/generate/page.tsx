"use client";

import { useState } from "react";

type Tab = "note" | "font";

const tabs: { id: Tab; label: string }[] = [
  { id: "note", label: "Note Renderer" },
  { id: "font", label: "Font Download" },
];

export default function GeneratePage() {
  const [activeTab, setActiveTab] = useState<Tab>("note");

  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">Generate</h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Use your handwriting font to render a note as an image, or download the
        font file to install on your system.
      </p>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-800 mb-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? "bg-gray-900 text-white border border-b-gray-900 border-gray-800"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Note Renderer tab */}
      {activeTab === "note" && (
        <div className="flex flex-col gap-6">
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
            <label
              htmlFor="note-text"
              className="block text-sm font-medium text-gray-300 mb-2"
            >
              Note text
            </label>
            <textarea
              id="note-text"
              rows={5}
              disabled
              placeholder="Enter the text you want to render in your handwriting…"
              className="w-full rounded-lg bg-gray-800 border border-gray-700 text-gray-400 placeholder-gray-600 px-3 py-2 text-sm resize-none cursor-not-allowed"
            />
            <button
              disabled
              className="mt-4 inline-flex items-center justify-center rounded-lg bg-indigo-600 opacity-50 cursor-not-allowed text-white font-semibold px-5 py-2.5 text-sm"
            >
              Render Note
            </button>
          </div>

          {/* Preview placeholder */}
          <div className="rounded-xl border border-dashed border-gray-700 bg-gray-900 p-12 flex items-center justify-center text-gray-600 text-sm">
            Rendered note preview will appear here
          </div>
        </div>
      )}

      {/* Font Download tab */}
      {activeTab === "font" && (
        <div className="rounded-xl border border-gray-800 bg-gray-900 p-10 flex flex-col items-center gap-6 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center text-3xl">
            🔤
          </div>
          <div>
            <p className="text-gray-200 font-medium mb-1">
              Your font is not ready yet
            </p>
            <p className="text-gray-500 text-sm max-w-sm mx-auto">
              Complete the Upload and Review steps first. Once your glyphs are
              confirmed, the font will be generated and available for download
              as a .ttf file.
            </p>
          </div>
          <button
            disabled
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 opacity-50 cursor-not-allowed text-white font-semibold px-6 py-2.5 text-sm"
          >
            Download Font (.ttf)
          </button>
        </div>
      )}
    </div>
  );
}
