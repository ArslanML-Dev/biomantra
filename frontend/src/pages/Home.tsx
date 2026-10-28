import type { Lang } from "../api";

export default function Home(_props: { lang: Lang; setLang?: (l: Lang) => void }) {
  return <div className="card"><h2>Home</h2><p className="muted">Coming next.</p></div>;
}
