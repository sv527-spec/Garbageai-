"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const ROLES = ["user", "worker", "supervisor", "admin"] as const;

export default function RegisterPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const { register } = useAuth();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "user" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register({ ...form, language_pref: locale });
      router.push(`/${locale}/dashboard`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto card space-y-4">
      <h1 className="text-xl font-semibold">{t("register_title")}</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="input" placeholder={t("full_name")} value={form.full_name}
          onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        <input className="input" type="email" placeholder={t("email")} value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className="input" type="password" placeholder={t("password")} value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
        <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          {ROLES.map((r) => (
            <option key={r} value={r}>{t(`role_${r}` as any)}</option>
          ))}
        </select>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="btn-primary w-full" type="submit" disabled={loading}>{t("submit_register")}</button>
      </form>
      <p className="text-sm text-primary-600 dark:text-primary-300">
        {t("have_account")} <Link href={`/${locale}/login`} className="underline">{t("submit_login")}</Link>
      </p>
    </div>
  );
}
