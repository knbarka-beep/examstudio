"""Validate the question bank and the interpretation bank against the course data.

Run: py tests\\validate.py
Exit code 0 only when every question whose status is not "excluded" passes.
Writes VALIDATION_REPORT.md, bank/expected/<id>.json, and the status field in
bank/questions.json and bank/interpretation.json. Safe to re-run after editing content.

Decisions that a run cannot make by itself (disputed references, exclusions,
manual checks) live in DECISIONS below, so they survive a rebuild of the bank.
"""
import csv
import hashlib
import io
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from functools import cache
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MAT = ROOT / "materials"
BANK = ROOT / "bank"
EXPECTED = BANK / "expected"
QUESTIONS = BANK / "questions.json"
INTERP = BANK / "interpretation.json"
MODELS = BANK / "models.json"
DATASETS = ROOT / "docs" / "data" / "datasets.json"
REPORT = ROOT / "VALIDATION_REPORT.md"
SQL_TIMEOUT = 30
REQUIRED = ["id", "subject", "case", "source_doc", "source_task", "dataset_ids", "required_objects", "prompt",
            "skills", "estimated_minutes", "is_variant_of", "reference_solution", "solution_source",
            "solution_file", "draft_solution", "expected_answer_hint", "status"]

# id -> (status, reason). Statuses: "disputed" (materials' answer looks wrong; the check still runs and must
# give the mismatch described), "excluded" (not checked, not used), "manual_check" (computed part checked,
# the rest needs a person).
DECISIONS = {
    "Q015": ("disputed", "solutions.xlsx says 2017. Shooting permits by year of StartDateTime: Brooklyn exceeds "
                         "Manhattan in 2017 (1,719 vs 1,550) and also in 2018 (176 vs 138). The 2018 data stops in "
                         "February, so 2017 is the only full year, but the question as set has two answers."),
    "Q108": ("disputed", "PWC answers.docx says 49. With its own assumption (all tracks of an album on one "
                         "invoice) there are 49 invoice and album pairs but only 41 distinct albums, because 8 "
                         "albums are downloaded complete twice. The question asks for distinct albums, so 49 "
                         "looks like a count of downloads, not of albums."),
    "Q026": ("manual_check", "The row count is computed (3); the cause (the unquoted comma in 'Apple, Inc.') is "
                             "checked by a person."),
    "Q028": ("manual_check", "The value is computed; naming the two formats (parentheses and minus sign) is "
                             "checked by a person."),
    "Q031": ("manual_check", "The company and the cleaned ticker are computed; the formula is checked by a "
                             "person, since several formulas work."),
    "Q082": ("manual_check", "The count is computed; the reason it matters for a regression is checked by a "
                             "person."),
}

# Fixes made to generated drafts, for the report. Each entry: (id, what was wrong, what changed).
FIXES = [
    ("Q072", "The prompt did not say the payroll files are pipe-delimited.",
     "Added '(pipe-delimited)' to the prompt (build_bank.py and questions.json)."),
    ("Q073", "The prompt did not say the payroll files are pipe-delimited.",
     "Added '(pipe-delimited)' to the prompt (build_bank.py and questions.json)."),
    ("Q124", "Three films tie on 7.3 at fifth place, so 'the five highest rated' had no single answer.",
     "Prompt now says ties go in alphabetical order of title; draft orders by rating DESC, title."),
]

# Things a reader of the report should know that did not lead to a change.
OBSERVATIONS = [
    "P-card: 12 cardholder names occur in 2014 in two letter cases (for example 'C Stover' and 'C STOVER'). "
    "The drafts follow the case text (Name = first initial and last name, as stored), so GROUP BY Name keeps "
    "them apart. This affects the per-person questions (Q152 to Q155, Q168 to Q170, Q172 to Q174, Q178).",
    "IntegrateCo: 2015 gross pay for job code 009 (Q058) is 0.00 while 2016 has wages on 009 (Q059). The "
    "zero is what the data gives, not a parsing error.",
    "Ties at a LIMIT cut-off are not detected automatically; Q085, Q107, Q109, Q124, Q129, Q140 and Q143 "
    "were checked by hand in Run 2.",
]


# ---------- helpers ----------

def canon_value(v):
    if v is None:
        return None
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        v = v.item()  # numpy scalar
    if isinstance(v, float) and v != v:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        r = round(float(v), 2)
        r = 0.0 if r == 0 else r
        return int(r) if r == int(r) else r
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return str(v).strip()


def canon(columns, rows, ordered):
    rows = [[canon_value(v) for v in r] for r in rows]
    if not ordered:
        rows = sorted(rows, key=lambda r: json.dumps(r, sort_keys=True))
    return [str(c).strip() for c in columns], rows


