// First-launch "Who are you?" screen, listing users from /meta.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Lang, type User } from "../api";
import { t } from "../i18n";

export default function UserPicker({ lang, onPick }: { lang: Lang; onPick: (u: User) => void }) {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.meta().then((m) => setUsers(m.users)).catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div className="card">
      <div className="eyebrow">{lang === "hi" ? "स्वागत है" : "Welcome"}</div>
      <h2>{t(lang, "whoAreYou")}</h2>
      {error && <p className="error">{error} <Link to="/settings">{t(lang, "settings")} →</Link></p>}
      {!users.length && !error && <p className="muted">{t(lang, "loading")}</p>}
      <ul className="list plain">
        {users.map((u) => (
          <li key={u.id}>
            <button className="person" onClick={() => onPick(u)}>
              <span className="n">{u.name}</span><span className="i">{u.institution}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
