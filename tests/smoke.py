"""Smoke test for the published site in docs/. Run after scripts\\build_site.py: py tests\\smoke.py

Checks that every JSON in docs/data parses, that every question, model and dataset referenced exists, that
every download link points to a file in docs/files or to a release asset listed in README.md, that no solution
field is published while showReferenceSolutions is false, that no key-like string is in docs/ or the git index,
and that the site copy has no em dashes. The data files in docs/files are the course files as given, so the em
dash check skips them. Exit code 1 on any failure.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = DOCS / "data"
SOLUTION_FIELDS = ("reference_solution", "draft_solution", "solution_file", "solution_source")
KEY_PATTERNS = [re.compile(p) for p in (rb"sk-[A-Za-z0-9_-]{16,}", rb"AIza[0-9A-Za-z_-]{30,}",
                                        rb"ghp_[A-Za-z0-9]{30,}", rb"xox[abprs]-[A-Za-z0-9-]{10,}")]
EM_DASH = "\u2014"

errors = []


def check(ok, msg):
    if not ok:
        errors.append(msg)


def main():
    data = {}
    for p in sorted(DATA.glob("*.json")):
        try:
            data[p.stem] = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"{p.name} does not parse: {e}")
    for name in ("config", "questions", "exams", "interpretation", "datasets"):
        check(name in data, f"docs/data/{name}.json missing")
        check("version" in data.get(name, {}), f"{name}.json has no version")
    if errors:
        return

    cfg = data["config"]
    questions = {q["id"]: q for q in data["questions"]["questions"]}
    items = {q["id"]: q for q in data["interpretation"]["questions"]}
    models = {m["id"] for m in data["interpretation"]["models"]}
    datasets = {d["id"]: d for d in data["datasets"]["datasets"]}

    for e in data["exams"]["exams"]:
        pool = questions if e["type"] == "manipulation" else items
        for qid in e["question_ids"]:
            check(qid in pool, f"exam {e['id']}: question {qid} missing")
        for f in e["files"]:
            check(f in datasets, f"exam {e['id']}: dataset {f} missing")
    for q in questions.values():
        for d in q["dataset_ids"]:
            check(d in datasets, f"{q['id']}: dataset {d} missing")
    for q in items.values():
        check(q["model_id"] in models, f"{q['id']}: model {q['model_id']} missing")

    index = (DOCS / "index.html").read_text(encoding="utf-8")
    for url in ("css/style.css", "js/app.js"):
        check(f'{url}?v={cfg["version"]}"' in index, f"index.html: {url} has no ?v={cfg['version']}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    manual = readme.split("Manual step: upload release assets", 1)[1] if "Manual step: upload release assets" in readme else ""
    linked = set()
    for d in datasets.values():
        url = d["download"]
        if url.startswith("files/"):
            linked.add(url[6:])
            check((DOCS / url).is_file(), f"{d['id']}: {url} not in docs/files")
        else:
            name = url.rsplit("/", 1)[-1]
            check(d.get("release_asset") == name and name in manual,
                  f"{d['id']}: {url} is not a release asset listed in README.md")
    for f in (DOCS / "files").iterdir():
        check(f.name in linked, f"docs/files/{f.name} is not a listed dataset")

    texts = {p: p.read_text(encoding="utf-8") for p in DOCS.rglob("*")
             if p.is_file() and p.suffix in (".html", ".css", ".js", ".json", ".md", ".txt") and "files" not in p.parts}
    if not cfg.get("showReferenceSolutions"):
        for p, t in texts.items():
            for field in SOLUTION_FIELDS:
                check(field not in t, f"{p.relative_to(ROOT)} contains {field}")
        check(not any("reference" in q for q in questions.values()), "questions.json has reference solutions")
    for p, t in texts.items():
        check(EM_DASH not in t, f"{p.relative_to(ROOT)} contains an em dash")

    tracked = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True).stdout.decode().split("\0")
    scan = {p for p in DOCS.rglob("*") if p.is_file()} | {ROOT / t for t in tracked if t and (ROOT / t).is_file()}
    for p in sorted(scan):
        raw = p.read_bytes()
        for pat in KEY_PATTERNS:
            check(not pat.search(raw), f"{p.relative_to(ROOT)} has a string that looks like a key ({pat.pattern.decode()[:4]})")
    for t in tracked:
        check(not t.startswith(("materials/", "release-assets/")) and t != "bank/inventory.json",
              f"{t} is tracked by git but must not be")

    print(f"{len(questions)} questions, {len(items)} interpretation items, {len(data['exams']['exams'])} exams, "
          f"{len(datasets)} datasets, {len(scan)} files scanned for keys")


if __name__ == "__main__":
    main()
    for e in errors:
        print("FAIL", e)
    print("smoke: " + ("FAILED" if errors else "passed"))
    sys.exit(1 if errors else 0)
