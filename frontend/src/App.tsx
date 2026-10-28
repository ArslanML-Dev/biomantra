// App layout: top bar, routes and the bottom nav (Home · Act · Leaderboard · Map).
import { useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import type { Lang } from "./api";
import { t } from "./i18n";
import Home from "./pages/Home";
import Act from "./pages/Act";
import Leaderboard from "./pages/Leaderboard";
import MapPage from "./pages/MapPage";

/** Read the saved language (defaults to English). */
function savedLang(): Lang {
  return localStorage.getItem("lang") === "hi" ? "hi" : "en";
}

export default function App() {
  const [lang, setLangState] = useState<Lang>(savedLang);
  const wide = ["/map", "/admin"].includes(useLocation().pathname);

  const setLang = (next: Lang) => {
    localStorage.setItem("lang", next);
    setLangState(next);
  };

  return (
    <div className={wide ? "shell wide" : "shell"}>
      <header className="topbar">
        <Link to="/" className="brand"><span>BM</span>Bio Mantra</Link>
        <nav className="toplinks">
          <Link to="/about">{t(lang, "about")}</Link>
          <Link to="/admin">{t(lang, "admin")}</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Home lang={lang} setLang={setLang} />} />
        <Route path="/act" element={<Act lang={lang} />} />
        <Route path="/leaderboard" element={<Leaderboard lang={lang} />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
      <nav className="bottomnav">
        <NavLink to="/" end>{t(lang, "home")}</NavLink>
        <NavLink to="/act">{t(lang, "act")}</NavLink>
        <NavLink to="/leaderboard">{t(lang, "leaderboard")}</NavLink>
        <NavLink to="/map">{t(lang, "map")}</NavLink>
      </nav>
    </div>
  );
}
