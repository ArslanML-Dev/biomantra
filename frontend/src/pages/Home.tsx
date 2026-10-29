// Home: tomorrow's PM2.5 forecast card with reason, tip, disclaimer and the EN/हिं toggle.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Forecast, type Lang, type User } from "../api";
import { categoryName, t } from "../i18n";
import { ArrowIcon } from "../icons";

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
      <div className="spread" style={{ margin: "4px 0 16px" }}>
        <span className="muted greet">
          {user && <><span>{t(lang, "hello")}, <strong>{user.name}</strong></span>
            <button className="linkbtn" onClick={onSwitchUser}>{t(lang, "switchUser")}</button></>}
        </span>
        <div className="toggle">
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>EN</button>
          <button className={lang === "hi" ? "on" : ""} onClick={() => setLang("hi")}>हिं</button>
        </div>
      </div>

      <div className="card forecast" style={forecast ? ({ "--cat": forecast.color } as React.CSSProperties) : undefined}>
        <div className="eyebrow">{t(lang, "tomorrow")}</div>
        {error && <p className="error">{error}</p>}
        {!forecast && !error && <p className="muted">{t(lang, "loading")}</p>}
        {forecast && (
          <>
            <div className="big">{forecast.pm25_tomorrow.toFixed(0)}<small>µg/m³</small></div>
            <span className="chip"><span className="dot" />{categoryName(lang, forecast.category)}</span>
            <div className="stats">
              <div className="stat"><div className="v">{forecast.pm25_now.toFixed(0)}</div><div className="k">{t(lang, "now")}</div></div>
              <div className="stat"><div className="v">±{forecast.model.test_mae.toFixed(0)}</div><div className="k">{t(lang, "typicalError")}</div></div>
            </div>
            <hr className="rule" />
            <p className="reason">{forecast.reason}</p>
            <p className="tip">{forecast.tip}</p>
            <p className="fineprint">
              {forecast.disclaimer} · LightGBM · {new Date(forecast.generated_at).toLocaleString()}
            </p>
          </>
        )}
      </div>

      <div className="row">
        <Link to="/act" className="btn gold">{t(lang, "takeAction")} <ArrowIcon /></Link>
        <Link to="/leaderboard" className="btn">{t(lang, "leaderboard")}</Link>
      </div>
    </>
  );
}
