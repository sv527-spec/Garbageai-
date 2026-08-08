"use client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import StatCard from "@/components/StatCard";

type Scan = {
  id: string;
  material: { name: string; category: string } | null;
  estimated_weight_kg: string | null;
  co2_saved_kg: string | null;
  earnings_estimate: string | null;
  status: string;
  created_at: string;
};

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const { user, loading: authLoading } = useAuth();
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    apiFetch<Scan[]>("/scans")
      .then(setScans)
      .finally(() => setLoading(false));
  }, [user]);

  if (authLoading) return null;
  if (!user) return <p>Please log in to view your dashboard.</p>;

  const totalWeight = scans.reduce((s, x) => s + Number(x.estimated_weight_kg ?? 0), 0);
  const totalCo2 = scans.reduce((s, x) => s + Number(x.co2_saved_kg ?? 0), 0);
  const totalEarnings = scans.reduce((s, x) => s + Number(x.earnings_estimate ?? 0), 0);
  const today = new Date().toDateString();
  const scannedToday = scans.filter((s) => new Date(s.created_at).toDateString() === today).length;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">{t("title")}, {user.full_name}</h1>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label={t("today")} value={String(scannedToday)} />
        <StatCard label={t("total_weight")} value={`${totalWeight.toFixed(2)} kg`} />
        <StatCard label={t("earnings")} value={`₹${totalEarnings.toFixed(2)}`} />
        <StatCard label={t("co2")} value={`${totalCo2.toFixed(2)} kg`} />
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">{t("recent_scans")}</h2>
        {loading ? (
          <p className="text-sm text-primary-500">Loading…</p>
        ) : scans.length === 0 ? (
          <p className="text-sm text-primary-500">No scans yet — go scan something!</p>
        ) : (
          <div className="card divide-y divide-primary-100 dark:divide-primary-800">
            {scans.slice(0, 10).map((s) => (
              <div key={s.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                <div>
                  <p className="font-medium">{s.material?.name ?? "Unknown"}</p>
                  <p className="text-xs text-primary-500">{new Date(s.created_at).toLocaleString()}</p>
                </div>
                <div className="text-right text-sm">
                  <p>{s.estimated_weight_kg ?? "—"} kg</p>
                  <p className="text-primary-500">₹{s.earnings_estimate ?? "0"}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
