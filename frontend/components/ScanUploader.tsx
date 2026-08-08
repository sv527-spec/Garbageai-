"use client";
import { useState, useRef } from "react";
import { useTranslations } from "next-intl";
import { apiUpload } from "@/lib/api";
import MaterialResultCard, { ScanResult } from "./MaterialResultCard";

export default function ScanUploader() {
  const t = useTranslations("scan");
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    setResult(null);
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("disposal_mode", "recycle");
      const data = await apiUpload<ScanResult>("/scans", formData);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card flex flex-col items-center justify-center gap-4 py-12 border-dashed">
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="Preview" className="max-h-64 rounded-xl object-contain" />
        ) : (
          <p className="text-primary-500 dark:text-primary-400">{t("upload_prompt")}</p>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          capture="environment"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        <button className="btn-primary" onClick={() => inputRef.current?.click()} disabled={loading}>
          {loading ? t("analyzing") : t("choose_file")}
        </button>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}
      {result && (
        <>
          <MaterialResultCard result={result} />
          <button className="btn-secondary" onClick={() => { setResult(null); setPreview(null); }}>
            {t("scan_another")}
          </button>
        </>
      )}
    </div>
  );
}
