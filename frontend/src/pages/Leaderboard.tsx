// Leaderboard: Users / Institutions tabs, ranked list and weekly goal progress bars.
import { useEffect, useState } from "react";
import { api, type Lang, type LeaderRow } from "../api";
import { t } from "../i18n";

type Scope = "users" | "institutions";

export default function Leaderboard({ lang }: { lang: Lang }) {
  const [scope, setScope] = useState<Scope>("institutions");
  const [rows, setRows] = useState<LeaderRow[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setRows(null);
    setError("");
    api.leaderboard(scope).then(setRows).catch((e: Error) => setError(e.message));
  }, [scope]);

  return (
    <div className="card">
      <div className="eyebrow">{t(lang, "thisWeek")} · {t(lang, "goal")} 50</div>
      <h2>{t(lang, "leaderboard")}</h2>
      <div className="tabs">
        <button className={scope === "institutions" ? "on" : ""} onClick={() => setScope("institutions")}>{t(lang, "institutions")}</button>
        <button className={scope === "users" ? "on" : ""} onClick={() => setScope("users")}>{t(lang, "users")}</button>
      </div>
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p className="muted">{t(lang, "loading")}</p>}
      <ol className="list">
        {rows?.map((r) => (
          <li key={r.id}>
            <div className="spread">
              <span className="who"><span className={r.rank <= 3 ? "rank top" : "rank"}>{r.rank}</span><strong>{r.name}</strong></span>
              <span className="pts"><b>{r.points_week}</b>{t(lang, "thisWeek")} · {r.points_total} {t(lang, "total")}</span>
            </div>
            <div className="bar" title={`${Math.round(r.progress * 100)}%`}>
              <div style={{ width: `${r.progress * 100}%` }} />
            </div>
            <div className="muted" style={{ marginTop: 6, fontSize: "0.74rem" }}>
              {r.points_week} / {r.goal} {t(lang, "goal")} · {Math.round(r.progress * 100)}%
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
