// Fetch helpers for the Bio Mantra backend (SPEC §9). Base URL comes from VITE_API_URL.
export const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

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
export type Metrics = {
  data_source: string; rows: number; test_period: [string, string]; best_iteration: number;
  persistence: ModelScores; linear: ModelScores; lightgbm: ModelScores;
};
export type Meta = { users: User[]; institutions: { id: number; name: string }[]; model_metrics: Metrics };
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
  const resp = await fetch(API_URL + path, init);
  if (!resp.ok) throw new Error(`${resp.status}: ${await resp.text()}`);
  return resp.json() as Promise<T>;
}

export const api = {
  forecast: (lang: Lang) => request<Forecast>(`/forecast?lang=${lang}`),
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
export const uploadUrl = (path: string) => API_URL + path;