def digest(columns, rows):
    return hashlib.sha256(json.dumps([columns, rows], ensure_ascii=False).encode("utf-8")).hexdigest()


def save_expected(qid, columns, rows, ordered, note=None):
    EXPECTED.mkdir(parents=True, exist_ok=True)
    out = {"id": qid, "columns": columns, "row_count": len(rows), "ordered": ordered, "rows": rows[:20],
           "sha256": digest(columns, rows)}
    if note:
        out["note"] = note
    (EXPECTED / f"{qid}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


@cache
def dataset_index():
    raw = json.loads(DATASETS.read_text(encoding="utf-8"))
    return {d["id"]: d for d in (raw["datasets"] if isinstance(raw, dict) else raw)}


@cache
def dataset_path(ds_id):
    name = dataset_index()[ds_id]["file"]
    hits = sorted(MAT.rglob(name))
    return hits[0] if hits else None


def ref_matches(ref, columns, rows):
    """Generic comparison of a stated reference with a result: a scalar against a one-cell result."""
    if isinstance(ref, str) and re.match(r"\s*(SELECT|WITH)\b", ref, re.I):
        return None  # handled by running it
    if isinstance(ref, list):
        return canon_value(ref) == rows
    if len(rows) == 1:  # the asked value is the first column; later columns are supporting detail
        return canon_value(ref) == rows[0][0]
    return False


# Comparisons where the materials state the answer in words. Each gets the canonical (columns, rows).
REF_CHECKS = {
    "Q100": lambda c, r: abs(r[0][0] - 55.5) <= 0.5,                      # "Approximately 55.5 years"
    "Q105": lambda c, r: r == [[2, 256]],                                 # "256 tracks have been downloaded twice"
    "Q106": lambda c, r: abs(r[0][2] - 5) <= 0.5,                         # "Approximately 5 years"
    "Q107": lambda c, r: len(r) == 5 and all(x[1] == 2 for x in r),       # top five all downloaded twice
    "Q108": lambda c, r: r == [[49]],                                     # "...on a single invoice: 49"
}


# ---------- structural ----------

def structural(q, ids, datasets):
    errs = []
    missing = [k for k in REQUIRED if k not in q]
    if missing:
        errs.append(f"missing fields: {', '.join(missing)}")
    for ds in q.get("dataset_ids", []):
        if ds not in datasets:
            errs.append(f"dataset_id {ds} not in datasets.json")
        elif dataset_path(ds) is None:
            errs.append(f"dataset file {datasets[ds]['file']} not found in materials/")
    if not q.get("dataset_ids"):
        errs.append("no dataset_ids")
    v = q.get("is_variant_of")
    if v is not None and v not in ids:
        errs.append(f"is_variant_of {v} does not exist")
    if not q.get("skills"):
        errs.append("skills empty")
    m = q.get("estimated_minutes")
    if not isinstance(m, (int, float)) or not 0.5 <= m <= 5:
        errs.append(f"estimated_minutes {m} outside 0,5 to 5")
    if q.get("solution_source") not in ("materials", "generated"):
        errs.append(f"solution_source {q.get('solution_source')!r}")
    if q.get("solution_source") == "materials" and not q.get("solution_file"):
        errs.append("solution_source materials without solution_file")
    return errs


# ---------- SQL ----------

def connect_ro(path):
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)


def run_sql(conn, sql):
    deadline = time.monotonic() + SQL_TIMEOUT
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10000)
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        return [d[0] for d in cur.description], [list(r) for r in rows]
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            raise TimeoutError(f"query ran longer than {SQL_TIMEOUT} s") from e
        raise
    finally:
        conn.set_progress_handler(None, 0)


def is_ordered(sql):
    tail = sql.rstrip().rstrip(";")
    i = tail.upper().rfind("ORDER BY")
    return i >= 0 and ")" not in tail[i:]


def check_sql(q):
    errs, notes = [], []
    path = dataset_path(q["dataset_ids"][0])
    conn = connect_ro(path)
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        for t in q["required_objects"]["tables"]:
            if t not in tables:
                errs.append(f"table {t} missing")
        for col in q["required_objects"]["columns"]:
            t, c = col.split(".", 1)
            if t in tables and c not in {r[1] for r in conn.execute(f"PRAGMA table_info('{t}')")}:
                errs.append(f"column {col} missing")
        try:
            cols, rows = run_sql(conn, q["draft_solution"])
        except Exception as e:  # noqa: BLE001 - any failure of the draft is a failed check
            return errs + [f"draft fails: {e}"], notes
        ordered = is_ordered(q["draft_solution"])
        cols, rows = canon(cols, rows, ordered)
        if not rows:
            errs.append("draft returns no rows")
        ref = q["reference_solution"]
        if ref is not None:
            if isinstance(ref, str) and re.match(r"\s*(SELECT|WITH)\b", ref, re.I):
                rc, rr = canon(*run_sql(conn, ref), ordered)
                ok = (rc, rr) == (cols, rows) or rr == rows
            elif q["id"] in REF_CHECKS:
                try:
                    ok = REF_CHECKS[q["id"]](cols, rows)
                except Exception:  # noqa: BLE001
                    ok = False
            else:
                ok = ref_matches(ref, cols, rows)
            if not ok:
                errs.append(f"result {rows[:3]} does not match the materials' reference {ref!r}")
        save_expected(q["id"], cols, rows, ordered)
    finally:
        conn.close()
    return errs, notes


