"""Fit the restaurant regressions on data.xlsm and write bank/models.json and bank/interpretation.json.

Data prep follows the ETL step in Instructions.docx: aggregate salesData to one row per date (sum over menu items),
merge weatherData on date, merge gameData on date and set gameDay/homeGame to 0 on dates without a game.
Worked answers use coefficients rounded to 4 decimals, so the arithmetic shown is exactly reproducible.
"""
import json
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "materials" / "1. Excel part 4" / "Regression Assignment" / "Restaurant" / "data.xlsm"
DOC = "1. Excel part 4/Regression Assignment/Restaurant/Instructions.docx"

VARS = {
    "sales": ("Total before-tax net sales of all menu items on the day (sum of netTotal over items)", "dollars"),
    "sales_7": ("Total net sales 7 days earlier (sum of netTotal_7 over items)", "dollars"),
    "sales_28": ("Total net sales 28 days earlier (sum of netTotal_28 over items)", "dollars"),
    "sales_364": ("Total net sales 364 days earlier, the same weekday last year (sum of netTotal_364 over items)",
                  "dollars"),
    "tmax": ("Maximum temperature during the day", "degrees Fahrenheit"),
    "prcp": ("Total precipitation during the day", "inches"),
    "gameDay": ("1 if there is a university football game on the date, 0 otherwise", "dummy"),
    "homeGame": ("1 if there is a home game on the date, 0 otherwise (away games and days without a game are 0)",
                 "dummy"),
}
DUMMY_REF = {"gameDay": "days without a game", "homeGame": "days without a home game (no game or an away game)"}
DUMMY_ON = {"gameDay": "game days", "homeGame": "home game days"}

# Models the instructions ask for (M1 to M4), then extra specifications on the same data (M5 to M8).
SPECS = [
    ("M1", "sales ~ sales_7 + sales_364", "Instructions: predict aggregated sales 7 days from the last day of data", True),
    ("M2", "sales ~ tmax", "Instructions: are sales affected by temperature?", True),
    ("M3", "sales ~ gameDay", "Instructions: does a game day affect sales?", True),
    ("M4", "sales ~ sales_364 * gameDay", "Instructions: how sales one year ago interact with a game day", True),
    ("M5", "sales ~ tmax + prcp + gameDay", "Extra: weather and game day together", False),
    ("M6", "sales ~ sales_7 + sales_28 + sales_364", "Extra: all three lagged sales measures", False),
    ("M7", "sales ~ homeGame", "Extra: home games only", False),
    ("M8", "sales ~ sales_364 + gameDay", "Extra: game day and last year's sales without interaction", False),
]


def load():
    x = pd.read_excel(DATA, sheet_name=None)  # openpyxl reads values only; macros are never run
    s = x["salesData"]
    daily = s.groupby("date").agg(sales=("netTotal", "sum"), sales_7=("netTotal_7", "sum"),
                                  sales_28=("netTotal_28", "sum"), sales_364=("netTotal_364", "sum"),
                                  items=("LineItem", "count")).reset_index()
    daily = daily.merge(x["weatherData"], on="date", how="left")
    daily = daily.merge(x["gameData"][["date", "gameDay", "homeGame"]], on="date", how="left")
    daily[["gameDay", "homeGame"]] = daily[["gameDay", "homeGame"]].fillna(0).astype(int)
    return daily


def r4(v):
    return round(float(v), 4)


def money(v):
    return f"{v:,.2f}"


