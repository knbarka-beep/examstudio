"""Build the public data for the site from bank/ and copy the student data files.

Run after build_exams.py: py scripts\\build_site.py

Writes docs/data/questions.json, exams.json, interpretation.json, datasets.json and config.json (created if
missing; values already there are kept). Solution fields are left out unless config.json has
"showReferenceSolutions": true; then they go into a "reference" object on each question.
Data files under 50 MB are copied to docs/files/; larger ones are zipped into release-assets/ and linked to the
GitHub release datasets-v1. Copying needs materials/; without it only the JSON is rebuilt.
"""
import datetime
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "bank"
DATA = ROOT / "docs" / "data"
FILES = ROOT / "docs" / "files"
MATERIALS = ROOT / "materials"
ASSETS = ROOT / "release-assets"
LABELS = Path(__file__).resolve().parent / "dataset_labels.json"
RELEASE_URL = "https://github.com/knbarka-beep/examstudio/releases/download/datasets-v1/"
LARGE = 50 * 1024 * 1024
CONFIG_DEFAULTS = {"showReferenceSolutions": False, "improvementEnabled": False,
                   "repoUrl": "https://github.com/knbarka-beep/examstudio"}
SOLUTION_FIELDS = ("reference_solution", "draft_solution", "solution_file", "solution_source")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def version():
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip() or "nogit"
    return f"{datetime.date.today():%d.%m.%Y}-{sha}"


def config():
    path = DATA / "config.json"
    cfg = load(path) if path.exists() else {}
    for k, v in CONFIG_DEFAULTS.items():
        cfg.setdefault(k, v)
    return cfg


def public_question(q, show):
    out = {k: v for k, v in q.items() if k not in SOLUTION_FIELDS and k != "status"}
    out["source_file"] = Path(q["source_doc"]).name
    if show:
        out["reference"] = {"solution": q.get("reference_solution"), "source": q.get("solution_source"),
                            "file": Path(q["solution_file"]).name if q.get("solution_file") else None,
                            "draft": q.get("draft_solution")}
    return out


def datasets(materials_paths):
    """Add a download link to each dataset; copy or zip the file when materials/ is there."""
    raw = load(DATA / "datasets.json")
    items = raw["datasets"] if isinstance(raw, dict) else raw
    FILES.mkdir(parents=True, exist_ok=True)
    for d in items:
        assert " " not in d["file"], f"file name with a space: {d['file']}"
        src = materials_paths.get(d["id"])
        if d["size_bytes"] > LARGE:
            zipname = Path(d["file"]).stem + ".zip"
            d["download"] = RELEASE_URL + zipname
            d["release_asset"] = zipname
            if src and src.exists():
                ASSETS.mkdir(exist_ok=True)
                dest = ASSETS / zipname
                if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
                        z.write(src, d["file"])
                d["download_size_bytes"] = dest.stat().st_size
        else:
            d["download"] = "files/" + d["file"]
            if src and src.exists():
                shutil.copy2(src, FILES / d["file"])
    return items


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    v = version()
    cfg = config()
    show = bool(cfg["showReferenceSolutions"])
    write("config.json", {**cfg, "version": v})

    labels = load(LABELS)
    paths = {meta["id"]: MATERIALS / rel for rel, meta in labels.items()}
    items = datasets(paths)
    write("datasets.json", {"version": v, "datasets": items})

    questions = [public_question(q, show) for q in load(BANK / "questions.json")
                 if q["status"] in ("validated", "manual_check")]
    write("questions.json", {"version": v, "questions": questions})

    write("exams.json", {"version": v, "seed": load(BANK / "exams.json")["seed"],
                         "exams": load(BANK / "exams.json")["exams"]})

    interp = [{k: x for k, x in q.items() if k != "status"} for q in load(BANK / "interpretation.json")
              if q["status"] in ("validated", "manual_check")]
    write("interpretation.json", {"version": v, "models": load(BANK / "models.json"), "questions": interp})

    print(f"version {v}: {len(questions)} questions, {len(interp)} interpretation items, "
          f"{len(items)} datasets, reference solutions {'shown' if show else 'hidden'}")
    for d in items:
        where = "release asset " + d["release_asset"] if "release_asset" in d else "docs/files"
        print(f"  {d['file']}: {d['size_bytes'] / 1e6:.2f} MB -> {where}"
              + (f" ({d['download_size_bytes'] / 1e6:.2f} MB zipped)" if "download_size_bytes" in d else ""))


if __name__ == "__main__":
    main()
