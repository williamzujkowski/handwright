import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { Home, FileText, Upload, CheckSquare, Wand2 } from "lucide-react";
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

const navLinks = [
  { href: "/", label: "Home", icon: Home },
  { href: "/worksheet", label: "Worksheet", icon: FileText },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/review", label: "Review", icon: CheckSquare },
  { href: "/generate", label: "Generate", icon: Wand2 },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-950 text-gray-100 min-h-screen`}
      >
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-lg focus:text-sm focus:font-semibold"
        >
          Skip to content
        </a>
        <nav className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              <Link
                href="/"
                className="text-lg font-semibold tracking-tight text-white hover:text-indigo-400 transition-colors"
              >
                Handwright
              </Link>
              <div className="flex items-center gap-1 overflow-x-auto">
                {navLinks.map(({ href, label, icon: Icon }) => (
                  <Link
                    key={href}
                    href={href}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900"
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </nav>
        <ToastProvider>
          <main id="main-content">{children}</main>
        </ToastProvider>
      </body>
    </html>
  );
}
