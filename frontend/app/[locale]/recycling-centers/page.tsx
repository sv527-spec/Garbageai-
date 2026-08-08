"use client";
import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { apiFetch } from "@/lib/api";

type Center = {
  id: string;
  name: string;
  address: string;
  phone: string | null;
  accepted_materials: string[];
  rating: string | null;
  distance_km: number | null;
  lat: string;
  lng: string;
};

export default function RecyclingCentersPage() {
  const t = useTranslations("centers");
  const [centers, setCenters] = useState<Center[]>([]);
  const [loading, setLoading] = useState(true);
  const [locError, setLocError] = useState<string | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) {
      fetchCenters();
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => fetchCenters(pos.coords.latitude, pos.coords.longitude),
      () => {
        setLocError("Location unavailable — showing all centers.");
        fetchCenters();
      }
    );
  }, []);

  function fetchCenters(lat?: number, lng?: number) {
    const qs = lat && lng ? `?lat=${lat}&lng=${lng}&radius_km=50` : "";
    apiFetch<Center[]>(`/recycling-centers${qs}`, { auth: false })
      .then(setCenters)
      .finally(() => setLoading(false));
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">{t("title")}</h1>
      {locError && <p className="text-sm text-primary-500">{locError}</p>}

      {loading ? (
        <p className="text-sm text-primary-500">Loading…</p>
      ) : centers.length === 0 ? (
        <p className="text-sm text-primary-500">No recycling centers found nearby yet.</p>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {centers.map((c) => (
            <div key={c.id} className="card space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{c.name}</h3>
                {c.rating && <span className="text-sm">⭐ {c.rating}</span>}
              </div>
              <p className="text-sm text-primary-600 dark:text-primary-300">{c.address}</p>
              {c.distance_km != null && <p className="text-xs text-primary-500">{t("distance")}: {c.distance_km} km</p>}
              <p className="text-xs">
                {t("materials")}: {c.accepted_materials.join(", ") || "—"}
              </p>
              <div className="flex gap-3 pt-1">
                {c.phone && <a className="btn-secondary !px-3 !py-1.5 text-xs" href={`tel:${c.phone}`}>{t("call")}</a>}
                <a
                  className="btn-primary !px-3 !py-1.5 text-xs"
                  href={`https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t("directions")}
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
