// App layout: top bar, user picker gate, routes and the bottom nav (Home · Act · Leaderboard · Map).
import { useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import type { Lang, User } from "./api";
import { t } from "./i18n";
import { loadUser, saveUser } from "./user";
import Home from "./pages/Home";
import Act from "./pages/Act";
import Leaderboard from "./pages/Leaderboard";
import MapPage from "./pages/MapPage";
import UserPicker from "./pages/UserPicker";
import Admin from "./pages/Admin";

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
        <Link to="/" className="brand"><span>BM</span>Bio Mantra</Link>
        <nav className="toplinks">
          <Link to="/about">{t(lang, "about")}</Link>
          <Link to="/admin">{t(lang, "admin")}</Link>
        </nav>
      </header>
      {needsUser ? <UserPicker lang={lang} onPick={setUser} /> : (
        <Routes>
          <Route path="/" element={<Home lang={lang} setLang={setLang} user={user} onSwitchUser={() => setUser(null)} />} />
          <Route path="/act" element={<Act lang={lang} user={user!} />} />
          <Route path="/leaderboard" element={<Leaderboard lang={lang} />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      )}
      <nav className="bottomnav">
        <NavLink to="/" end>{t(lang, "home")}</NavLink>
        <NavLink to="/act">{t(lang, "act")}</NavLink>
        <NavLink to="/leaderboard">{t(lang, "leaderboard")}</NavLink>
        <NavLink to="/map">{t(lang, "map")}</NavLink>
      </nav>
    </div>
  );
}