# ---------- Excel ----------

def P(ds):
    return dataset_path(ds)


@cache
def nyc():
    return pd.read_excel(P("nyc_film_permits_xlsx"))


def sp():
    n = nyc()
    return n[n.EventType == "Shooting Permit"]


@cache
def etl1_rows():
    """ETL Case 1 read with a plain comma split, then the Apple rows repaired (name holds a comma)."""
    with open(P("etl_case1"), encoding="utf-8", newline="") as f:
        raw = list(csv.reader(f))
    head, body = raw[0], raw[1:]
    fixed = [r[:1] + [r[1] + "," + r[2]] + r[3:] if len(r) == 9 else r for r in body]
    return head, body, pd.DataFrame(fixed, columns=head)


def plain_number(s):
    s = str(s).strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    mult = {"K": 1e3, "M": 1e6}.get(s[-1:], 1)
    s = s.rstrip("KM").strip()
    return (-1 if neg else 1) * float(s) * mult


@cache
def wb(ds, sheet):
    return pd.read_excel(P(ds), sheet_name=sheet)


def etl2():
    d = wb("etl_case2", "Case 2").copy()
    c = d.EmployeeCode.astype(str)
    d["Location"] = c.str[:3]
    d["EmpID"] = c.str[3:7].astype(int)
    d["PlantID"] = c.str.split("-").str[1].str[:2]
    d["PayPeriod"] = c.str[-1]
    d["LocationPlantID"] = d.Location + "-" + d.PlantID
    return d


def etl3():
    d = wb("etl_case3", "Case 3 data").copy()
    parts = d.EmployeeCode.astype(str).str.extract(r"^([A-Za-z]+)(\d+)-(\d+)([A-Za-z]+)$")
    assert parts.notna().all().all(), "unparsed Case 3 codes"
    d["Location"], d["EmpID"], d["PlantID"], d["PayPeriod"] = parts[0], parts[1], parts[2].astype(int), parts[3]
    d["LocationPlantID"] = d.Location + "-" + d.PlantID.astype(str)
    return d


def etl4():
    return {k: wb("etl_case4", k) for k in ["JELineItems", "BusinessUnits", "ChartOfAccounts", "PreparerInfo",
                                            "Source"]}


def je_with(sheet, key, cols):
    t = etl4()
    m = t["JELineItems"].merge(t[sheet][[key] + cols], on=key, how="left", validate="many_to_one")
    assert m[cols].notna().all().all(), f"unmatched lookup on {sheet}"
    return m


def jobcode(s):
    return s.astype(str).str.extract(r"^\d{2}[HS]?(\d{3})")[0]


@cache
def p15():
    d = pd.read_csv(P("ic_payroll2015_csv"), sep="|", dtype={"Job": str})
    d["Code"] = jobcode(d.Job)
    d["Gross"] = d.Reg_Pay + d.OT_Pay
    d["Hrs"] = d.Reg_Hrs + d.OT_Hrs
    d["Date"] = pd.to_datetime(d.Pay_Date, format="%m/%d/%Y")
    d["Name"] = d.First_Name + " " + d.Last_Name
    return d


@cache
def p16():
    d = pd.read_csv(P("ic_payroll2016_csv"), sep="|", dtype={"Project": str})
    d["Code"] = jobcode(d.Project)
    d["Hrs"] = d.Hours + d.OT_Hours
    return d


@cache
def locs():
    return pd.read_csv(P("ic_locations"), sep="|")


def with_loc(d, name_col):
    m = d.merge(locs(), left_on=name_col, right_on="Employee_Name", how="left", suffixes=("", "_loc"))
    assert len(m) == len(d)
    return m


@cache
def daily():
    s = wb("restaurant_data", "salesData")
    d = s.groupby("date").agg(sales=("netTotal", "sum"), items=("LineItem", "count")).reset_index()
    g = wb("restaurant_data", "gameData")[["date", "gameDay"]]
    d = d.merge(g, on="date", how="left")
    d["gameDay"] = d.gameDay.fillna(0).astype(int)
    return d.merge(wb("restaurant_data", "weatherData"), on="date", how="left")