def main():
    d = load()
    models, items = [], []

    def add(kind, mid, prompt, answer, inputs=None, verdict=None):
        items.append({"id": f"I{len(items) + 1:03d}", "kind": kind, "model_id": mid, "prompt": prompt,
                      "worked_answer": answer, "inputs": inputs or {}, "significance_verdict": verdict})

    for mid, formula, purpose, asked in SPECS:
        fit = smf.ols(formula, data=d, missing="drop").fit()
        used = d.loc[fit.model.data.row_labels]
        preds = [n for n in fit.params.index if n != "Intercept"]
        raw = sorted({p for n in preds for p in n.split(":")})
        ranges = {v: {"min": r4(used[v].min()), "max": r4(used[v].max()), "median": r4(used[v].median())}
                  for v in raw + ["sales"]}
        coefs = {n: {"coef": r4(fit.params[n]), "se": r4(fit.bse[n]), "p": float(f"{fit.pvalues[n]:.6g}")}
                 for n in fit.params.index}
        models.append({
            "id": mid, "formula": formula, "purpose": purpose, "asked_in_instructions": asked, "source_doc": DOC,
            "n": int(fit.nobs), "r_squared": r4(fit.rsquared), "adj_r_squared": r4(fit.rsquared_adj),
            "coefficients": coefs,
            "variables": {v: {"definition": VARS[v][0], "unit": VARS[v][1], **ranges[v]} for v in raw + ["sales"]},
            "dummy_coding": {v: {"1": DUMMY_ON[v], "0 (reference)": DUMMY_REF[v]} for v in raw if v in DUMMY_REF},
            "data_prep": "salesData summed by date; weatherData and gameData merged on date; dates without a game "
                         "get gameDay = 0 and homeGame = 0; rows with a missing predictor are dropped.",
        })
        b = {n: coefs[n]["coef"] for n in coefs}
        eq = f"sales = {b['Intercept']}" + "".join(f" + {b[n]} x {n}" for n in preds)
        head = f"Model {mid}: {formula.replace('*', 'x')} (OLS, n = {int(fit.nobs)}, R squared = {r4(fit.rsquared)}). "

        # Predict at observed values.
        cont = [v for v in raw if v not in DUMMY_REF]
        points = []
        if mid == "M1":
            last = d["date"].max()
            target = last + pd.Timedelta(days=7)
            lag364 = target - pd.Timedelta(days=364)
            vals = {"sales_7": float(d.loc[d.date == last, "sales"].iloc[0]),
                    "sales_364": float(d.loc[d.date == lag364, "sales"].iloc[0])}
            points.append((vals, f"Bob wants sales for {target:%d.%m.%Y}, 7 days after the last day of data "
                                 f"({last:%d.%m.%Y}). Sales on {last:%d.%m.%Y} were {money(vals['sales_7'])} dollars "
                                 f"and sales on {lag364:%d.%m.%Y} (364 days before the target) were "
                                 f"{money(vals['sales_364'])} dollars."))
        if cont:
            for q in (0.25, 0.75):
                vals = {v: round(float(used[v].quantile(q)), 0 if v.startswith("sales") or v == "tmax" else 2)
                        for v in cont}
                vals.update({v: (1 if q == 0.75 else 0) for v in raw if v in DUMMY_REF})
                points.append((vals, None))
        else:
            for v in raw:
                points += [({v: 1}, None), ({v: 0}, None)]
        for vals, story in points:
            for v, x in vals.items():
                assert ranges[v]["min"] <= x <= ranges[v]["max"], (mid, v, x)
            terms, total = [f"{b['Intercept']}"], b["Intercept"]
            for n in preds:
                x = 1.0
                for part in n.split(":"):
                    x *= vals[part]
                terms.append(f"{b[n]} x {x:g}")
                total += b[n] * x
            given = ", ".join(f"{v} = {vals[v]:g} {VARS[v][1] if VARS[v][1] != 'dummy' else ''}".strip()
                              for v in raw)
            rng = "; ".join(f"{v} observed from {ranges[v]['min']:g} to {ranges[v]['max']:g}" for v in raw)
            add("predict", mid, head + (story + " " if story else "") +
                f"Predict daily sales for {given}. ({rng}.)",
                f"{eq}. Predicted sales = {' + '.join(terms)} = {money(total)} dollars.",
                inputs=vals)

        for n in preds:
            c, p = coefs[n], coefs[n]["p"]
            sig = p < 0.05
            verdict = "significant" if sig else "not significant"
            add("significance", mid, head + f"The coefficient on {n} is {c['coef']} with standard error {c['se']} "
                                            f"and p-value {p:.4g}. Is it statistically significant at the 5 % level?",
                f"p = {p:.4g} is {'below' if sig else 'not below'} 0.05, so the coefficient on {n} is {verdict} at "
                f"the 5 % level: we {'reject' if sig else 'cannot reject'} the null hypothesis that its true value "
                f"is zero.", verdict=verdict)
            if ":" in n:
                cv, dv = [v for v in n.split(":") if v not in DUMMY_REF][0], [v for v in n.split(":") if v in DUMMY_REF][0]
                x = ranges[cv]["median"]
                eff = b[dv] + b[n] * x
                add("dummy", mid, head + f"Explain what the interaction {n} means, and give the difference in "
                                         f"predicted sales between {DUMMY_ON[dv]} and {DUMMY_REF[dv]} when {cv} = "
                                         f"{x:g} dollars ({cv} observed from {ranges[cv]['min']:g} to "
                                         f"{ranges[cv]['max']:g}).",
                    f"The effect of a {dv} depends on {cv}: on {DUMMY_ON[dv]} each extra dollar of {cv} changes "
                    f"predicted sales by {b[cv]} + {b[n]} = {r4(b[cv] + b[n])} dollars instead of {b[cv]}. "
                    f"Difference at {cv} = {x:g}: {b[dv]} + {b[n]} x {x:g} = {money(eff)} dollars.",
                    inputs={cv: x})
            elif n in DUMMY_REF:
                interacted = [p for p in preds if ":" in p and n in p.split(":")]
                if interacted:
                    cv = [v for v in interacted[0].split(":") if v != n][0]
                    cond = (f"When {cv} is 0, predicted daily sales on {DUMMY_ON[n]} are {money(abs(c['coef']))} "
                            f"dollars {'higher' if c['coef'] > 0 else 'lower'} than on {DUMMY_REF[n]}. Because of "
                            f"the interaction, the gap at other values of {cv} is {c['coef']} + "
                            f"{b[interacted[0]]} x {cv}.")
                else:
                    others = "Holding the other variables in the model constant, p" if len(preds) > 1 else "P"
                    cond = (f"{others}redicted daily sales on {DUMMY_ON[n]} are {money(abs(c['coef']))} dollars "
                            f"{'higher' if c['coef'] > 0 else 'lower'} than on {DUMMY_REF[n]}.")
                add("dummy", mid, head + f"Explain the coefficient on {n} ({c['coef']}) against its reference "
                                         f"group.",
                    f"{n} is 1 on {DUMMY_ON[n]} and 0 on {DUMMY_REF[n]}, the reference group. " + cond)
            else:
                unit = VARS[n][1]
                step = "dollar" if unit == "dollars" else {"degrees Fahrenheit": "degree Fahrenheit",
                                                           "inches": "inch"}[unit]
                definition = VARS[n][0][0].lower() + VARS[n][0][1:]
                if any(":" in p for p in preds):
                    cond = f" On {DUMMY_REF['gameDay']} (gameDay = 0), because the model has an interaction, each"
                elif len(preds) > 1:
                    cond = " Holding the other variables in the model constant, each"
                else:
                    cond = " Each"
                add("coefficient", mid, head + f"Interpret the coefficient on {n} ({c['coef']}) in words, with units.",
                    f"{n} is the {definition}.{cond} additional {step} of {n} goes with predicted daily sales "
                    f"that are {abs(c['coef'])} dollars {'higher' if c['coef'] > 0 else 'lower'}.")

    (ROOT / "bank" / "models.json").write_text(json.dumps(models, indent=1), encoding="utf-8")
    (ROOT / "bank" / "interpretation.json").write_text(json.dumps(items, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(models), "models;", len(items), "items", dict(Counter(i["kind"] for i in items)))


if __name__ == "__main__":
    main()
