"""Finish docs/report_pack: folder tree, git log, INDEX.md (key numbers read from real files).

Usage (from backend/):
    python scripts/finalize_report_pack.py
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PACK = ROOT / "docs" / "report_pack"
SKIP_DIRS = {"node_modules", ".venv", "data", "build", ".git", "__pycache__", ".pytest_cache", "dist", ".gradle", ".idea"}
SKIP_PATHS = {Path("frontend/android/build"), Path("frontend/android/app/build"),
              Path("frontend/android/app/src/main/assets/public")}


def tree(folder: Path, prefix: str = "") -> list[str]:
    """Text tree of folder, skipping build/dependency/data folders."""
    lines = []
    entries = sorted((p for p in folder.iterdir()
                      if p.name not in SKIP_DIRS and p.relative_to(ROOT) not in SKIP_PATHS),
                     key=lambda p: (p.is_file(), p.name.lower()))
    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        lines.append(f"{prefix}{'└── ' if last else '├── '}{entry.name}{'/' if entry.is_dir() else ''}")
        if entry.is_dir():
            lines += tree(entry, prefix + ("    " if last else "│   "))
    return lines


def describe(path: Path) -> str:
    """One-line description of a pack file (first markdown heading, or a fixed label)."""
    labels = {".png": "figure / screenshot (PNG)", ".mmd": "Mermaid diagram source", ".json": "JSON data",
              ".jpg": "input photo", ".txt": "text output"}
    if path.suffix == ".md":
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return labels.get(path.suffix, path.suffix)


def key_numbers() -> list[str]:
    """Key numbers taken from the real files in the pack."""
    m2 = json.loads((PACK / "data" / "metrics_v2.json").read_text())
    m1 = json.loads((PACK / "data" / "metrics_v1.json").read_text())
    summary = (PACK / "data" / "dataset_summary.md").read_text(encoding="utf-8")
    rows = re.search(r"Rows: \*\*([\d,]+)\*\* hourly rows, (\S+) \S+ → (\S+)", summary)
    splits = re.findall(r"\| (train|val|test) \| [^|]+ \| ([\d,]+) \| (\S+) \S+ \| (\S+) \S+ \|", summary)
    pytest_line = [l for l in (PACK / "raw" / "pytest_v_full.txt").read_text(encoding="utf-8").splitlines()
                   if " passed" in l][-1].strip("= ")
    n_fig = len(list((PACK / "figures").glob("*.png")))
    n_shot = len(list((PACK / "screenshots").glob("*.png")))

    def fmt(s: dict) -> str:
        return (f"MAE {s['mae']}, RMSE {s['rmse']}, R² {s['r2']}, category accuracy {s['acc_cat']}, "
                f"macro-F1 {s['macro_f1']}, recall Poor+ {s['recall_poor_plus']}")

    return [
        f"- **Model v2 (deployed):** LightGBM, target = {m2['model']['target_label']}, past + next-24 h weather. Test: {fmt(m2['lightgbm'])}.",
        f"  - Same target, baselines: linear MAE {m2['linear']['mae']}, persistence MAE {m2['persistence']['mae']}.",
        f"- **Model v1 (original):** LightGBM, target = PM2.5 at t+24 h, past features. Test: {fmt(m1['lightgbm'])}.",
        f"  - v1 baselines: linear MAE {m1['linear']['mae']}, persistence MAE {m1['persistence']['mae']}.",
        f"- **Test period:** {m2['test_period'][0]} → {m2['test_period'][1]}. v2 scores are an upper bound (actual next-day weather was used as a stand-in for a forecast).",
        f"- **Data:** {rows.group(1)} hourly rows, {rows.group(2)} → {rows.group(3)} (UTC), Open-Meteo (modelled).",
        f"  - {m2['rows']:,} rows were usable by every model.",
        "- **Split (time order):** " + "; ".join(f"{n} {c} ({a} → {b})" for n, c, a, b in splits) + ".",
        f"- **Tests:** {pytest_line} (pytest; YOLO mocked).",
        "- **Fraud test:** 5 of 8 cases real, 3 PENDING (need phone photos).",
        f"- **Figures:** {n_fig} (300 dpi, black-and-white safe). **Screenshots:** {n_shot} (headless, phone and laptop size, sample database).",
    ]


def main() -> None:
    """Write docs/folder_tree.txt, docs/git_log.txt and INDEX.md."""
    tree_lines = [ROOT.name + "/", *tree(ROOT)]
    (PACK / "docs" / "folder_tree.txt").write_text(
        "Project folder tree (excludes node_modules, .venv, data, build, android/build, .git, __pycache__, "
        ".pytest_cache, dist, .gradle and the generated android assets/public copy)\n\n" + "\n".join(tree_lines) + "\n",
        encoding="utf-8")
    log = subprocess.run(["git", "log", "--oneline"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    (PACK / "docs" / "git_log.txt").write_text(
        "Full one-line git log (newest first). The final 'docs: complete report pack' commit is made after this file "
        "is written, so it isn't listed.\n\n" + log, encoding="utf-8")

    files = sorted(p for p in PACK.rglob("*") if p.is_file() and p.name != "INDEX.md")
    lines = ["# Bio Mantra report pack: index", "", "## Key numbers (read from the files in this pack)", "",
             *key_numbers(), "", f"## Files ({len(files) + 1}, including this index)", ""]
    for p in files:
        lines.append(f"- `{p.relative_to(PACK).as_posix()}`: {describe(p)}")
    (PACK / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"tree: {len(tree_lines)} lines, git log: {len(log.splitlines())} commits, INDEX: {len(files) + 1} files")


if __name__ == "__main__":
    main()
