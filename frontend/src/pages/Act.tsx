import type { Lang, User } from "../api";

export default function Act(_props: { lang: Lang; user: User }) {
  return <div className="card"><h2>Act</h2><p className="muted">Coming next.</p></div>;
}
