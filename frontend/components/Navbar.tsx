"use client";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useAuth } from "@/lib/auth-context";
import ThemeToggle from "./ThemeToggle";
import LanguageSwitcher from "./LanguageSwitcher";

export default function Navbar({ locale }: { locale: string }) {
  const t = useTranslations("nav");
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-primary-100 dark:border-primary-800 bg-white/80 dark:bg-surface-dark/80 backdrop-blur">
      <nav className="mx-auto max-w-6xl flex items-center justify-between px-4 py-3">
        <Link href={`/${locale}`} className="font-semibold text-lg text-primary-700 dark:text-primary-300">
          ♻️ SmartWaste
        </Link>
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          <Link href={`/${locale}/scan`}>{t("scan")}</Link>
          <Link href={`/${locale}/dashboard`}>{t("dashboard")}</Link>
          <Link href={`/${locale}/leaderboard`}>{t("leaderboard")}</Link>
          <Link href={`/${locale}/recycling-centers`}>{t("centers")}</Link>
        </div>
        <div className="flex items-center gap-3">
          <LanguageSwitcher currentLocale={locale} />
          <ThemeToggle />
          {user ? (
            <button onClick={logout} className="btn-secondary !px-3 !py-1.5 text-sm">{t("logout")}</button>
          ) : (
            <Link href={`/${locale}/login`} className="btn-primary !px-3 !py-1.5 text-sm">{t("login")}</Link>
          )}
        </div>
      </nav>
    </header>
  );
}
