"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { Suspense } from "react";

const STEPS = [
  { label: "Worksheet", path: "/worksheet" },
  { label: "Upload", path: "/upload" },
  { label: "Review", path: "/review" },
  { label: "Generate", path: "/generate" },
] as const;

const STEP_ORDER: Record<string, number> = {
  "/worksheet": 0,
  "/upload": 1,
  "/review": 2,
  "/generate": 3,
};

function StepperContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const sessionId = searchParams?.get("session") ?? null;
  const currentIndex = STEP_ORDER[pathname] ?? -1;

  if (currentIndex === -1) return null;

  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center justify-center gap-0">
        {STEPS.map((step, idx) => {
          const isCompleted = idx < currentIndex;
          const isCurrent = idx === currentIndex;

          const href =
            isCompleted && sessionId && idx >= 2
              ? `${step.path}?session=${sessionId}`
              : isCompleted
                ? step.path
                : undefined;

          return (
            <li key={step.label} className="flex items-center">
              {idx > 0 && (
                <div
                  className={`w-6 sm:w-10 h-0.5 ${
                    isCompleted ? "bg-indigo-500" : "bg-gray-700"
                  }`}
                />
              )}
              {href ? (
                <a href={href} className="flex items-center gap-1.5 group">
                  <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white text-xs font-bold group-hover:bg-indigo-500 transition-colors">
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth="2.5"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4.5 12.75l6 6 9-13.5"
                      />
                    </svg>
                  </span>
                  <span className="hidden sm:inline text-xs text-indigo-400 group-hover:text-indigo-300 transition-colors">
                    {step.label}
                  </span>
                </a>
              ) : (
                <span className="flex items-center gap-1.5">
                  <span
                    className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold transition-all ${
                      isCurrent
                        ? "bg-indigo-600 text-white ring-2 ring-indigo-400/50 ring-offset-2 ring-offset-gray-950"
                        : "bg-gray-800 text-gray-500 border border-gray-700"
                    }`}
                  >
                    {idx + 1}
                  </span>
                  <span
                    className={`hidden sm:inline text-xs ${
                      isCurrent ? "text-white font-semibold" : "text-gray-600"
                    }`}
                  >
                    {step.label}
                  </span>
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function ProgressStepper() {
  return (
    <Suspense fallback={null}>
      <StepperContent />
    </Suspense>
  );
}
