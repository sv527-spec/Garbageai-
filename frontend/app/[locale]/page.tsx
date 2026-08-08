import Link from "next/link";
import { useTranslations } from "next-intl";

export default function LandingPage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations("landing");

  const features = [
    { title: t("feature_ai_title"), desc: t("feature_ai_desc"), icon: "🤖" },
    { title: t("feature_co2_title"), desc: t("feature_co2_desc"), icon: "🌍" },
    { title: t("feature_earn_title"), desc: t("feature_earn_desc"), icon: "💰" },
    { title: t("feature_bin_title"), desc: t("feature_bin_desc"), icon: "🗑️" },
  ];

  return (
    <div className="space-y-16">
      <section className="text-center max-w-2xl mx-auto space-y-6 py-8">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-primary-800 dark:text-primary-200">
          {t("title")}
        </h1>
        <p className="text-lg text-primary-600 dark:text-primary-300">{t("subtitle")}</p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href={`/${locale}/scan`} className="btn-primary">{t("cta_scan")}</Link>
          <Link href={`/${locale}/dashboard`} className="btn-secondary">{t("cta_learn")}</Link>
        </div>
      </section>

      <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((f) => (
          <div key={f.title} className="card">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold mb-1">{f.title}</h3>
            <p className="text-sm text-primary-600 dark:text-primary-300">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
