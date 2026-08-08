"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push(`/${locale}/dashboard`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto card space-y-4">
      <h1 className="text-xl font-semibold">{t("login_title")}</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="input" type="email" placeholder={t("email")} value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="input" type="password" placeholder={t("password")} value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="btn-primary w-full" type="submit" disabled={loading}>{t("submit_login")}</button>
      </form>
      <p className="text-sm text-primary-600 dark:text-primary-300">
        {t("no_account")} <Link href={`/${locale}/register`} className="underline">{t("submit_register")}</Link>
      </p>
    </div>
  );
}
