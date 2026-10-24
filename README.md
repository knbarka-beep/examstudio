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

## Where the improvement goes

Every question view (exam and question bank, data manipulation and data interpretation) has an empty `<section id="improvement-slot" hidden>` directly under the prompt. `docs/js/app.js` calls `initImprovement(context)` from `docs/js/improvement.js` after each question is shown, only when `docs/data/config.json` has `"improvementEnabled": true`. The context is `{ question, exam, datasets, config, slot }`. Both places are marked `// IMPROVEMENT: Knut adds his feature here`. The expected results in `bank/expected/` are there for a later feature to use; they are not part of the site.

[[KNUT: paragraph on the added functionality and why it improves on the lecturer's site]]

## The starting materials

[[KNUT: paragraph on how the starting materials made this case harder than earlier cases, see MATERIALS_NOTES.md]]
