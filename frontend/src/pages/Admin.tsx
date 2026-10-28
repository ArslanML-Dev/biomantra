// Admin: enter the token (kept in sessionStorage), then approve/reject the needs_review queue.
import { useCallback, useEffect, useState } from "react";
import { api, uploadUrl, type ReviewItem } from "../api";

// COCO classes the AI check uses for each action type (highlighted in the detection list).
const LITTER = ["bottle", "cup", "bowl", "wine glass", "fork", "knife", "spoon"];
const KEY_CLASSES: Record<string, string[]> = {
  sapling: ["potted plant"], segregated_bin: LITTER, cleanup: LITTER, dumping_report: LITTER,
};

export default function Admin() {
  const [token, setToken] = useState(() => sessionStorage.getItem("adminToken") ?? "");
  const [draft, setDraft] = useState("");
  const [reviewer, setReviewer] = useState("coordinator");
  const [queue, setQueue] = useState<ReviewItem[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    if (!token) return;
    setError("");
    api.reviewQueue(token).then(setQueue).catch((e: Error) => {
      setError(e.message);
      if (e.message.startsWith("401")) { sessionStorage.removeItem("adminToken"); setToken(""); }
    });
  }, [token]);

  useEffect(load, [load]);

  /** Approve or reject one action, then reload the queue. */
  const decide = async (id: number, decision: "approve" | "reject") => {
    try { await api.review(id, decision, reviewer, token); load(); } catch (e) { setError((e as Error).message); }
  };

  if (!token) {
    return (
      <form className="card" onSubmit={(e) => { e.preventDefault(); sessionStorage.setItem("adminToken", draft); setToken(draft); }}>
        <h2>Admin review</h2>
        {error && <p className="error">{error}</p>}
        <p><input type="password" placeholder="Admin token" value={draft} onChange={(e) => setDraft(e.target.value)} /></p>
        <button className="btn" type="submit">Open review queue</button>
      </form>
    );
  }

  return (
    <>
      <div className="adminhead">
        <h2>Review queue ({queue?.length ?? "…"})</h2>
        <div className="row">
          <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} aria-label="Reviewer name" placeholder="Reviewer name" />
          <button className="btn ghost" onClick={load}>Refresh</button>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {queue?.length === 0 && <p className="muted">Nothing waiting for review.</p>}
      <div className="reviewgrid">
        {queue?.map((item) => (
          <div className="card" key={item.id}>
            <div className="spread"><strong>#{item.id} {item.action_type}</strong><span className="muted">{item.user_name}</span></div>
            {item.before_photo_url && <><div className="muted">Before</div><img className="photo" src={uploadUrl(item.before_photo_url)} alt="before" /></>}
            {item.before_photo_url && <div className="muted">After</div>}
            <img className="photo" src={uploadUrl(item.photo_url)} alt="submitted" />
            <p className="muted">AI confidence <strong>{item.confidence?.toFixed(2)}</strong> · {new Date(item.server_time).toLocaleString()}</p>
            <ul className="tags">
              {item.detections.map((d, i) => (
                <li key={i} className={KEY_CLASSES[item.action_type]?.includes(d.name) ? "key" : ""}>{d.name} {d.conf.toFixed(2)}</li>
              ))}
            </ul>
            <div className="row">
              <button className="btn lime" onClick={() => decide(item.id, "approve")}>Approve</button>
              <button className="btn" onClick={() => decide(item.id, "reject")}>Reject</button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
