"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="max-w-xl mx-auto px-4 py-24 text-center">
      <div className="w-16 h-16 rounded-full bg-red-950/50 flex items-center justify-center mx-auto mb-6">
        <AlertTriangle className="w-8 h-8 text-red-400" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-3">
        Something went wrong
      </h2>
      <p className="text-gray-400 mb-8 leading-relaxed">
        {error.message || "An unexpected error occurred. Please try again."}
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          onClick={reset}
          className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 text-sm transition-colors"
        >
          Try again
        </button>
        <Link
          href="/"
          className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-6 py-2.5 text-sm transition-colors"
        >
          Go home
        </Link>
      </div>
    </div>
  );
}
