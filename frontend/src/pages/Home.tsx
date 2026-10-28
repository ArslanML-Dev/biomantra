// Home: tomorrow's PM2.5 forecast card with reason, tip, disclaimer and the EN/हिं toggle.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Forecast, type Lang, type User } from "../api";
import { t } from "../i18n";

type Props = { lang: Lang; setLang: (l: Lang) => void; user: User | null; onSwitchUser: () => void };

export default function Home({ lang, setLang, user, onSwitchUser }: Props) {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    api.forecast(lang).then(setForecast).catch((e: Error) => setError(e.message));
  }, [lang]);

  return (
    <>
      <div className="spread" style={{ marginBottom: 12 }}>
        <span className="muted">
          {user && <>{t(lang, "hello")}, {user.name} · <button className="btn ghost" style={{ padding: "2px 8px" }} onClick={onSwitchUser}>{t(lang, "switchUser")}</button></>}
        </span>
        <div className="toggle">
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिं</button>
        </div>
      </div>

      <div className="card">
        {error && <p className="error">{error}</p>}
        {!forecast && !error && <p className="muted">{t(lang, "loading")}</p>}
        {forecast && (
          <>
            <div className="muted">{t(lang, "tomorrow")}</div>
            <div className="big">{forecast.pm25_tomorrow.toFixed(0)}</div>
            <span className="chip" style={{ background: forecast.color }}>{forecast.category}</span>
            <span className="muted" style={{ marginLeft: 10 }}>{t(lang, "now")}: {forecast.pm25_now.toFixed(0)}</span>
            <p><strong>{forecast.reason}</strong></p>
            <p>{forecast.tip}</p>
            <p className="muted"><em>{forecast.disclaimer}</em></p>
            <p className="muted" style={{ fontSize: "0.75rem" }}>
              LightGBM · test MAE {forecast.model.test_mae} µg/m³ · {new Date(forecast.generated_at).toLocaleString()}
            </p>
          </>
        )}
      </div>

      <div className="row">
        <Link to="/act" className="btn lime">{t(lang, "takeAction")}</Link>
        <Link to="/leaderboard" className="btn">{t(lang, "leaderboard")}</Link>
      </div>
    </>
  );
}
