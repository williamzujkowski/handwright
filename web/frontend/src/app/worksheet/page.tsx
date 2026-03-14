"use client";

import { useState } from "react";
import { generateWorksheet } from "@/lib/api";
import { ProgressStepper } from "@/components/progress-stepper";
import { useToast } from "@/components/toast";

export default function WorksheetPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [includeSymbols, setIncludeSymbols] = useState(false);
  const { toast } = useToast();

  async function handleGenerate() {
    setLoading(true);
    setError(null);

    try {
      const blob = await generateWorksheet(includeSymbols);

      // Trigger browser download
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "handwright_worksheet.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast("Worksheet downloaded successfully!");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to generate worksheet.";
      setError(message);
      toast(message, "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <ProgressStepper />
      <h1 className="text-3xl font-bold text-white mb-3">
        Generate Worksheet
      </h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Download a printable worksheet containing all the characters we need to
        build your font. Fill it in with your natural handwriting, then head to
        the Upload step.
      </p>

      <div className="rounded-xl border border-gray-800 bg-gray-900 p-10 flex flex-col items-center gap-6 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center text-3xl">
          📄
        </div>
        <div>
          <p className="text-gray-300 font-medium mb-1">
            Handwriting Worksheet (PDF)
          </p>
          <p className="text-gray-500 text-sm">
            The PDF includes all 96 printable ASCII characters laid out in
            clearly defined boxes with alignment markers.
          </p>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={includeSymbols}
            onChange={(e) => setIncludeSymbols(e.target.checked)}
            className="rounded border-gray-600 bg-gray-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-gray-900 w-4 h-4"
          />
          Include extended symbols (@#$%^*+=[] etc.)
        </label>

        <button
          onClick={handleGenerate}
          disabled={loading}
          className={`inline-flex items-center justify-center rounded-lg text-white font-semibold px-6 py-2.5 text-sm transition-colors ${
            loading
              ? "bg-indigo-600 opacity-50 cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-500 cursor-pointer"
          }`}
        >
          {loading ? "Generating..." : "Generate & Download Worksheet"}
        </button>

        {error && (
          <p className="text-red-400 text-sm mt-2">Error: {error}</p>
        )}
      </div>

      <div className="mt-8 rounded-lg border border-gray-800 bg-gray-900/50 p-6">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">
          Instructions
        </h2>
        <ol className="list-decimal list-inside text-gray-400 text-sm space-y-2">
          <li>Click the button above to generate and download the worksheet PDF.</li>
          <li>Print the PDF on standard letter or A4 paper.</li>
          <li>
            Write each character in its box using your natural handwriting and a
            dark pen or marker.
          </li>
          <li>
            Scan or photograph the completed worksheet (keep it flat and
            well-lit).
          </li>
          <li>
            Go to the{" "}
            <a href="/upload" className="text-indigo-400 hover:underline">
              Upload
            </a>{" "}
            page to submit your scan.
          </li>
        </ol>
      </div>

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
