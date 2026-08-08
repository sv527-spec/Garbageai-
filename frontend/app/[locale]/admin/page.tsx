"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { apiFetch } from "@/lib/api";
import StatCard from "@/components/StatCard";

type Summary = { total_scans: number; total_users: number };

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    if (user?.role !== "admin") return;
    apiFetch<Summary>("/admin/analytics/summary").then(setSummary);
  }, [user]);

  if (authLoading) return null;
  if (!user || user.role !== "admin") {
    return <p>Admin access only.</p>;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Admin Panel</h1>
      <div className="grid sm:grid-cols-2 gap-4">
        <StatCard label="Total Scans" value={String(summary?.total_scans ?? "—")} />
        <StatCard label="Total Users" value={String(summary?.total_users ?? "—")} />
      </div>
      <p className="text-sm text-primary-500">
        Extend this panel with user management, market price editing, CO2 factor editing, and recycling
        center CRUD — the backend endpoints (`/admin/users`, `/market-prices`, `/recycling-centers`)
        already exist; this page currently only surfaces the summary metrics as a starting point.
      </p>
    </div>
  );
}