def one(name, v):
    return [name], [[v]]


def top(series, label, value):
    """Single top entry of a series; fails on a tie so ambiguous questions are caught."""
    s = series.sort_values(ascending=False)
    assert len(s) < 2 or s.iloc[0] != s.iloc[1], f"tie for the top value: {s.index[0]} and {s.index[1]}"
    return [label, value], [[s.index[0], s.iloc[0]]]


def mode1(series):
    return top(series.value_counts(), "", "")[1][0][0]


def includes_weekday(day):
    n = sp()
    a, b = n.StartDateTime.dt.normalize(), n.EndDateTime.dt.normalize()
    span = (b - a).dt.days
    hit = (span >= 6) | (((day - a.dt.weekday) % 7) <= span)
    return one("share", round(hit.mean(), 4))


def gross_by_code(code):
    d = p15()
    return one("gross_pay", round(d.loc[d.Code == code, "Gross"].sum(), 2))


def monthly15():
    d = p15()
    return d.groupby(d.Date.dt.month).Gross.sum()


EXCEL = {
    "Q001": lambda: one("records", len(nyc())),
    "Q002": lambda: one("columns", nyc().shape[1]),
    "Q003": lambda: one("missing", int(nyc().ZipCode.isna().sum())),
    "Q004": lambda: one("invalid", int(nyc().ZipCode.dropna().map(lambda z: len(str(int(z))) != 5).sum())),
    "Q005": lambda: (["column"], [[c] for c in nyc().columns if nyc()[c].nunique(dropna=False) == 1]),
    "Q006": lambda: one("oldest", nyc().EnteredOn.min()),
    "Q007": lambda: one("newest", nyc().EnteredOn.max()),
    "Q008": lambda: one("types", nyc().EventType.nunique()),
    "Q009": lambda: one("EventType", mode1(nyc().EventType)),
    "Q010": lambda: one("Category", mode1(sp().Category)),
    "Q011": lambda: one("count", int((sp().Category == "Student").sum())),
    "Q012": lambda: one("count", int((sp().Category == "Documentary").sum())),
    "Q013": lambda: one("count", int((sp().Category == "Music Video").sum())),
    "Q014": lambda: one("share", round(sp()["CommunityBoard(s)"].astype(str).str.contains(",").mean(), 4)),
    "Q015": lambda: (["year"], [[y] for y, r in sp().groupby([sp().StartDateTime.dt.year, "Borough"]).size()
                                .unstack().iterrows() if r.get("Brooklyn", 0) > r.get("Manhattan", 0)]),
    "Q016": lambda: one("share", round(sp()[sp().Borough == "Manhattan"].ParkingHeld.str.contains(
        "BROADWAY", case=False).mean(), 2)),
    "Q017": lambda: one("share", round(sp()[sp().Borough == "Brooklyn"].ParkingHeld.str.contains(
        "BROADWAY", case=False).mean(), 2)),
    "Q018": lambda: one("count", int(((sp().EnteredOn >= "2013-01-01")
                                      & (sp().Country != "United States of America")).sum())),
    "Q019": lambda: one("count", int(((sp().EnteredOn >= "2016-01-01")
                                      & (sp().Country != "United States of America")).sum())),
    "Q020": lambda: one("hours", round(((sp().EndDateTime - sp().StartDateTime).dt.total_seconds()
                                        / 3600).mean() * 2) / 2),
    "Q021": lambda: one("minutes", (sp().EndDateTime - sp().StartDateTime).dt.total_seconds().min() / 60),
    "Q022": lambda: one("days", round(((sp().StartDateTime - sp().EnteredOn).dt.total_seconds()
                                       / 86400).mean())),
    "Q023": lambda: one("day", mode1(sp().StartDateTime.dt.day_name())),
    "Q024": lambda: includes_weekday(4),
    "Q025": lambda: includes_weekday(5),
    "Q026": lambda: one("rows_over_8_fields", sum(len(r) > 8 for r in etl1_rows()[1])),
    "Q027": lambda: (["column", "value"], [["Cash", plain_number(etl1_rows()[2].query(
        "Ticker == 'AAPL' and Year == '2016'").Cash.iloc[0])]]),
    "Q028": lambda: one("value", plain_number(etl1_rows()[2].query(
        "Ticker == 'AAL' and Year == '2018'")["Total Depreciation"].iloc[0])),
    "Q029": lambda: one("duplicates", int(etl1_rows()[2].duplicated().sum())),
    "Q030": lambda: (["rows", "company"], [[int((etl1_rows()[2].Ticker.str.strip() == "").sum()),
                                            *etl1_rows()[2][etl1_rows()[2].Ticker.str.strip() == ""].Name.unique()]]),
    "Q031": lambda: (["company", "ticker"], [[n, g.Ticker.str.replace(" ", "").unique()[0]]
                                            for n, g in etl1_rows()[2].groupby("Name")
                                            if g.Ticker.nunique() == 3 and g.Ticker.str.replace(" ", "").nunique() == 1]),
    "Q032": lambda: one("rows", int(etl1_rows()[2].Inventories.str.strip().isin(["", "-"]).sum())),
    "Q033": lambda: one("count", int((etl2().Location == "GER").sum())),
    "Q034": lambda: one("count", int((etl2().Location == "JAP").sum())),
    "Q035": lambda: one("count", int((etl2().Location == "USA").sum())),
    "Q036": lambda: (["min", "max"], [[etl2().EmpID.min(), etl2().EmpID.max()]]),
    "Q037": lambda: one("distinct", etl2().LocationPlantID.nunique()),
    "Q038": lambda: one("count", int((etl2().PayPeriod == "W").sum())),
    "Q039": lambda: top(etl2().LocationPlantID.value_counts(), "LocationPlantID", "count"),
    "Q040": lambda: one("count", int((etl3().Location == "Canada").sum())),
    "Q041": lambda: one("count", int((etl3().Location == "Japan").sum())),
    "Q042": lambda: one("count", int(etl3().PayPeriod.str.startswith("M").sum())),
    "Q043": lambda: one("max", etl3().PlantID.max()),
    "Q044": lambda: one("distinct", etl3().LocationPlantID.nunique()),
    "Q045": lambda: one("GLAccountName", etl4()["ChartOfAccounts"].set_index("GLAccountNumber")
                        .loc[43440, "GLAccountName"]),
    "Q046": lambda: one("debit", round(je_with("BusinessUnits", "BusinessUnitID", ["BusinessUnit"])
                                       .query("BusinessUnit == 'HOTEL'").Debit.sum(), 2)),
    "Q047": lambda: one("debit", round(je_with("BusinessUnits", "BusinessUnitID", ["BusinessUnit"])
                                       .query("BusinessUnit == 'FOOD SERVICE'").Debit.sum(), 2)),
    "Q048": lambda: one("preparer", etl4()["PreparerInfo"].query("PreparerID == 102 and BusinessUnitID == 2")
                        .PreparerName.iloc[0].split("|")[0]),
    "Q049": lambda: one("lines", int((je_with("Source", "SourceID", ["Source"]).Source == "PURCHASE CARD").sum())),
    "Q050": lambda: one("lines", int((je_with("Source", "SourceID", ["Source"]).Source == "CHECK").sum())),
    "Q051": lambda: one("sum", round(etl4()["JELineItems"].Amount.sum(), 2)),
    "Q052": lambda: one("amount", round(je_with("ChartOfAccounts", "GLAccountNumber", ["AccountType"])
                                        .query("AccountType == 'Revenue'").Amount.sum(), 2)),
    "Q053": lambda: one("rows", len(p15())),
    "Q054": lambda: one("rows", len(p16())),
    "Q055": lambda: one("rows", int((p15().Code == "005").sum())),
    "Q056": lambda: (["Job", "rows"], [[j, n] for j, n in p15()[~p15().Code.isin(
        [f"{i:03d}" for i in range(1, 13)])].Job.value_counts().items()]),
    "Q057": lambda: gross_by_code("001"),
    "Q058": lambda: gross_by_code("009"),
    "Q059": lambda: one("gross_wages", round(p16().loc[p16().Code == "009", "Gross_Wages"].sum(), 2)),
    "Q060": lambda: one("increase", round(p16().Gross_Wages.sum() - p15().Gross.sum(), 2)),
    "Q061": lambda: one("per_hour", round(p15().loc[p15().Code == "005", "Gross"].sum()
                                          / p15().loc[p15().Code == "005", "Hrs"].sum(), 2)),
    "Q062": lambda: (lambda s: (["Emp_No", "Name", "OT_Pay"], [[*s.index[0], round(s.iloc[0], 2)]]))(
        p15()[p15().Date.dt.month <= 6].groupby(["Emp_No", "Name"]).OT_Pay.sum().sort_values(ascending=False)),
    "Q063": lambda: top(p15().groupby("Code").OT_Pay.sum().round(2), "Code", "OT_Pay"),
    "Q064": lambda: (["rows", "gross_wages"], [[int(p16().Employee_Number.isna().sum()),
                                                round(p16()[p16().Employee_Number.isna()].Gross_Wages.sum(), 2)]]),
    "Q065": lambda: one("combinations", int(p15().groupby(["First_Name", "Last_Name", "Pay_Date"])[
        ["Reg_Hrs", "OT_Hrs"]].sum().query("OT_Hrs > 0 and Reg_Hrs < 40").shape[0])),
    "Q066": lambda: one("cost", round(p16()[["Gross_Wages", "SocSec_Medicare", "FUTA", "SUTA",
                                             "Work_Comp"]].sum().sum(), 2)),
    "Q067": lambda: one("gross", round(with_loc(p15(), "Name").query("Location == 1").Gross.sum(), 2)),
    "Q068": lambda: one("gross", round(with_loc(p15(), "Name").query("Location == 2").Gross.sum(), 2)),
    "Q069": lambda: (lambda m: one("per_hour", round(m.Gross_Wages.sum() / m.Hrs.sum(), 2)))(
        with_loc(p16().dropna(subset=["Employee_Name"]), "Employee_Name").query("Location == 1")),
    "Q070": lambda: (lambda d: one("percent", round(d.loc[d.Code == "001", "Gross_Wages"].sum()
                                                    / d.Gross_Wages.sum() * 100, 2)))(
        p16()[p16().Employee_Name == "Dale Hamilton"]),
    "Q071": lambda: (lambda m: (["month", "above_average"], [[int(m.idxmax()), round(m.max() - m.mean(), 2)]]))(
        monthly15()),
    "Q072": lambda: one("march", round(monthly15()[3] / monthly15().sum() * p16().Gross_Wages.sum(), 2)),
    "Q073": lambda: one("combinations", len(
        p15().groupby(["Emp_No", "Code"])[["Hrs", "Gross"]].sum().query("Hrs > 0 and Gross > 0").index.intersection(
            p16().dropna(subset=["Employee_Number"]).astype({"Employee_Number": int})
            .groupby(["Employee_Number", "Code"])[["Hrs", "Gross_Wages"]].sum()
            .query("Hrs > 0 and Gross_Wages > 0").index))),
    "Q074": lambda: (["pay_dates", "payroll_ids"], [[p15().Pay_Date.nunique(), p15().Payroll_ID.nunique()]]),
    "Q075": lambda: one("sales", daily().set_index("date").loc["2018-12-31", "sales"]),
    "Q076": lambda: one("sales", daily().set_index("date").loc["2018-01-08", "sales"]),
    "Q077": lambda: (["dates", "short_dates"], [[len(daily()), int((daily()["items"] < 15).sum())]]),
    "Q078": lambda: top(daily().set_index("date").sales, "date", "sales"),
    "Q079": lambda: one("tmax", daily().loc[daily().sales.idxmax(), "tmax"]),
    "Q080": lambda: one("average", round(daily().query("gameDay == 1").sales.mean(), 2)),
    "Q081": lambda: one("average", round(daily().query("gameDay == 0").sales.mean(), 2)),
    "Q082": lambda: one("missing_prcp", int(wb("restaurant_data", "weatherData").prcp.isna().sum())),
}


