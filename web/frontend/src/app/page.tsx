import Link from "next/link";

const steps = [
  {
    number: "1",
    title: "Write",
    description:
      "Download and print a worksheet. Fill in every letter, number, and punctuation mark in your natural handwriting.",
    icon: "✏️",
  },
  {
    number: "2",
    title: "Upload",
    description:
      "Photograph or scan your completed worksheet and upload it here. We handle the rest — no special equipment needed.",
    icon: "📷",
  },
  {
    number: "3",
    title: "Generate",
    description:
      "We extract each glyph, let you review and adjust, then package everything as a downloadable font file.",
    icon: "🔤",
  },
] as const;

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-4 py-24 sm:py-32">
        <h1 className="text-5xl sm:text-6xl font-bold tracking-tight text-white mb-4">
          Handwright
        </h1>
        <p className="text-xl sm:text-2xl font-medium text-indigo-400 mb-6">
          Turn your handwriting into a font.
        </p>
        <p className="max-w-xl text-gray-400 text-base sm:text-lg leading-relaxed mb-10">
          Write once on a simple worksheet, upload a photo, and get a fully
          usable font — ready to use in any app — built from your own
          handwriting. No design skills required.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Link
            href="/worksheet"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 transition-colors shadow-lg shadow-indigo-900/40"
          >
            Get Started
          </Link>
          <a
            href="#how-it-works"
            className="inline-flex items-center justify-center rounded-lg border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-semibold px-6 py-3 transition-colors"
          >
            Learn More
          </a>
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="px-4 py-20 border-t border-gray-800"
      >
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-white mb-3">
            How It Works
          </h2>
          <p className="text-center text-gray-400 mb-12 max-w-lg mx-auto">
            Three simple steps, no special equipment, no design experience
            needed.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {steps.map((step) => (
              <div
                key={step.number}
                className="flex flex-col items-center text-center rounded-xl border border-gray-800 bg-gray-900 p-8 hover:border-indigo-800 transition-colors"
              >
                <span className="text-4xl mb-4">{step.icon}</span>
                <div className="flex items-center gap-2 mb-3">
                  <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white text-sm font-bold">
                    {step.number}
                  </span>
                  <h3 className="text-xl font-semibold text-white">
                    {step.title}
                  </h3>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="px-4 py-16 border-t border-gray-800">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            Ready to get started?
          </h2>
          <p className="text-gray-400 mb-8">
            Generate your worksheet now — it takes less than a minute.
          </p>
          <Link
            href="/worksheet"
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3 transition-colors"
          >
            Generate Worksheet
          </Link>
        </div>
      </section>
    </div>
  );
}
