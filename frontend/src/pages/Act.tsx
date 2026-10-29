// Act: pick an action, take a LIVE camera photo (never the gallery) + GPS, submit, show the result.
// App: native camera (Capacitor). Website: live browser camera preview (getUserMedia), no file picker.
import { useEffect, useRef, useState, type ReactElement } from "react";
import { Capacitor } from "@capacitor/core";
import { Camera, CameraResultType, CameraSource } from "@capacitor/camera";
import { Geolocation } from "@capacitor/geolocation";
import { api, type ActionResult, type Lang, type User } from "../api";
import { t } from "../i18n";
import { AlertIcon, CameraIcon, LeafIcon, RecycleIcon, SparkleIcon } from "../icons";

type ActionType = "sapling" | "segregated_bin" | "cleanup" | "dumping_report";
type Stage = "before" | "after";

const ACTIONS: { type: ActionType; en: string; hi: string; icon: () => ReactElement }[] = [
  { type: "sapling", en: "Planted a sapling", hi: "पौधा लगाया", icon: LeafIcon },
  { type: "segregated_bin", en: "Segregated waste", hi: "कचरा अलग किया", icon: RecycleIcon },
  { type: "cleanup", en: "Cleaned up a spot", hi: "जगह साफ़ की", icon: SparkleIcon },
  { type: "dumping_report", en: "Report dumping", hi: "कचरा फेंकने की रिपोर्ट", icon: AlertIcon },
];

// Points when approved (SPEC §8; backend scoring.py is the source of truth).
const POINTS: Record<ActionType, number> = { sapling: 4, segregated_bin: 2, cleanup: 5, dumping_report: 2 };
const native = Capacitor.isNativePlatform();

/** App only: open the native camera (camera only, no gallery) and return the photo as a Blob. */
async function nativePhoto(): Promise<Blob> {
  const photo = await Camera.getPhoto({ source: CameraSource.Camera, resultType: CameraResultType.Uri, quality: 80 });
  return (await fetch(photo.webPath!)).blob();
}

/** Website only: live camera preview with a capture button (no file or gallery picker). */
function WebCamera({ hi, onCapture, onCancel }: { hi: boolean; onCapture: (b: Blob) => void; onCancel: () => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let stream: MediaStream | undefined;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError(hi ? "कैमरा केवल सुरक्षित (https) पेज पर चलता है।" : "The camera only works on a secure (https) page, e.g. biomantra.vercel.app.");
      return;
    }
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: false })
      .then((s) => {
        stream = s;
        if (video.current) { video.current.srcObject = s; video.current.play().catch(() => undefined); }
      })
      .catch(() => setError(hi ? "कैमरा की अनुमति दें और फिर से कोशिश करें।" : "Please allow camera access in your browser and try again."));
    return () => stream?.getTracks().forEach((track) => track.stop());
  }, [hi]);

  /** Grab the current video frame as a JPEG. */
  const capture = () => {
    const v = video.current;
    if (!v || !v.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;
    canvas.getContext("2d")!.drawImage(v, 0, 0);
    canvas.toBlob((b) => b && onCapture(b), "image/jpeg", 0.88);
  };

  return (
    <div className="camera">
      {error ? <p className="error" style={{ padding: 16 }}>{error}</p> : <video ref={video} playsInline muted />}
      <div className="row">
        <button className="btn ghost" onClick={onCancel}>{hi ? "रद्द करें" : "Cancel"}</button>
        {!error && <button className="btn gold" onClick={capture}><CameraIcon /> {hi ? "फ़ोटो लें" : "Capture"}</button>}
      </div>
    </div>
  );
}