@cache
def sheet_headers(ds, sheet):
    meta = next(s for s in dataset_index()[ds]["sheets"] if s["name"] == sheet)
    w = openpyxl.load_workbook(P(ds), read_only=True, data_only=True)
    try:
        row = next(w[sheet].iter_rows(min_row=meta["header_row"], max_row=meta["header_row"], values_only=True))
    finally:
        w.close()
    return [h for h in row if h is not None]


@cache
def csv_headers(ds):
    meta = dataset_index()[ds]
    delim = {"pipe": "|", "comma": ",", "semicolon": ";", "tab": "\t"}[meta["delimiter"]]
    with open(P(ds), encoding=meta.get("encoding", "utf-8"), newline="") as f:
        return next(csv.reader(io.StringIO(f.readline()), delimiter=delim))


def check_excel(q):
    errs, notes = [], []
    ro = q["required_objects"]
    found = []
    for ds in q["dataset_ids"]:
        meta = dataset_index()[ds]
        if "sheets" in meta:
            names = {s["name"] for s in meta["sheets"]}
            wanted = [s for s in ro["sheets"] if s in names]
            for s in wanted:
                found += sheet_headers(ds, s)
        else:
            found += csv_headers(ds)
            if meta.get("delimiter") == "pipe" and "pipe" not in q["prompt"].lower():
                errs.append(f"{meta['file']} is pipe-delimited but the prompt does not say an import step is needed")
    all_sheets = {s["name"] for ds in q["dataset_ids"] for s in dataset_index()[ds].get("sheets", [])}
    for s in ro["sheets"]:
        if s not in all_sheets:
            errs.append(f"sheet {s!r} missing")
    for h in ro["headers"]:
        if h not in found:
            near = [f for f in found if str(f).strip().casefold() == h.strip().casefold()]
            errs.append(f"header {h!r} missing" + (f" (near miss: {near[0]!r})" if near else ""))
    fn = EXCEL.get(q["id"])
    if fn is None:
        if DECISIONS.get(q["id"], ("",))[0] != "manual_check":
            errs.append("no independent computation defined")
        return errs, notes
    try:
        cols, rows = fn()
    except Exception as e:  # noqa: BLE001
        return errs + [f"computation fails: {e}"], notes
    cols, rows = canon(cols, rows, ordered=False)
    if not rows:
        errs.append("computed result is empty")
    ref = q["reference_solution"]
    if ref is not None and not ref_matches(ref, cols, rows):
        errs.append(f"computed {rows[:3]} does not match the materials' reference {ref!r}")
    save_expected(q["id"], cols, rows, False, note="Computed independently with pandas from the raw file.")
    return errs, notes


