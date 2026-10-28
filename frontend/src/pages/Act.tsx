// Act: pick an action, take a LIVE camera photo (never the gallery) + GPS, submit, show the result.
import { useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Camera, CameraResultType, CameraSource } from "@capacitor/camera";
import { Geolocation } from "@capacitor/geolocation";
import { api, type ActionResult, type Lang, type User } from "../api";

type ActionType = "sapling" | "segregated_bin" | "cleanup" | "dumping_report";

const ACTIONS: { type: ActionType; en: string; hi: string }[] = [
  { type: "sapling", en: "🌱 Planted a sapling", hi: "🌱 पौधा लगाया" },
  { type: "segregated_bin", en: "♻️ Segregated waste", hi: "♻️ कचरा अलग किया" },
  { type: "cleanup", en: "🧹 Cleaned up a spot", hi: "🧹 जगह साफ़ की" },
  { type: "dumping_report", en: "⚠️ Report dumping", hi: "⚠️ कचरा फेंकने की रिपोर्ट" },
];

// Points when approved (SPEC §8; backend scoring.py is the source of truth).
const POINTS: Record<ActionType, number> = { sapling: 4, segregated_bin: 2, cleanup: 5, dumping_report: 2 };

/** Open the camera (camera only, no gallery) and return the photo as a Blob. */
async function takePhoto(): Promise<Blob> {
  const photo = await Camera.getPhoto({ source: CameraSource.Camera, resultType: CameraResultType.Uri, quality: 80 });
  return (await fetch(photo.webPath!)).blob();
}

export default function Act({ lang, user }: { lang: Lang; user: User }) {
  const [type, setType] = useState<ActionType | null>(null);
  const [before, setBefore] = useState<Blob | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<ActionResult | null>(null);
  const hi = lang === "hi";

  if (!Capacitor.isNativePlatform()) {
    return (
      <div className="card">
        <h2>{hi ? "कदम उठाएँ" : "Take action"}</h2>
        <p><strong>{hi ? "कार्य केवल Bio Mantra ऐप से ही जमा किए जा सकते हैं।" : "Actions can only be submitted from the Bio Mantra app."}</strong></p>
        <p className="muted">{hi ? "ऐप में लाइव कैमरा फ़ोटो + GPS से:" : "In the app, with a live camera photo + GPS:"}</p>
        <ul className="list">
          {ACTIONS.map((a) => (
            <li key={a.type} className="spread"><span>{hi ? a.hi : a.en}</span><strong>+{POINTS[a.type]}</strong></li>
          ))}
        </ul>
      </div>
    );
  }

  const reset = () => { setType(null); setBefore(null); setResult(null); setError(""); };

  /** Take the "before" photo of a cleanup. */
  const captureBefore = async () => {
    setError("");
    try { setBefore(await takePhoto()); } catch (e) { setError((e as Error).message); }
  };

  /** Take the (after) photo, read GPS, and POST everything to /actions. */
  const captureAndSubmit = async () => {
    if (!type) return;
    setError("");
    try {
      const photo = await takePhoto();
      setBusy(hi ? "स्थान लिया जा रहा है…" : "Getting location…");
      const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
      const form = new FormData();
      form.append("user_id", String(user.id));
      form.append("action_type", type);
      form.append("lat", String(pos.coords.latitude));
      form.append("lon", String(pos.coords.longitude));
      form.append("client_time", new Date().toISOString());
      form.append("photo", photo, "photo.jpg");
      if (type === "cleanup" && before) form.append("before_photo", before, "before.jpg");
      setBusy(hi ? "जाँच हो रही है…" : "Checking photo…");
      setResult(await api.submitAction(form));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };

  if (result) {
    return (
      <div className="card">
        <h2>{hi ? "नतीजा" : "Result"}</h2>
        <span className={`status ${result.status}`}>{result.status.replace("_", " ")}</span>
        <p><strong>+{result.points} {hi ? "अंक" : "points"}</strong>
          {result.confidence !== null && <span className="muted"> · AI confidence {result.confidence.toFixed(2)}</span>}</p>
        <ul>{result.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        {result.detections.length > 0 && (
          <>
            <div className="muted">{hi ? "AI ने देखा:" : "AI saw:"}</div>
            <ul>{result.detections.map((d, i) => <li key={i}>{d.name} ({d.conf.toFixed(2)})</li>)}</ul>
          </>
        )}
        <button className="btn" onClick={reset}>{hi ? "एक और" : "Do another"}</button>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>{hi ? "आपने क्या किया?" : "What did you do?"}</h2>
      <div className="grid2">
        {ACTIONS.map((a) => (
          <button key={a.type} className={type === a.type ? "bigbtn on" : "bigbtn"}
            onClick={() => { setType(a.type); setBefore(null); }}>
            {hi ? a.hi : a.en}
          </button>
        ))}
      </div>
      {type && (
        <div style={{ marginTop: 16 }} className="row">
          {type === "cleanup" && !before ? (
            <button className="btn lime" disabled={!!busy} onClick={captureBefore}>
              📷 {hi ? "1. पहले की फ़ोटो" : "1. Take BEFORE photo"}
            </button>
          ) : (
            <button className="btn lime" disabled={!!busy} onClick={captureAndSubmit}>
              📷 {type === "cleanup" ? (hi ? "2. बाद की फ़ोटो और जमा करें" : "2. Take AFTER photo & submit") : (hi ? "फ़ोटो लें और जमा करें" : "Take photo & submit")}
            </button>
          )}
        </div>
      )}
      {type === "cleanup" && before && <p className="muted">✓ {hi ? "पहले की फ़ोटो ली गई" : "Before photo taken"}</p>}
      {busy && <p className="muted">{busy}</p>}
      {error && <p className="error">{error}</p>}
      <p className="muted" style={{ marginTop: 16 }}>
        {hi ? "केवल लाइव कैमरा फ़ोटो। समय और GPS की जाँच सर्वर पर होती है।" : "Live camera photos only. Time and GPS are checked on the server."}
      </p>
    </div>
  );
}
