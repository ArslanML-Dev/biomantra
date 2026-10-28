// English/Hindi UI strings. Forecast reason and tip text come translated from the backend.
import type { Lang } from "./api";

const STRINGS = {
  home: { en: "Home", hi: "होम" },
  act: { en: "Act", hi: "कार्य" },
  leaderboard: { en: "Leaderboard", hi: "लीडरबोर्ड" },
  map: { en: "Map", hi: "नक्शा" },
  about: { en: "About", hi: "जानकारी" },
  admin: { en: "Admin", hi: "एडमिन" },
  tomorrow: { en: "PM2.5 tomorrow (µg/m³)", hi: "कल का PM2.5 (µg/m³)" },
  now: { en: "Now", hi: "अभी" },
  takeAction: { en: "Take action", hi: "कदम उठाएँ" },
  whoAreYou: { en: "Who are you?", hi: "आप कौन हैं?" },
  loading: { en: "Loading…", hi: "लोड हो रहा है…" },
  users: { en: "Users", hi: "उपयोगकर्ता" },
  institutions: { en: "Institutions", hi: "संस्थान" },
  thisWeek: { en: "this week", hi: "इस हफ़्ते" },
  total: { en: "total", hi: "कुल" },
  goal: { en: "goal", hi: "लक्ष्य" },
  switchUser: { en: "Switch user", hi: "उपयोगकर्ता बदलें" },
  hello: { en: "Hello", hi: "नमस्ते" },
  settings: { en: "Settings", hi: "सेटिंग्स" },
} as const;

export type StringKey = keyof typeof STRINGS;

/** Look up a UI string in the chosen language. */
export const t = (lang: Lang, key: StringKey): string => STRINGS[key][lang];
