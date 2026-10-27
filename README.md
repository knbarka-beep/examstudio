# ExamStudio practice site

A practice website for the course Data Analytics in Accounting, with timed data manipulation exams (Excel and SQL), a searchable question bank and timed data interpretation exams on regression output. All questions are built from the course cases and their data files, and checked against the data before they are published.

Live site: https://knbarka-beep.github.io/examstudio/

## Run it locally

```
py -m http.server 8000 --directory docs
```

Then open http://localhost:8000. The site loads its data with `fetch`, so opening `docs/index.html` directly from disk does not work.

## Repository structure

| Path | What it holds |
|---|---|
| `docs/` | The published site (GitHub Pages serves `main` /docs): `index.html`, `css/style.css`, `js/app.js`, `js/improvement.js` |
| `docs/data/` | Public JSON built by `scripts/build_site.py`: `questions.json`, `exams.json`, `interpretation.json`, `datasets.json`, `config.json` |
| `docs/files/` | The student data files under 50 MB, copied unchanged from the course materials |
| `bank/` | The full question bank, exams, regression models and expected results (`bank/expected/`), used to build and validate the site |
| `scripts/` | Build scripts |
| `tests/` | `validate.py` (checks every question against the data) and `smoke.py` (checks the published site) |
| `prompts/` | The prompts for the three unattended Claude Code runs |
| `LOG.md`, `MATERIALS_NOTES.md`, `VALIDATION_REPORT.md` | Run log, notes on the course materials, validation results |

`materials/` (the local copy of the course materials) and `release-assets/` are not in git.

## How the content is built

```
py scripts\build_bank.py
py tests\validate.py
py scripts\build_exams.py
py scripts\build_site.py
py tests\smoke.py
```

1. `build_bank.py` writes the question bank (`bank/questions.json`) from the course cases.
2. `validate.py` runs every SQL answer against its database, computes every Excel answer independently with pandas, refits the regression models, and sets each question's status. It writes `VALIDATION_REPORT.md`.
3. `build_exams.py` composes the exams from validated questions with a fixed seed (2026), so the same exams come out every time. A data manipulation exam has three Excel questions on one file and two SQL questions on one database, 8 minutes in total; a data interpretation exam has four questions, 5 minutes.
4. `build_site.py` writes the public JSON to `docs/data/`, copies the data files to `docs/files/` and zips files over 50 MB into `release-assets/`. Reference solutions are left out unless `docs/data/config.json` has `"showReferenceSolutions": true`.

## Validation status

From `VALIDATION_REPORT.md` (23.10.2026):

| Subject | validated | manual_check | disputed | excluded | Total |
|---|---:|---:|---:|---:|---:|
| Excel | 77 | 4 | 1 | 0 | 82 |
| SQL | 96 | 0 | 1 | 0 | 97 |
| Interpretation | 49 | 0 | 0 | 0 | 49 |
| All | 222 | 4 | 2 | 0 | 228 |

Only validated and manual_check questions are on the site. The two disputed questions (Q015 and Q108) are left out because the reference answer in the materials does not match the data; the evidence is in the report. There are 304 data manipulation exams and 30 data interpretation exams.

## Manual step: upload release assets

Two databases are over 50 MB, so they are not in git. `py scripts\build_site.py` zips them into `release-assets/`. Upload both files to a GitHub release with the tag `datasets-v1` (Releases, Draft a new release, tag `datasets-v1`, attach the files, publish). The site links to `https://github.com/knbarka-beep/examstudio/releases/download/datasets-v1/<file>`.

| File | Original | Size of the original | Size of the zip |
|---|---|---:|---:|
| `movies.zip` | `movies.db` (CS50 movies database) | 68,939,776 bytes (68.9 MB) | 39,419,579 bytes (39.4 MB) |
| `pcards.zip` | `pcards.db` (Oklahoma P-card transactions) | 94,003,200 bytes (94.0 MB) | 22,048,698 bytes (22.0 MB) |

## The improvement: answer check with trap answers

Every single-value question (in the bank and in exams) gets a box under the prompt. The typed answer is compared with the answer computed from the data, accepting European and US number formats, percentages as 8%, 8 or 0.08, and dates as 07.12.2011 16:38 or 2011-12-07 16:38. If it matches a computed trap answer, the site names the trap and explains it. Data: `docs/data/checks.json`, built by `py scripts\build_checks.py` (after `py tests\validate.py`). Overview of all traps: `TRAPS.md`. Test: `node tests/check_answers.mjs`. The code is `docs/js/improvement.js` and `docs/css/improvement.css`; it is switched on by `"improvementEnabled": true` in `docs/data/config.json`. Expected answers are readable in `checks.json`. That is deliberate: this is a practice site whose questions are meant to be the exam questions.

My added functionality is an answer check that recognises trap answers. Your website lets students practise the exams and ask the AI tutor for help, but it never tells them whether the number they got is right. In Data Analytics in Accounting the hard part was rarely finding a number. It was getting one that looks right but is wrong: averaging menu-item rows instead of days, looking up PreparerID 102 without BusinessUnitID, comparing 2016 Gross_Wages with 2015 Reg_Pay only, or using > where the question says "or more". A student who makes one of these mistakes feels finished and brings the wrong method to the oral exam. On my site the student types the result, and it is compared with the answer computed from the data. If it matches a known wrong method, the site names the trap and explains why the method fails. The traps are not guessed. Each one is computed from the raw data with the wrong method (`scripts/build_checks.py`) and kept only if it differs from the right answer. 103 of the 177 questions get a check, 36 of them have at least one computed trap, and 240 of the 304 manipulation exams contain at least one trap question. An AI tutor cannot do this reliably, because it never ran the query on the 489,178 P-card rows, and none of the 70 AI suggestions mentions checking the student's result.

## The starting materials

The earlier cases each came with one dataset and one task. This one came with 31 files in eight formats across seven cases, and most of the work was turning them into questions that can be checked at all. Files did not match their descriptions. The IntegrateCo .csv files are pipe-delimited, ETL Case 1 breaks on the unquoted comma in "Apple, Inc.", the Excel assignment asks for a NYC_Film_Permits.csv that does not exist, and the P-card case is written for six CSV files that were replaced by a 94 MB database with dates stored as text. The 2015 and 2016 payroll files have different columns and a different grain, so even "how much did pay rise" needs both years rebuilt into one measure first. The solutions were uneven too. Some were complete, some were only images, three "solution" sheets were empty templates, and two answers disagree with the data: NYC question 13 has two valid years, and PWC question 22 says 49 albums where the data gives 41 distinct ones. So I could not copy answers. Every answer was recomputed from the raw files and checked against the materials (222 of 228 match, 4 need a person to judge, and the 2 disputed questions are left off the site). Finally, there was no list of requirements to meet, only a website to beat, so deciding what was worth building became part of the task.
