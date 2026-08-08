"use client";
import { useRouter, usePathname } from "next/navigation";
import { locales, localeNames, type Locale } from "@/i18n/config";

export default function LanguageSwitcher({ currentLocale }: { currentLocale: string }) {
  const router = useRouter();
  const pathname = usePathname();

  function onChange(next: string) {
    const segments = pathname.split("/");
    segments[1] = next;
    router.push(segments.join("/"));
  }

  return (
    <select
      value={currentLocale}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Select language"
      className="rounded-lg border border-primary-200 dark:border-primary-700 bg-transparent px-2 py-1.5 text-sm"
    >
      {locales.map((l: Locale) => (
        <option key={l} value={l} className="text-black">
          {localeNames[l]}
        </option>
      ))}
    </select>
  );
}
