import type { Lang } from "../api";

export default function Leaderboard(_props: { lang: Lang; setLang?: (l: Lang) => void }) {
  return <div className="card"><h2>Leaderboard</h2><p className="muted">Coming next.</p></div>;
}
