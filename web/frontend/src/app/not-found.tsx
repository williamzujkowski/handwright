import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto px-4 py-24 text-center">
      <p className="text-7xl font-bold text-gray-800 mb-4">404</p>
      <h2 className="text-2xl font-bold text-white mb-3">Page not found</h2>
      <p className="text-gray-400 mb-8">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/"
        className="inline-flex items-center justify-center rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-2.5 text-sm transition-colors"
      >
        Go home
      </Link>
    </div>
  );
}
