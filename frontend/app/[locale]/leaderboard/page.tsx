"use client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { apiFetch } from "@/lib/api";

type Entry = {
  user_id: string;
  full_name: string;
  total_weight_kg: string;
  total_co2_kg: string;
  total_earnings: string;
  rank: number | null;
};

export default function LeaderboardPage() {
  const t = useTranslations("leaderboard");
  const [period, setPeriod] = useState<"daily" | "monthly" | "alltime">("monthly");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch<Entry[]>(`/leaderboard?period=${period}&scope=national`, { auth: false })
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-semibold">{t("title")}</h1>
        <div className="flex gap-2">
          {(["daily", "monthly", "alltime"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={p === period ? "btn-primary !px-3 !py-1.5 text-sm" : "btn-secondary !px-3 !py-1.5 text-sm"}
            >
              {t(`period_${p}`)}
            </button>
          ))}
        </div>
      </div>

      <div className="card overflow-x-auto">
        {loading ? (
          <p className="text-sm text-primary-500">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-primary-500">No data yet for this period.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-primary-500 border-b border-primary-100 dark:border-primary-800">
                <th className="py-2 pr-4">{t("rank")}</th>
                <th className="py-2 pr-4">{t("name")}</th>
                <th className="py-2 pr-4">{t("weight")}</th>
                <th className="py-2 pr-4">{t("co2")}</th>
                <th className="py-2 pr-4">{t("earnings")}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.user_id} className="border-b border-primary-50 dark:border-primary-900">
                  <td className="py-2 pr-4 font-medium">#{e.rank}</td>
                  <td className="py-2 pr-4">{e.full_name}</td>
                  <td className="py-2 pr-4">{e.total_weight_kg}</td>
                  <td className="py-2 pr-4">{e.total_co2_kg}</td>
                  <td className="py-2 pr-4">₹{e.total_earnings}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
