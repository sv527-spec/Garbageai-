import { useTranslations } from "next-intl";
import ScanUploader from "@/components/ScanUploader";

export default function ScanPage() {
  const t = useTranslations("scan");
  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold">{t("title")}</h1>
      <ScanUploader />
    </div>
  );
}
