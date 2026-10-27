"""Build docs/data/checks.json: the answer check and the computed trap answers.

Run: py scripts\\build_checks.py   (after py tests\\validate.py)

Every single-value manipulation question gets an answer check against bank/expected/<id>.json.
For a subset, a plausible wrong answer ("trap") is computed here from the raw data with the wrong
method, and stored with the right method's explanation. A trap is only kept when it differs from the
expected answer by more than the tolerance, so the site never calls a right answer a trap.
Nothing here is copied from the solution documents.
"""
import glob
import json
import sqlite3
import sys
from collections import Counter
from functools import cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import validate as V  # noqa: E402  (reuses the same data loaders as the validator)

OUT = ROOT / "docs" / "data" / "checks.json"
SUMMARY = ROOT / "TRAPS.md"


@cache
def db(name):
    path = sorted(glob.glob(str(ROOT / "materials" / "**" / name), recursive=True))[0]
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def sql(name, s):
    return db(name).execute(s).fetchone()[0]


CH, MV, PC = "Chinook_Sqlite.sqlite", "movies.db", "pcards.db"
SP = "EventType 'Shooting Permit'"


def nyc_count(cat):
    return int((V.nyc().Category == cat).sum())


def hours_all():
    n = V.nyc()
    return round(((n.EndDateTime - n.StartDateTime).dt.total_seconds() / 3600).mean() * 2) / 2


def lead_all():
    n = V.nyc()
    return round(((n.StartDateTime - n.EnteredOn).dt.total_seconds() / 86400).mean())


def starts_on(day):
    return round((V.sp().StartDateTime.dt.weekday == day).mean(), 4)


def mean_of_ratios(d, num, den):
    r = (d[num] / d[den]).replace([float("inf"), float("-inf")], pd.NA).dropna()
    return round(float(r.mean()), 2)


def first_row_sales(date):
    s = V.wb("restaurant_data", "salesData")
    return float(s[s.date == date].netTotal.iloc[0])


def row_mean(game):
    s = V.wb("restaurant_data", "salesData")
    g = V.wb("restaurant_data", "gameData")[["date", "gameDay"]]
    m = s.merge(g, on="date", how="left")
    m["gameDay"] = m.gameDay.fillna(0)
    return round(float(m[m.gameDay == game].netTotal.mean()), 2)


def tmax_top_row():
    s = V.wb("restaurant_data", "salesData")
    w = V.wb("restaurant_data", "weatherData").set_index("date")
    return float(w.loc[s.loc[s.netTotal.idxmax(), "date"], "tmax"])


def unrated_as_zero(year):
    return round(sql(MV, f"SELECT SUM(COALESCE(r.rating, 0)) * 1.0 / COUNT(*) FROM movies m "
                         f"LEFT JOIN ratings r ON r.movie_id = m.id WHERE m.year = {year}"), 2)


def returns_first_char(year):
    return round(sql(PC, f"SELECT SUM(Amount) FROM pcards WHERE Amount < 0 AND TransactionDate LIKE '%/{year} %' "
                         "AND substr(TransactionDate, 1, 1) IN ('1', '2', '3')"), 2)


def amazon(where):
    return round(sql(PC, "SELECT SUM(CASE WHEN Amount >= 500 THEN Amount * 0.0075 ELSE Amount * 0.005 END) "
                         f"FROM pcards WHERE TransactionDate LIKE '%/2014 %' AND {where}"), 2)


# Category names are the five kinds of "looks right, is wrong" from the course notes.
POP, GRAIN, MIX, EDGE, DEF = ("Wrong population", "Wrong grain or key", "Average of ratios",
                              "Boundary or parsing", "Wrong definition")

