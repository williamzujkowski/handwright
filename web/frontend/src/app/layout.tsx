import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Github } from "lucide-react";
import { Nav } from "@/components/nav";
import { ToastProvider } from "@/components/toast";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Handwright — Turn Your Handwriting Into a Font",
  description:
    "Upload a handwriting sample and generate a fully usable font from your own handwriting.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-950 text-gray-100 min-h-screen flex flex-col`}
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-lg focus:text-sm focus:font-semibold"
        >
          Skip to content
        </a>
        <Nav />
        <ToastProvider>
          <main id="main-content" className="flex-1">{children}</main>
        </ToastProvider>
        <footer className="border-t border-gray-800 py-6 mt-auto">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-gray-500">
            <p>&copy; {new Date().getFullYear()} Handwright. MIT License.</p>
            <a
              href="https://github.com/williamzujkowski/handwright"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <Github className="w-4 h-4" />
              Source on GitHub
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