# ---------- interpretation ----------

def check_interpretation():
    import statsmodels.formula.api as smf
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_interpretation import load  # same data prep as the bank builder

    d = load()
    models = {m["id"]: m for m in json.loads(MODELS.read_text(encoding="utf-8"))}
    items = json.loads(INTERP.read_text(encoding="utf-8"))
    fits, results = {}, {}
    for mid, m in models.items():
        fit = smf.ols(m["formula"], data=d, missing="drop").fit()
        errs = [f"{n}: refit {round(fit.params[n], 4)} vs stored {c['coef']}"
                for n, c in m["coefficients"].items() if round(float(fit.params[n]), 4) != c["coef"]]
        if set(fit.params.index) != set(m["coefficients"]):
            errs.append("coefficient names differ")
        fits[mid] = (fit, d.loc[fit.model.data.row_labels], errs)

    def last_money(text):
        nums = re.findall(r"= (-?[\d,]+\.\d{2}) dollars", text)
        return float(nums[-1].replace(",", "")) if nums else None

    for it in items:
        if DECISIONS.get(it["id"], ("",))[0] == "excluded":
            results[it["id"]] = []
            continue
        fit, used, errs = fits[it["model_id"]]
        errs = list(errs)
        m = models[it["model_id"]]
        b = {n: c["coef"] for n, c in m["coefficients"].items()}
        if f"n = {int(fit.nobs)}," not in it["prompt"] or f"R squared = {round(fit.rsquared, 4)})" not in it["prompt"]:
            errs.append("n or R squared in the prompt differs from the refit")
        if it["kind"] == "predict" or (it["kind"] == "dummy" and it["inputs"]):
            for v, x in it["inputs"].items():
                if not used[v].min() <= x <= used[v].max():
                    errs.append(f"{v} = {x} outside observed range {used[v].min()} to {used[v].max()}")
        if it["kind"] == "predict":
            total = b["Intercept"]
            for n in b:
                if n != "Intercept":
                    x = 1.0
                    for part in n.split(":"):
                        x *= it["inputs"][part]
                    total += b[n] * x
            if last_money(it["worked_answer"]) != round(total, 2):
                errs.append(f"worked answer {last_money(it['worked_answer'])} vs recomputed {round(total, 2)}")
        elif it["kind"] == "dummy" and it["inputs"]:
            (cv, x), = it["inputs"].items()
            inter = next(n for n in b if ":" in n)
            dv = next(p for p in inter.split(":") if p != cv)
            eff = b[dv] + b[inter] * x
            if last_money(it["worked_answer"]) != round(eff, 2):
                errs.append(f"worked answer {last_money(it['worked_answer'])} vs recomputed {round(eff, 2)}")
        else:
            mm = re.search(r"coefficient on (\S+?)(?: is | \()(-?[\d.]+(?:e-?\d+)?)", it["prompt"])
            if not mm:
                errs.append("could not find the coefficient in the prompt")
            else:
                n, val = mm.group(1), float(mm.group(2))
                if round(float(fit.params[n]), 4) != val:
                    errs.append(f"coefficient on {n} in prompt {val} vs refit {round(float(fit.params[n]), 4)}")
                if it["kind"] == "significance":
                    want = "significant" if fit.pvalues[n] < 0.05 else "not significant"
                    if it["significance_verdict"] != want:
                        errs.append(f"verdict {it['significance_verdict']!r} but p = {fit.pvalues[n]:.4g}")
                    if f"p-value {fit.pvalues[n]:.4g}" not in it["prompt"]:
                        errs.append("p-value in prompt differs from the refit")
        results[it["id"]] = errs
    return items, results


