// Central locale registry. Adding a language later = add its code here + drop messages/<code>.json.
export const locales = ["en", "hi", "as", "bn", "ne", "lus", "lep", "nag"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";

export const localeNames: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी (Hindi)",
  as: "অসমীয়া (Assamese)",
  bn: "বাংলা (Bengali)",
  ne: "नेपाली (Nepali)",
  lus: "Mizo tawng",
  lep: "ᰛᰩᰵ (Lepcha)",
  nag: "Nagamese",
};
