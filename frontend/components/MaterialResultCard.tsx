"use client";
import { useTranslations } from "next-intl";

export type ScanResult = {
  id: string;
  material: {
    name: string;
    code: string;
    category: string;
    biodegradable: boolean;
    recyclable: boolean;
    reusable: boolean;
    disposal_instructions: string | null;
    recycling_instructions: string | null;
  } | null;
  confidence_score: string | null;
  estimated_weight_kg: string | null;
  co2_saved_kg: string | null;
  tree_equivalent: string | null;
  energy_saved_kwh: string | null;
  landfill_volume_reduced_l: string | null;
  earnings_estimate: string | null;
};

export default function MaterialResultCard({ result }: { result: ScanResult }) {
  const t = useTranslations("scan");
  if (!result.material) return null;

  const badges = [
    result.material.biodegradable ? "Biodegradable" : "Non-biodegradable",
    result.material.recyclable ? "Recyclable" : "Non-recyclable",
    result.material.reusable ? "Reusable" : "Non-reusable",
  ];

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">{result.material.name}</h3>
        <span className="text-xs rounded-full bg-primary-100 dark:bg-primary-800 px-3 py-1">
          {t("confidence")}: {result.confidence_score ? `${Math.round(Number(result.confidence_score) * 100)}%` : "—"}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {badges.map((b) => (
          <span key={b} className="text-xs rounded-full border border-primary-200 dark:border-primary-700 px-3 py-1">
            {b}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <Stat label={t("weight")} value={result.estimated_weight_kg ? `${result.estimated_weight_kg} kg` : "—"} />
        <Stat label={t("co2_saved")} value={result.co2_saved_kg ? `${result.co2_saved_kg} kg CO2` : "—"} />
        <Stat label={t("trees")} value={result.tree_equivalent ?? "—"} />
        <Stat label={t("energy")} value={result.energy_saved_kwh ? `${result.energy_saved_kwh} kWh` : "—"} />
        <Stat label={t("landfill")} value={result.landfill_volume_reduced_l ? `${result.landfill_volume_reduced_l} L` : "—"} />
        <Stat label={t("earnings")} value={result.earnings_estimate ? `₹${result.earnings_estimate}` : "—"} />
      </div>

      {result.material.disposal_instructions && (
        <div>
          <p className="text-sm font-medium">{t("disposal")}</p>
          <p className="text-sm text-primary-600 dark:text-primary-300">{result.material.disposal_instructions}</p>
        </div>
      )}
      {result.material.recycling_instructions && (
        <div>
          <p className="text-sm font-medium">{t("recycling")}</p>
          <p className="text-sm text-primary-600 dark:text-primary-300">{result.material.recycling_instructions}</p>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-primary-500 dark:text-primary-400">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
