// Settings: the backend "Server URL" saved on this device, with a Test connection button.
import { useState } from "react";
import { apiUrl, normalizeServerUrl, saveServerUrl, testServer, type Lang } from "../api";

export default function Settings({ lang }: { lang: Lang }) {
  const hi = lang === "hi";
  const [url, setUrl] = useState(apiUrl());
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  /** Check the typed address answers /health. */
  const test = async () => {
    setBusy(true);
    const ok = await testServer(url);
    setBusy(false);
    setMessage(ok
      ? { ok, text: hi ? `✓ जुड़ गया: ${normalizeServerUrl(url)}` : `✓ Connected to ${normalizeServerUrl(url)}` }
      : { ok, text: hi ? "✗ सर्वर नहीं मिला। पता, Wi-Fi और लैपटॉप पर start_demo.ps1 जाँचें।" : "✗ No answer. Check the address, that the phone is on the same Wi-Fi, and that start_demo.ps1 is running." });
  };

  /** Save the address on this device. */
  const save = () => {
    saveServerUrl(url);
    setUrl(apiUrl());
    setMessage({ ok: true, text: hi ? "सेव हो गया।" : "Saved on this device." });
  };

  /** Forget the saved address and use the built-in default. */
  const reset = () => {
    saveServerUrl("");
    setUrl(apiUrl());
    setMessage({ ok: true, text: hi ? "डिफ़ॉल्ट पता इस्तेमाल होगा।" : "Using the default address." });
  };

  return (
    <div className="card">
      <h2>{hi ? "सेटिंग्स" : "Settings"}</h2>
      <label htmlFor="server" className="muted">{hi ? "सर्वर URL" : "Server URL"}</label>
      <input id="server" inputMode="url" autoCapitalize="off" autoCorrect="off" spellCheck={false}
        placeholder="http://192.168.1.19:8000" value={url} onChange={(e) => { setUrl(e.target.value); setMessage(null); }} />
      <p className="muted">{hi
        ? "लैपटॉप पर start_demo.ps1 चलाएँ और वहाँ दिखाया गया पता यहाँ लिखें।"
        : "Run start_demo.ps1 on the laptop and type the address it shows here."}</p>
      <div className="row">
        <button className="btn ghost" disabled={busy || !url.trim()} onClick={test}>{busy ? "…" : hi ? "कनेक्शन जाँचें" : "Test connection"}</button>
        <button className="btn" disabled={!url.trim()} onClick={save}>{hi ? "सेव करें" : "Save"}</button>
      </div>
      {message && <p className={message.ok ? "ok" : "error"}>{message.text}</p>}
      <button className="linkbtn" onClick={reset}>{hi ? "डिफ़ॉल्ट पर लौटें" : "Reset to default"}</button>
    </div>
  );
}