TRAPS = {
    "Q004": [(DEF, lambda: int(V.nyc().ZipCode.isna().sum()) + 2,
              "You counted the blank ZipCodes as invalid too. LEN(blank) is 0, which is not 5, so a LEN test "
              "catches the {m} missing ones. The question asks for values that are present but wrong.",
              {"m": lambda: int(V.nyc().ZipCode.isna().sum())})],
    "Q011": [(POP, lambda: nyc_count("Student"),
              "You counted every event type, not only shooting permits. Filter EventType first, then count.", {})],
    "Q012": [(POP, lambda: nyc_count("Documentary"),
              "You counted every event type, not only shooting permits. Filter EventType first, then count.", {})],
    "Q013": [(POP, lambda: nyc_count("Music Video"),
              "You counted every event type, not only shooting permits. Filter EventType first, then count.", {})],
    "Q016": [(POP, lambda: round(float((V.sp().Borough.eq("Manhattan") & V.sp().ParkingHeld.str.contains(
                  "BROADWAY", case=False)).mean()), 4),
              "You divided by all shooting permits instead of the Manhattan ones. The denominator is the "
              "population the question names: shoots in Manhattan.", {}),
             (POP, lambda: round(float(V.nyc()[V.nyc().Borough == "Manhattan"].ParkingHeld.str.contains(
                  "BROADWAY", case=False).mean()), 4),
              "You kept every event type in Manhattan. Filter on shooting permits first.", {})],
    "Q020": [(POP, hours_all,
              "You averaged every event type. Non-shooting events run longer, which pulls the mean up. "
              "Filter on shooting permits first.", {})],
    "Q022": [(POP, lead_all,
              "You averaged every event type. Filter on shooting permits first.", {})],
    "Q024": [(DEF, lambda: starts_on(4),
              "You counted permits that start on a Friday. The question counts permits that touch a Friday "
              "anywhere between start and end, so multi-day shoots that start on Wednesday or Thursday count too.",
              {})],
    "Q025": [(DEF, lambda: starts_on(5),
              "You counted permits that start on a Saturday. The question counts permits that touch a Saturday "
              "anywhere between start and end, so shoots that start earlier in the week and run over count too.",
              {})],
    "Q029": [(DEF, lambda: int(V.etl1_rows()[2].duplicated(keep=False).sum()),
              "You counted both copies. Remove Duplicates and COUNTIFS both see the original as well; the "
              "question asks how many rows repeat an earlier row.", {})],
    "Q037": [(GRAIN, lambda: V.etl2().PlantID.nunique(),
              "You counted distinct PlantIDs. Plant 12 exists in several countries, so PlantID alone is not a "
              "key. The plant is only identified by Location and PlantID together.", {})],
    "Q044": [(GRAIN, lambda: V.etl3().PlantID.nunique(),
              "You counted distinct PlantIDs. The same plant number is used in several countries, so the key "
              "is Location and PlantID together.", {})],
    "Q042": [(EDGE, lambda: int((V.etl3().PayPeriod == "M").sum()),
              "You matched only 'M'. {mo} employees are coded 'Mo', which also means monthly. Check the distinct "
              "values of a coded field before you count.",
              {"mo": lambda: int((V.etl3().PayPeriod == "Mo").sum())})],
    "Q048": [(GRAIN, lambda: V.etl4()["PreparerInfo"].query("PreparerID == 102").PreparerName.iloc[0]
              .split("|")[0].strip(),
              "You looked up PreparerID 102 alone and got the first match, which belongs to BusinessUnitID 1. "
              "PreparerID 102 appears {k} times, so the lookup needs both columns (INDEX/MATCH on two "
              "conditions, or a helper key).",
              {"k": lambda: int((V.etl4()["PreparerInfo"].PreparerID == 102).sum())})],
    "Q052": [(DEF, lambda: -round(V.je_with("ChartOfAccounts", "GLAccountNumber", ["AccountType"])
                                  .query("AccountType == 'Revenue'").Amount.sum(), 2),
              "Right size, wrong sign. Revenue is posted as credits, so in a signed Amount column it sums to a "
              "negative number.", {})],
    "Q053": [(DEF, lambda: sum(1 for _ in open(V.P("ic_payroll2015_csv"), encoding="utf-8", errors="ignore")),
              "You counted the header line as a data row.", {})],
    "Q057": [(DEF, lambda: round(V.p15().loc[V.p15().Code == "001", "Reg_Pay"].sum(), 2),
              "You summed Reg_Pay only. Gross pay is Reg_Pay plus OT_Pay.", {})],
    "Q060": [(GRAIN, lambda: round(V.p16().Gross_Wages.sum() - V.p15().Reg_Pay.sum(), 2),
              "You compared 2016 gross wages with 2015 regular pay. The two files measure pay differently: "
              "2016 has one Gross_Wages column, 2015 splits Reg_Pay and OT_Pay. Build the same measure in both "
              "years before you subtract.", {})],
    "Q061": [(MIX, lambda: mean_of_ratios(V.p15()[V.p15().Code == "005"], "Gross", "Hrs"),
              "You averaged the pay per hour of each row. Rows with few hours count as much as rows with many, "
              "so the mean of ratios is not the pay per hour. Divide total gross pay by total hours.", {})],
    "Q066": [(DEF, lambda: round(V.p16().Gross_Wages.sum(), 2),
              "You summed Gross_Wages only. Employee cost also includes SocSec_Medicare, FUTA, SUTA and "
              "Work_Comp.", {})],
    "Q069": [(MIX, lambda: mean_of_ratios(V.with_loc(V.p16().dropna(subset=["Employee_Name"]), "Employee_Name")
                                         .query("Location == 1"), "Gross_Wages", "Hrs"),
              "You averaged each row's pay per hour. That weights a two-hour row like a forty-hour row. "
              "Divide total Gross_Wages by total hours.", {})],
    "Q075": [(GRAIN, lambda: first_row_sales("2018-12-31"),
              "You looked the date up and got one menu item's netTotal. salesData has one row per menu item per "
              "day, so a daily total needs SUMIFS or a pivot, not VLOOKUP.", {})],
    "Q076": [(GRAIN, lambda: first_row_sales("2018-01-08"),
              "You looked the date up and got one menu item's netTotal. salesData has one row per menu item per "
              "day, so a daily total needs SUMIFS or a pivot, not VLOOKUP.", {})],
    "Q079": [(GRAIN, tmax_top_row,
              "You took the date of the single biggest menu-item row. The question is about the biggest day, so "
              "sum netTotal per date first, then find the maximum.", {})],
    "Q080": [(GRAIN, lambda: row_mean(1),
              "You averaged menu-item rows, not days. Sum netTotal per date first, then average the daily "
              "totals.", {})],
    "Q081": [(GRAIN, lambda: row_mean(0),
              "You averaged menu-item rows, not days. Sum netTotal per date first, then average the daily "
              "totals.", {})],
    "Q098": [(EDGE, lambda: sql(CH, "SELECT COUNT(*) FROM Employee WHERE strftime('%w', BirthDate) = '1'"),
              "You used '1' for Sunday, as in Excel's WEEKDAY. In SQLite strftime('%w') Sunday is '0' and "
              "Monday is '1'.", {})],
    "Q100": [(EDGE, lambda: sql(CH, "SELECT MAX(CAST(strftime('%Y', HireDate) AS INT) - "
                                    "CAST(strftime('%Y', BirthDate) AS INT)) FROM Employee"),
              "You subtracted the years only. That ignores whether the birthday had passed at the hire date. "
              "Use the day difference divided by 365.25.", {})],
    "Q114": [(EDGE, lambda: sql(MV, "SELECT COUNT(*) FROM ratings WHERE rating >= 9.0"),
              "You used >= instead of >. {k} movies are rated exactly 9.0.",
              {"k": lambda: sql(MV, "SELECT COUNT(*) FROM ratings WHERE rating = 9.0")})],
    "Q115": [(EDGE, lambda: sql(MV, "SELECT COUNT(*) FROM ratings WHERE rating >= 9.5"),
              "You used >= instead of >. {k} movies are rated exactly 9.5.",
              {"k": lambda: sql(MV, "SELECT COUNT(*) FROM ratings WHERE rating = 9.5")})],
    "Q118": [(DEF, lambda: unrated_as_zero(2013),
              "You counted movies without a rating as zero (LEFT JOIN with COALESCE, or SUM divided by COUNT(*)). "
              "AVG(rating) skips missing ratings; a missing rating is unknown, not zero.", {})],
    "Q119": [(DEF, lambda: unrated_as_zero(2012),
              "You counted movies without a rating as zero (LEFT JOIN with COALESCE, or SUM divided by COUNT(*)). "
              "AVG(rating) skips missing ratings; a missing rating is unknown, not zero.", {})],
    "Q148": [(EDGE, lambda: sql(PC, "SELECT COUNT(*) FROM pcards WHERE Amount > 5000"),
              "You used > instead of >=. {k} transactions are exactly $5,000, and 'or more' includes them.",
              {"k": lambda: sql(PC, "SELECT COUNT(*) FROM pcards WHERE Amount = 5000")})],
    "Q149": [(EDGE, lambda: returns_first_char(2014),
              "You took the month from the first character of TransactionDate. That also catches October, "
              "November and December, because '10/', '11/' and '12/' start with 1. Take everything before the "
              "first '/' as the month.", {})],
    "Q150": [(EDGE, lambda: returns_first_char(2013),
              "You took the month from the first character of TransactionDate. That also catches October, "
              "November and December. Take everything before the first '/' as the month.", {})],
    "Q163": [(EDGE, lambda: amazon("Vendor = 'Amazon.com' AND Amount > 0"),
              "You matched the vendor name with exact case. The vendor is also written in other cases, and the "
              "question says any letter case: use LOWER(Vendor) = 'amazon.com'.", {}),
             (DEF, lambda: amazon("LOWER(Vendor) = 'amazon.com'"),
              "You included returns. Earnings are on purchases only (Amount above 0); a return would reduce "
              "them twice.", {})],
}

