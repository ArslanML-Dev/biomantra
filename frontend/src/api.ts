// Fetch helpers for the Bio Mantra backend (SPEC §9).
import { Capacitor } from "@capacitor/core";

const SERVER_KEY = "serverUrl";

/** Backend URL: the one saved in Settings, else (laptop dev website) same host on port 8000, else VITE_API_URL. */
export function apiUrl(): string {
  const saved = localStorage.getItem(SERVER_KEY);
  if (saved) return saved;
  if (import.meta.env.DEV && !Capacitor.isNativePlatform()) return `${location.protocol}//${location.hostname}:8000`;
  return (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
}

/** Clean up a typed server address: add http:// if missing, drop a trailing slash. */
export function normalizeServerUrl(value: string): string {
  const url = value.trim().replace(/\/+$/, "");
  return /^https?:\/\//i.test(url) ? url : `http://${url}`;
}

/** Save a server URL on this device, or clear it (empty string) to use the default. */
export function saveServerUrl(value: string): void {
  if (value.trim()) localStorage.setItem(SERVER_KEY, normalizeServerUrl(value));
  else localStorage.removeItem(SERVER_KEY);
}

/** True if GET {url}/health answers {"ok": true} within 5 s. */
export async function testServer(url: string): Promise<boolean> {
  try {
    const resp = await fetch(`${normalizeServerUrl(url)}/health`, { signal: AbortSignal.timeout(5000) });
    return resp.ok && (await resp.json()).ok === true;
  } catch {
    return false;
  }
}

export type Lang = "en" | "hi";
export type Forecast = {
  location: { lat: number; lon: number }; generated_at: string;
  pm25_now: number; pm25_tomorrow: number; category: string; tier: number; color: string;
  reason: string; tip: string; disclaimer: string; model: { name: string; test_mae: number };
};
export type User = { id: number; name: string; institution_id: number; institution: string };
export type ModelScores = {
  mae: number; rmse: number; r2: number; acc_cat: number; macro_f1: number; recall_poor_plus: number;
};
export type Experiment = {
  target: "t24" | "mean24"; future_weather: boolean;
  val_mae: Record<"persistence" | "linear" | "lightgbm", number>;
  test: Record<"persistence" | "linear" | "lightgbm", ModelScores>;
};
export type Metrics = {
  data_source: string; rows: number; test_period: [string, string]; best_iteration: number;
  model: { kind: string; target: "t24" | "mean24"; future_weather: boolean; target_label: string };
  persistence: ModelScores; linear: ModelScores; lightgbm: ModelScores; experiments: Experiment[];
};
export type Meta = {
  users: User[]; institutions: { id: number; name: string }[]; model_metrics: Metrics;
  location: { lat: number; lon: number };
};
export type LeaderRow = {
  rank: number; id: number; name: string; points_total: number; points_week: number; goal: number; progress: number;
};
export type Hotspot = { id: number; lat: number; lon: number; created_at: string; open: boolean; cleaned_at: string | null };
export type Detection = { name: string; conf: number; box: number[] };
export type ActionResult = {
  id: number; status: "approved" | "needs_review" | "rejected"; confidence: number | null;
  points: number; reasons: string[]; detections: Detection[];
};
export type ReviewItem = {
  id: number; user_name: string; action_type: string; confidence: number; server_time: string;
  photo_url: string; before_photo_url: string | null; detections: Detection[]; reasons: string[];
};

/** Fetch JSON from the API; throw an Error with the server's message on failure. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(apiUrl() + path, { ...init, signal: AbortSignal.timeout(60000) });
  } catch {
    throw new Error(`Cannot reach the server at ${apiUrl()}. Check Settings → Server URL and that the laptop is on the same Wi-Fi.`);
  }
  if (!resp.ok) throw new Error(`${resp.status}: ${await resp.text()}`);
  return resp.json() as Promise<T>;
}

const WEATHER_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation";

/** Fetch the weather from Open-Meteo on this device: free hosting shares one server IP, which Open-Meteo rate-limits. */
async function deviceWeather(lat: number, lon: number): Promise<unknown> {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=${WEATHER_FIELDS}` +
    "&past_days=3&forecast_days=2&timezone=GMT";
  const resp = await fetch(url, { signal: AbortSignal.timeout(20000) });
  if (!resp.ok) throw new Error(`Open-Meteo ${resp.status}`);
  return (await resp.json()).hourly;
}

/** Forecast using weather fetched on this device; if that fails, let the server fetch the weather itself. */
async function forecast(lang: Lang): Promise<Forecast> {
  try {
    const { location } = await request<Meta>("/meta");
    const weather = await deviceWeather(location.lat, location.lon);
    return await request<Forecast>("/forecast", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: location.lat, lon: location.lon, lang, weather }),
    });
  } catch {
    return request<Forecast>(`/forecast?lang=${lang}`);
  }
}

export const api = {
  forecast,
  meta: () => request<Meta>("/meta"),
  leaderboard: (scope: "users" | "institutions") => request<LeaderRow[]>(`/leaderboard?scope=${scope}`),
  hotspots: () => request<Hotspot[]>("/hotspots"),
  submitAction: (form: FormData) => request<ActionResult>("/actions", { method: "POST", body: form }),
  reviewQueue: (token: string) => request<ReviewItem[]>("/admin/review", { headers: { "X-Admin-Token": token } }),
  review: (id: number, decision: "approve" | "reject", reviewer: string, token: string) =>
    request<{ id: number; status: string; points: number }>(`/admin/review/${id}`, {
      method: "POST",
      headers: { "X-Admin-Token": token, "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reviewer }),
    }),
};

/** Full URL for a backend upload path like /uploads/x.jpg. */
export const uploadUrl = (path: string) => apiUrl() + path;
