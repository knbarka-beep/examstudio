"""Compose practice exams from the validated bank and write bank/exams.json.

Run after tests\\validate.py: py scripts\\build_exams.py

Format mirrors the lecturer's live Exam Studio:
- Data manipulation: 5 questions, 3 Excel then 2 SQL, one Excel-side file and one database, 8 minutes,
  no two questions from the same variant family, estimated minutes summing to at most 8.
- Data interpretation: 4 items, 5 minutes, one of each kind where possible, each from a different model
  where possible.
Only questions with status validated or manual_check are used; optional questions are left out because the
exams cover the required tasks. The seed makes the set reproducible.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "bank"
SEED = 2026
PER_PAIR = 10
INTERPRETATION_EXAMS = 30
ATTEMPTS = 200
KINDS = ["predict", "coefficient", "significance", "dummy"]


def family(q):
    return q["is_variant_of"] or q["id"]


def pick(rng, pool, n, used_families):
    """n questions from pool, each from a new variant family, or None."""
    pool = pool[:]
    rng.shuffle(pool)
    out = []
    for q in pool:
        if family(q) not in used_families:
            out.append(q)
            used_families.add(family(q))
            if len(out) == n:
                return out
    return None


def manipulation(rng, questions):
    usable = [q for q in questions if q["status"] in ("validated", "manual_check") and not q.get("optional")
              and len(q["dataset_ids"]) == 1]
    by_file = {}
    for q in usable:
        by_file.setdefault((q["subject"], q["dataset_ids"][0]), []).append(q)
    excel = sorted(k[1] for k in by_file if k[0] == "Excel")
    sql = sorted(k[1] for k in by_file if k[0] == "SQL")
    exams, pairs = [], {}
    for xf in excel:
        for db in sql:
            seen = set()
            for _ in range(ATTEMPTS):
                if len(seen) == PER_PAIR:
                    break
                fams = set()
                x = pick(rng, by_file[("Excel", xf)], 3, fams)
                s = pick(rng, by_file[("SQL", db)], 2, fams)
                if not x or not s or sum(q["estimated_minutes"] for q in x + s) > 8:
                    continue
                key = (frozenset(q["id"] for q in x), frozenset(q["id"] for q in s))
                if key in seen:
                    continue
                seen.add(key)
                exams.append({"type": "manipulation", "files": [xf, db], "time_limit_minutes": 8,
                              "question_ids": [q["id"] for q in x + s]})
            if seen:
                pairs[f"{xf} + {db}"] = len(seen)
    for i, e in enumerate(exams, 1):
        e["id"] = f"E{i:03d}"
    return exams, pairs


def interpretation(rng, items):
    usable = [it for it in items if it["status"] == "validated"]
    by_kind = {k: [it for it in usable if it["kind"] == k] for k in KINDS}
    exams, seen = [], set()
    for _ in range(ATTEMPTS * 5):
        if len(exams) == INTERPRETATION_EXAMS:
            break
        chosen, models = [], set()
        for k in sorted(KINDS, key=lambda k: len(by_kind[k])):  # scarcest kind first
            options = [it for it in by_kind[k] if it["model_id"] not in models] or by_kind[k]
            if not options:
                continue
            it = rng.choice(options)
            chosen.append(it)
            models.add(it["model_id"])
        if len(chosen) != 4:
            continue
        chosen.sort(key=lambda it: KINDS.index(it["kind"]))
        key = frozenset(it["id"] for it in chosen)
        if key in seen:
            continue
        seen.add(key)
        exams.append({"id": f"R{len(exams) + 1:03d}", "type": "interpretation", "files": ["restaurant_data"],
                      "time_limit_minutes": 5, "question_ids": [it["id"] for it in chosen]})
    return exams


def main():
    rng = random.Random(SEED)
    questions = json.loads((BANK / "questions.json").read_text(encoding="utf-8"))
    items = json.loads((BANK / "interpretation.json").read_text(encoding="utf-8"))
    man, pairs = manipulation(rng, questions)
    rec = interpretation(rng, items)
    q = {x["id"]: x for x in questions}
    for e in man:  # self-check of the format rules
        qs = [q[i] for i in e["question_ids"]]
        assert [x["subject"] for x in qs] == ["Excel"] * 3 + ["SQL"] * 2, e
        assert {d for x in qs for d in x["dataset_ids"]} == set(e["files"]), e
        assert len({family(x) for x in qs}) == 5 and sum(x["estimated_minutes"] for x in qs) <= 8, e
    assert all(len(e["question_ids"]) == 4 for e in rec)
    out = {"seed": SEED, "per_pair_limit": PER_PAIR, "pairs": pairs, "exams": man + rec}
    (BANK / "exams.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"seed {SEED}: {len(man)} manipulation exams over {len(pairs)} file pairs, {len(rec)} interpretation exams")


if __name__ == "__main__":
    main()
