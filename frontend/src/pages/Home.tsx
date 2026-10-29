// Home: tomorrow's PM2.5 forecast (hero card + CPCB scale), the reason and tip, and the EN/हिं toggle.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Forecast, type Lang, type User } from "../api";
import { categoryName, t } from "../i18n";
import { ArrowIcon, LeafIcon } from "../icons";

type Props = { lang: Lang; setLang: (l: Lang) => void; user: User | null; onSwitchUser: () => void };

// CPCB PM2.5 bands (upper bound, colour), same as backend forecast.BANDS. Shown as six equal segments.
const BANDS: [number, string][] = [[30, "#00B050"], [60, "#92D050"], [90, "#FFFF00"], [120, "#FF9900"], [250, "#FF0000"], [400, "#C00000"]];

/** Position (0–100 %) of a PM2.5 value on the six equal-width CPCB segments. */
function scalePos(pm: number): number {
  let lo = 0;
  for (let i = 0; i < BANDS.length; i++) {
    const hi = BANDS[i][0];
    if (pm <= hi || i === BANDS.length - 1) return ((i + Math.min(1, (pm - lo) / (hi - lo))) / BANDS.length) * 100;
    lo = hi;
  }
  return 100;
}

export default function Home({ lang, setLang, user, onSwitchUser }: Props) {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    api.forecast(lang).then(setForecast).catch((e: Error) => setError(e.message));
  }, [lang]);

  return (
    <>
      <div className="spread" style={{ margin: "2px 0 14px" }}>
        <span className="muted greet">
          {user && <><span>{t(lang, "hello")}, <strong style={{ color: "var(--ink)" }}>{user.name}</strong></span>
            <button className="linkbtn" onClick={onSwitchUser}>{t(lang, "switchUser")}</button></>}
        </span>
        <div className="toggle">
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिं</button>
        </div>
      </div>

      <div className="card forecast" style={forecast ? ({ "--cat": forecast.color } as React.CSSProperties) : undefined}>
        <div className="eyebrow">{t(lang, "tomorrow")}</div>
        {error && <p className="error" style={{ color: "#ffb4a8" }}>{error}</p>}
        {!forecast && !error && <p className="muted">{t(lang, "loading")}</p>}
        {forecast && (
          <>
            <div className="big">{forecast.pm25_tomorrow.toFixed(0)}<small>µg/m³ PM2.5</small></div>
            <span className="chip"><span className="dot" />{categoryName(lang, forecast.category)}</span>
            <div className="scale">
              {BANDS.map(([, c]) => <span key={c} style={{ background: c }} />)}
              <i style={{ left: `${scalePos(forecast.pm25_tomorrow)}%` }} />
            </div>
            <div className="scalelabels"><span>{categoryName(lang, "Good")}</span><span>{categoryName(lang, "Severe")}</span></div>
            <div className="stats">
              <div className="stat"><div className="v">{forecast.pm25_now.toFixed(0)}</div><div className="k">{t(lang, "now")} · µg/m³</div></div>
              <div className="stat"><div className="v">±{forecast.model.test_mae.toFixed(0)}</div><div className="k">{t(lang, "typicalError")}</div></div>
            </div>
          </>
        )}
      </div>

      {forecast && (
        <div className="card">
          <div className="eyebrow">{lang === "hi" ? "क्यों" : "Why"}</div>
          <p className="reason">{forecast.reason}</p>
          <p className="tip"><span style={{ color: "var(--good)", flexShrink: 0 }}><LeafIcon /></span><span>{forecast.tip}</span></p>
          <p className="fineprint">
            {forecast.disclaimer} · LightGBM · {new Date(forecast.generated_at).toLocaleString()}
          </p>
        </div>
      )}

      <div className="row">
        <Link to="/act" className="btn gold">{t(lang, "takeAction")} <ArrowIcon /></Link>
        <Link to="/leaderboard" className="btn">{t(lang, "leaderboard")}</Link>
      </div>
    </>
  );
}
