// First-launch "Who are you?" screen, listing users from /meta.
import { useEffect, useState } from "react";
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
      <h2>{t(lang, "whoAreYou")}</h2>
      {error && <p className="error">{error}</p>}
      {!users.length && !error && <p className="muted">{t(lang, "loading")}</p>}
      <ul className="list">
        {users.map((u) => (
          <li key={u.id}>
            <button className="btn ghost" style={{ width: "100%" }} onClick={() => onPick(u)}>
              {u.name} · {u.institution}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