# ---------- main ----------

def main():
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    datasets = dataset_index()
    counts = Counter(q["id"] for q in questions)
    ids = set(counts)
    failures, statuses = {}, {}
    for q in questions:
        qid = q["id"]
        errs = [f"duplicate id {qid}"] if counts[qid] > 1 else []
        errs += structural(q, ids, datasets)
        decided = DECISIONS.get(qid)
        if decided and decided[0] == "excluded":
            statuses[qid] = "excluded"
            continue
        if not errs:
            try:
                e, _ = (check_sql if q["subject"] == "SQL" else check_excel)(q)
            except Exception as ex:  # noqa: BLE001
                e = [f"check crashed: {ex}"]
            errs += e
        if decided and decided[0] == "disputed":
            # The reference mismatch is the documented dispute; anything else still fails.
            errs = [e for e in errs if "materials' reference" not in e]
            statuses[qid] = "disputed" if not errs else "failed"
        elif decided and decided[0] == "manual_check":
            statuses[qid] = "manual_check" if not errs else "failed"
        else:
            statuses[qid] = "validated" if not errs else "failed"
        if errs:
            failures[qid] = errs

    items, iresults = check_interpretation()
    for it in items:
        decided = DECISIONS.get(it["id"])
        if decided and decided[0] == "excluded":
            statuses[it["id"]] = "excluded"
        elif iresults[it["id"]]:
            statuses[it["id"]] = "failed"
            failures[it["id"]] = iresults[it["id"]]
        else:
            statuses[it["id"]] = "validated"

    for q in questions:
        q["status"] = statuses[q["id"]]
    for it in items:
        it["status"] = statuses[it["id"]]
    QUESTIONS.write_text(json.dumps(questions, indent=1, ensure_ascii=False), encoding="utf-8")
    INTERP.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")

    write_report(questions, items, statuses, failures)
    by = Counter(statuses.values())
    total = len(questions) + len(items)
    print(f"{total} checked: {by['validated']} validated, {by['manual_check']} manual_check, "
          f"{by['disputed']} disputed, {by['excluded']} excluded, {by['failed']} failed. See VALIDATION_REPORT.md")
    return 1 if by["failed"] else 0


