"use client";
import { useTheme } from "@/lib/theme-context";

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle color theme"
      className="rounded-full border border-primary-200 dark:border-primary-700 w-9 h-9 flex items-center justify-center hover:bg-primary-50 dark:hover:bg-primary-800/40 transition-colors"
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
