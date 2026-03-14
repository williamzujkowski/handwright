"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  FileText,
  Upload,
  CheckSquare,
  Wand2,
  type LucideIcon,
} from "lucide-react";

interface NavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

const navLinks: NavLink[] = [
  { href: "/", label: "Home", icon: Home },
  { href: "/worksheet", label: "Worksheet", icon: FileText },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/review", label: "Review", icon: CheckSquare },
  { href: "/generate", label: "Generate", icon: Wand2 },
];

export function Nav() {
  const pathname = usePathname();

  return (
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
            {navLinks.map(({ href, label, icon: Icon }) => {
              const isActive =
                href === "/" ? pathname === "/" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
                    isActive
                      ? "bg-gray-800 text-white font-medium"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-400" : ""}`} />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
