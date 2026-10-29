// App layout: top bar, user picker gate, routes and the floating bottom nav (Home · Act · Leaderboard · Map).
import { useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import type { Lang, User } from "./api";
import { t } from "./i18n";
import { loadUser, saveUser } from "./user";
import { CameraIcon, GearIcon, HomeIcon, LeafIcon, MapIcon, TrophyIcon } from "./icons";
import Home from "./pages/Home";
import Act from "./pages/Act";
import Leaderboard from "./pages/Leaderboard";
import MapPage from "./pages/MapPage";
import UserPicker from "./pages/UserPicker";
import Admin from "./pages/Admin";
import About from "./pages/About";
import Settings from "./pages/Settings";

/** Read the saved language (defaults to English). */
function savedLang(): Lang {
  return localStorage.getItem("lang") === "hi" ? "hi" : "en";
}

export default function App() {
  const [lang, setLangState] = useState<Lang>(savedLang);
  const [user, setUserState] = useState<User | null>(loadUser);
  const path = useLocation().pathname;
  const wide = ["/map", "/admin"].includes(path);
  const needsUser = !user && ["/", "/act"].includes(path);

  const setLang = (next: Lang) => {
    localStorage.setItem("lang", next);
    setLangState(next);
  };
  const setUser = (next: User | null) => {
    saveUser(next);
    setUserState(next);
  };

  return (
    <div className={wide ? "shell wide" : "shell"}>
      <header className="topbar">
        <Link to="/" className="brand" aria-label="Bio Mantra home">
          <span className="mono"><LeafIcon /></span>
          <span className="word">Bio <em>Mantra</em></span>
        </Link>
        <nav className="toplinks">
          <NavLink to="/about">{t(lang, "about")}</NavLink>
          <NavLink to="/admin">{t(lang, "admin")}</NavLink>
          <NavLink to="/settings" className="gear" aria-label={t(lang, "settings")} title={t(lang, "settings")}><GearIcon /></NavLink>
        </nav>
      </header>
      {needsUser ? <UserPicker lang={lang} onPick={setUser} /> : (
        <Routes>
          <Route path="/" element={<Home lang={lang} setLang={setLang} user={user} onSwitchUser={() => setUser(null)} />} />
          <Route path="/act" element={<Act lang={lang} user={user!} />} />
          <Route path="/leaderboard" element={<Leaderboard lang={lang} />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/about" element={<About />} />
          <Route path="/settings" element={<Settings lang={lang} />} />
        </Routes>
      )}
      <nav className="bottomnav">
        <NavLink to="/" end><span className="ico"><HomeIcon /></span>{t(lang, "home")}</NavLink>
        <NavLink to="/act"><span className="ico"><CameraIcon /></span>{t(lang, "act")}</NavLink>
        <NavLink to="/leaderboard"><span className="ico"><TrophyIcon /></span>{t(lang, "leaderboard")}</NavLink>
        <NavLink to="/map"><span className="ico"><MapIcon /></span>{t(lang, "map")}</NavLink>
      </nav>
    </div>
  );
}
