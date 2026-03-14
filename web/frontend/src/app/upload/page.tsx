"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadImage } from "@/lib/api";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".pdf", ".heic"]);

function getExtension(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      // Validate extension
      const ext = getExtension(file.name);
      if (!ALLOWED_EXTENSIONS.has(ext)) {
        setError(
          `Unsupported format "${ext}". Accepted: ${[...ALLOWED_EXTENSIONS].join(", ")}`
        );
        return;
      }

      // Validate size
      if (file.size > MAX_FILE_SIZE) {
        setError(
          `File is ${(file.size / 1024 / 1024).toFixed(1)} MB — maximum is 10 MB.`
        );
        return;
      }

      setFileName(file.name);
      setUploading(true);

      try {
        const data = await uploadImage(file);
        router.push(`/review?session=${data.session_id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
        setUploading(false);
      }
    },
    [router]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) void handleFile(file);
    },
    [handleFile]
  );

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) void handleFile(file);
    },
    [handleFile]
  );

  return (
    <div className="max-w-3xl mx-auto px-4 py-16">
      <h1 className="text-3xl font-bold text-white mb-3">
        Upload Handwriting
      </h1>
      <p className="text-gray-400 mb-8 leading-relaxed">
        Upload a photo or scan of your completed worksheet. For best results,
        use good lighting and keep the page flat.
      </p>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.pdf,.heic"
        className="hidden"
        onChange={onFileSelect}
      />

      {/* Drag-and-drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed transition-colors p-16 flex flex-col items-center gap-4 text-center cursor-pointer ${
          dragOver
            ? "border-indigo-500 bg-indigo-950/30"
            : "border-gray-700 bg-gray-900 hover:border-indigo-600"
        } ${uploading ? "pointer-events-none opacity-60" : ""}`}
        role="button"
        aria-label="Upload worksheet image"
      >
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center text-3xl">
          {uploading ? (
            <span className="animate-spin">&#9696;</span>
          ) : (
            <span>&#128193;</span>
          )}
        </div>
        <div>
          {uploading ? (
            <p className="text-gray-200 font-medium">
              Uploading {fileName}...
            </p>
          ) : (
            <>
              <p className="text-gray-200 font-medium mb-1">
                Drag and drop your worksheet here
              </p>
              <p className="text-gray-500 text-sm">
                Or click to browse — PNG, JPG, PDF, or HEIC accepted
              </p>
            </>
          )}
        </div>
        {!uploading && (
          <button
            type="button"
            className="mt-2 inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 text-sm transition-colors"
          >
            Choose File
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-sm">
          {error}
        </div>
      )}

      <p className="mt-4 text-xs text-gray-600 text-center">
        Maximum file size: 10 MB. Images are processed server-side and not
        retained after your session.
      </p>

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