export default function Act({ lang, user }: { lang: Lang; user: User }) {
  const [type, setType] = useState<ActionType | null>(null);
  const [before, setBefore] = useState<Blob | null>(null);
  const [camera, setCamera] = useState<Stage | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<ActionResult | null>(null);
  const [preview, setPreview] = useState("");
  const hi = lang === "hi";

  const reset = () => { setType(null); setBefore(null); setCamera(null); setResult(null); setError(""); setPreview(""); };

  /** Read GPS, then POST the photo (and the before photo for a cleanup) to /actions. */
  const submit = async (photo: Blob) => {
    if (!type) return;
    setError("");
    setPreview(URL.createObjectURL(photo));
    try {
      setBusy(hi ? "स्थान लिया जा रहा है…" : "Getting your location…");
      const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true, timeout: 20000 });
      const form = new FormData();
      form.append("user_id", String(user.id));
      form.append("action_type", type);
      form.append("lat", String(pos.coords.latitude));
      form.append("lon", String(pos.coords.longitude));
      form.append("client_time", new Date().toISOString());
      form.append("photo", photo, "photo.jpg");
      if (type === "cleanup" && before) form.append("before_photo", before, "before.jpg");
      setBusy(hi ? "AI फ़ोटो जाँच रहा है…" : "Verifying your photo…");
      setResult(await api.submitAction(form));
    } catch (e) {
      const msg = (e as Error).message || "";
      setError(/denied|permission/i.test(msg)
        ? (hi ? "कृपया स्थान (location) की अनुमति दें।" : "Please allow location access, then try again.")
        : msg);
    } finally {
      setBusy("");
    }
  };

  /** Handle a captured photo for the given stage. */
  const handlePhoto = (stage: Stage, photo: Blob) => {
    setCamera(null);
    if (stage === "before") setBefore(photo);
    else void submit(photo);
  };

  /** Open the camera for a stage: native camera in the app, live preview on the website. */
  const open = async (stage: Stage) => {
    setError("");
    if (!native) { setCamera(stage); return; }
    try { handlePhoto(stage, await nativePhoto()); } catch (e) { setError((e as Error).message); }
  };

  if (result) {
    return (
      <div className="card">
        <div className="eyebrow">{hi ? "नतीजा" : "Verification result"}</div>
        <div className="spread" style={{ margin: "6px 0 14px" }}>
          <span className={`status ${result.status}`}>{result.status.replace("_", " ")}</span>
          <span className="pts"><b>+{result.points}</b>{hi ? "अंक" : "points"}</span>
        </div>
        {preview && <img className="photo" src={preview} alt="" />}
        <ul className="reasons">{result.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        {result.confidence !== null && <p className="muted">AI confidence {result.confidence.toFixed(2)}</p>}
        {result.detections.length > 0 && (
          <ul className="tags">{result.detections.slice(0, 10).map((d, i) => <li key={i}>{d.name} {d.conf.toFixed(2)}</li>)}</ul>
        )}
        <button className="btn gold" style={{ width: "100%", marginTop: 8 }} onClick={reset}>{hi ? "एक और" : "Record another"}</button>
      </div>
    );
  }

  const nextStage: Stage = type === "cleanup" && !before ? "before" : "after";
  return (
    <div className="card">
      <div className="eyebrow">{hi ? "कदम उठाएँ" : "Take action"}</div>
      <h2>{hi ? "आपने क्या किया?" : "What did you do?"}</h2>
      <div className="grid2">
        {ACTIONS.map((a) => (
          <button key={a.type} className={type === a.type ? "bigbtn on" : "bigbtn"}
            onClick={() => { setType(a.type); setBefore(null); setCamera(null); setError(""); }}>
            <span className="ic"><a.icon /></span>
            <span className="t">{hi ? a.hi : a.en}</span>
            <span className="p">+{POINTS[a.type]} {hi ? "अंक" : "points"}</span>
          </button>
        ))}
      </div>
      {type && camera && <WebCamera hi={hi} onCapture={(b) => handlePhoto(camera, b)} onCancel={() => setCamera(null)} />}
      {type && !camera && (
        <div className="row" style={{ marginTop: 20 }}>
          <button className="btn gold" disabled={!!busy} onClick={() => open(nextStage)}>
            <CameraIcon />
            {nextStage === "before"
              ? (hi ? "1. पहले की फ़ोटो" : "1 · Photo before cleaning")
              : type === "cleanup"
                ? (hi ? "2. बाद की फ़ोटो और जमा करें" : "2 · Photo after & submit")
                : (hi ? "फ़ोटो लें और जमा करें" : "Take photo & submit")}
          </button>
        </div>
      )}
      {type === "cleanup" && before && !camera && <p className="ok" style={{ marginTop: 12 }}>✓ {hi ? "पहले की फ़ोटो ली गई" : "Before photo captured"}</p>}
      {busy && <p className="muted" style={{ marginTop: 12 }}>{busy}</p>}
      {error && <p className="error" style={{ marginTop: 12 }}>{error}</p>}
      <p className="fineprint">{t(lang, "liveOnly")}</p>
    </div>
  );
}
