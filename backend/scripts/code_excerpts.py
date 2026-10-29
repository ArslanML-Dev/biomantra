"""Copy exact source excerpts into docs/report_pack/code/ (report pack). Nothing is retyped by hand.

Usage (from backend/):
    python scripts/code_excerpts.py
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "report_pack" / "code"

# (output name, title, source file, python names OR [(start text, end text)] for other files, None = whole file)
EXCERPTS = [
    ("01_cpcb_categories.md", "CPCB bands and pm25_to_category", "backend/app/forecast.py",
     ["LAGS", "HORIZON_H", "WINTER_MONTHS", "BANDS", "CATEGORIES", "pm25_to_category"]),
    ("02_build_features.md", "Feature building (past features, next-24 h weather, targets)", "backend/app/forecast.py",
     ["future_weather", "next24_mean", "make_target", "build_features"]),
    ("03_training_main_loop.md", "Training: one configuration, and the main experiment loop", "backend/scripts/train_forecast.py",
     ["main"]),
    ("04_shap_reason.md", "SHAP reason sentence (EN/HI)", "backend/app/forecast.py",
     ["feature_group", "top_reasons", "make_reason"]),
    ("05_tips_and_live_prediction.md", "Health tips, disclaimer and live SHAP prediction", "backend/app/forecast.py",
     ["TIPS", "DISCLAIMER", "current_row", "predict_core"]),
    ("06_verify_checks.md", "Anti-fraud checks: clock, geofence, duplicate (pHash)", "backend/app/verify.py",
     ["check_clock", "haversine_km", "check_geofence", "compute_phash", "check_duplicate"]),
    ("07_verify_ai_and_decide.md", "AI check (YOLOv8n, COCO stand-in classes) and the decision thresholds", "backend/app/verify.py",
     ["litter_confs", "ai_check", "decide"]),
    ("08_scoring_rules.md", "Scoring rules: points, weekly window, hotspots", "backend/app/scoring.py",
     ["POINTS", "SAPLING_NOTE", "WEEKLY_GOAL", "HOTSPOT_CLOSE_KM", "week_start", "close_nearest_hotspot", "apply_approval"]),
    ("09_actions_endpoint.md", "POST /actions endpoint", "backend/app/main.py", ["create_action"]),
    ("10_act_camera_gps.md", "React Act screen: live camera + GPS + submit", "frontend/src/pages/Act.tsx",
     [("/** Open the camera", "}"), ("  /** Take the (after) photo", "  };")]),
    ("11_capacitor_config.md", "Capacitor configuration", "frontend/capacitor.config.ts", None),
]


def python_ranges(source: str, names: list[str]) -> list[tuple[int, int]]:
    """Line ranges (1-based) of the given top-level functions/constants; neighbours are merged."""
    spans = []
    for node in ast.parse(source).body:
        name = getattr(node, "name", None) or (
            node.targets[0].id if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) else None)
        if name in names:
            start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
            spans.append((start, node.end_lineno))
    if len(spans) != len(names):
        raise ValueError(f"not all names found: {names}")
    merged = [sorted(spans)[0]]
    for a, b in sorted(spans)[1:]:
        if a - merged[-1][1] <= 3:  # only blank lines between them
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def text_ranges(lines: list[str], markers: list[tuple[str, str]]) -> list[tuple[int, int]]:
    """For each (start text, end text): from the line starting with start text up to the end-text line."""
    ranges = []
    for start_text, end_text in markers:
        start = next(i for i, line in enumerate(lines) if line.startswith(start_text))
        end = next(i for i, line in enumerate(lines) if i > start and line.startswith(end_text))
        ranges.append((start + 1, end + 1))
    return ranges


def main() -> None:
    """Write one markdown file per excerpt and print the line counts."""
    OUT.mkdir(parents=True, exist_ok=True)
    for out_name, title, rel, spec in EXCERPTS:
        source = (ROOT / rel).read_text(encoding="utf-8")
        lines = source.splitlines()
        if spec is None:
            ranges = [(1, len(lines))]
        elif isinstance(spec[0], str):
            ranges = python_ranges(source, spec)
        else:
            ranges = text_ranges(lines, spec)
        lang = "python" if rel.endswith(".py") else "tsx" if rel.endswith(".tsx") else "ts"
        total = sum(b - a + 1 for a, b in ranges)
        parts = [f"# {title}", "", f"Source: `{rel}` ({total} lines in total), copied unchanged.", ""]
        for a, b in ranges:
            parts += [f"Lines {a}–{b}:", "", f"```{lang}", *lines[a - 1:b], "```", ""]
        (OUT / out_name).write_text("\n".join(parts), encoding="utf-8")
        where = ", ".join(f"{a}-{b}" for a, b in ranges)
        print(f"{out_name:<34} {rel}:{where}  ({total} lines)")


if __name__ == "__main__":
    main()