def write_report(questions, items, statuses, failures):
    subjects = {q["id"]: q["subject"] for q in questions} | {it["id"]: "Interpretation" for it in items}
    files = {q["id"]: ", ".join(dataset_index()[d]["file"] for d in q["dataset_ids"] if d in dataset_index())
             for q in questions} | {it["id"]: "data.xlsm" for it in items}
    cols = ["validated", "manual_check", "disputed", "excluded", "failed"]
    out = ["# Validation report", "",
           "Written by `py tests\\validate.py`. Re-run it after editing the bank; this file is replaced each time.",
           "", "## Summary", "", "| Subject | " + " | ".join(cols) + " | Total |",
           "|---|" + "---:|" * (len(cols) + 1)]
    for subj in ["Excel", "SQL", "Interpretation"]:
        c = Counter(statuses[i] for i, s in subjects.items() if s == subj)
        out.append(f"| {subj} | " + " | ".join(str(c[k]) for k in cols) + f" | {sum(c.values())} |")
    c = Counter(statuses.values())
    out.append("| All | " + " | ".join(str(c[k]) for k in cols) + f" | {sum(c.values())} |")

    out += ["", "## Questions that are not validated", ""]
    rows = [i for i in subjects if statuses[i] != "validated"]
    if not rows:
        out.append("None.")
    else:
        out += ["| Id | Status | File | What failed and why |", "|---|---|---|---|"]
        for i in rows:
            why = [DECISIONS[i][1]] if i in DECISIONS else []
            why += failures.get(i, [])
            out.append(f"| {i} | {statuses[i]} | {files[i]} | " + "<br>".join(w.replace("|", "\\|") for w in why) + " |")

    out += ["", "## Fixes made to generated drafts", ""]
    if FIXES:
        out += ["| Id | Problem | Fix |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in FIXES]
    else:
        out.append("None.")

    out += ["", "## Observations (no change made)", ""] + [f"- {o}" for o in OBSERVATIONS]

    out += ["", "## Exams", ""]
    exams_file = BANK / "exams.json"
    if exams_file.exists():
        ex = json.loads(exams_file.read_text(encoding="utf-8"))
        kinds = Counter(e["type"] for e in ex["exams"])
        out.append(f"Seed {ex['seed']}. Data manipulation exams: {kinds['manipulation']}. "
                   f"Data interpretation exams: {kinds['interpretation']}. Built by `py scripts\\build_exams.py`.")
        for pair, n in ex.get("pairs", {}).items():
            out.append(f"- {pair}: {n}")
    else:
        out.append("Not built yet (`py scripts\\build_exams.py`).")
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
