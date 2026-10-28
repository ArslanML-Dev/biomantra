import type { Lang } from "../api";

export default function Act(_props: { lang: Lang; setLang?: (l: Lang) => void }) {
  return <div className="card"><h2>Act</h2><p className="muted">Coming next.</p></div>;
}