# Disputed questions: more than one defensible answer.
ALSO_ACCEPT = {}  # id -> ([other accepted values], note); empty: Q015 and Q108 are disputed and left off the site


def kind_of(q, value):
    hint = (q.get("expected_answer_hint") or "").lower()
    if "percentage" in hint and isinstance(value, float) and abs(value) <= 1:
        return "percent"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if "date" in hint:
        return "datetime"
    return "text"


def tolerance(q, kind, value):
    p = q["prompt"].lower()
    if kind == "percent":
        return 0.0055
    if kind != "number":
        return 0
    if "half hour" in p:
        return 0.25
    if "nearest day" in p or "nearest percent" in p:
        return 0.49
    if float(value).is_integer() and "round" not in p and "average" not in p:
        return 0
    if "one number" in (q.get("expected_answer_hint") or "").lower() or "years" in p:
        return 0.051
    return 0.0051


def py(v):
    return v.item() if hasattr(v, "item") else v


def main():
    qs = json.loads((ROOT / "bank" / "questions.json").read_text(encoding="utf-8"))
    on_site = {q["id"] for q in json.loads((ROOT / "docs" / "data" / "questions.json").read_text(
        encoding="utf-8"))["questions"]}
    qs = [q for q in qs if q["id"] in on_site]
    checks, cats, eligible = {}, Counter(), 0
    for q in qs:
        exp = json.loads((ROOT / "bank" / "expected" / f"{q['id']}.json").read_text(encoding="utf-8"))
        if len(exp["columns"]) != 1 or not exp["rows"]:
            continue
        values = [py(r[0]) for r in exp["rows"]]
        if len(values) > 1 and q["id"] not in ALSO_ACCEPT:
            continue
        value = values[0]
        if isinstance(value, str) and len(value) > 60:
            continue
        eligible += 1
        kind = kind_of(q, value)
        tol = tolerance(q, kind, value)
        entry = {"kind": kind, "answer": value, "tol": tol, "traps": []}
        if q["id"] in ALSO_ACCEPT:
            extra, note = ALSO_ACCEPT[q["id"]]
            assert set(values) == {value, *extra}, q["id"]
            entry["also"] = extra
            entry["note"] = note
        for cat, fn, why, ev in TRAPS.get(q["id"], []):
            t = py(fn())
            if isinstance(t, float) and kind in ("number", "percent"):
                t = round(t, 4)
            same = (abs(float(t) - float(value)) <= tol) if kind in ("number", "percent") else \
                str(t).strip().lower() == str(value).strip().lower()
            if same:
                print(f"{q['id']}: trap equals the answer ({t}), dropped")
                continue
            entry["traps"].append({"category": cat, "value": t,
                                   "why": why.format(**{k: py(f()) for k, f in ev.items()})})
            cats[cat] += 1
        checks[q["id"]] = entry
    with_traps = sorted(k for k, v in checks.items() if v["traps"])
    meta = {"checked": len(checks), "with_traps": len(with_traps),
            "traps": sum(len(checks[k]["traps"]) for k in with_traps), "categories": dict(cats)}
    OUT.write_text(json.dumps({"meta": meta, "checks": checks}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    lines = ["# Computed trap answers", "",
             f"{meta['checked']} single-value questions on the site get an answer check. {meta['with_traps']} of them have "
             f"at least one computed trap answer ({meta['traps']} traps in total). Every trap is calculated from "
             "the raw data with the wrong method in `scripts/build_checks.py`; none is guessed.", "",
             "| Category | Traps |", "|---|---|"]
    lines += [f"| {c} | {n} |" for c, n in cats.most_common()]
    lines += ["", "| Question | Answer | Trap answer | Category |", "|---|---|---|---|"]
    for k in with_traps:
        for t in checks[k]["traps"]:
            lines.append(f"| {k} | {checks[k]['answer']} | {t['value']} | {t['category']} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
