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
| `docs/` | The published site (GitHub Pages serves `main` /docs): `index.html`, `css/`, `js/app.js`, `js/improvement.js` (answer check), `js/examiner.js` (exam mode), `improvement-evidence.md` |
| `docs/data/` | Public JSON built by `scripts/build_site.py`: `questions.json`, `exams.json`, `interpretation.json`, `datasets.json`, `checks.json`, `probes.json`, `config.json` |
| `docs/files/` | The student data files under 50 MB, copied unchanged from the course materials |
| `bank/` | The full question bank, exams, regression models and expected results (`bank/expected/`), used to build and validate the site |
| `scripts/` | Build scripts |
| `tests/` | `validate.py` (checks every question against the data) and `smoke.py` (checks the published site) |
| `prompts/` | The prompts for the Claude Code runs |
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

From `VALIDATION_REPORT.md` (01.11.2026):

| Subject | validated | manual_check | disputed | excluded | Total |
|---|---:|---:|---:|---:|---:|
| Excel | 78 | 4 | 0 | 0 | 82 |
| SQL | 97 | 0 | 0 | 0 | 97 |
| Interpretation | 49 | 0 | 0 | 0 | 49 |
| All | 224 | 4 | 0 | 0 | 228 |

Only validated and manual_check questions are on the site. Two questions were disputed until 01.11.2026 and are now back on the site. Q015 (NYC question 13) had two valid years, 2017 and 2018; the prompt now says to count full calendar years only (the data stops in February 2018), so 2017 is the one answer, as in `solutions.xlsx`. Q108 (PWC question 22): `PWC answers.docx` gives 49, which counts complete-album purchases (8 albums were bought complete twice), while the question asks for distinct albums; the expected answer is now 41 (`solution_source: "generated"`), and 49 is a computed trap. There are 303 data manipulation exams and 30 data interpretation exams.

## Manual step: upload release assets

Two databases are over 50 MB, so they are not in git. `py scripts\build_site.py` zips them into `release-assets/`. Upload both files to a GitHub release with the tag `datasets-v1` (Releases, Draft a new release, tag `datasets-v1`, attach the files, publish). The site links to `https://github.com/knbarka-beep/examstudio/releases/download/datasets-v1/<file>`.

| File | Original | Size of the original | Size of the zip |
|---|---|---:|---:|
| `movies.zip` | `movies.db` (CS50 movies database) | 68,939,776 bytes (68.9 MB) | 39,419,579 bytes (39.4 MB) |
| `pcards.zip` | `pcards.db` (Oklahoma P-card transactions) | 94,003,200 bytes (94.0 MB) | 22,048,698 bytes (22.0 MB) |

## The improvement: answer check with trap answers

Every single-value question (in the bank and in exams) gets a box under the prompt. The typed answer is compared with the answer computed from the data, accepting European and US number formats, percentages as 8%, 8 or 0.08, and dates as 07.12.2011 16:38 or 2011-12-07 16:38. If it matches a computed trap answer, the site names the trap and explains it. Data: `docs/data/checks.json`, built by `py scripts\build_checks.py` (after `py tests\validate.py`). Overview of all traps: `TRAPS.md`. Test: `node tests/check_answers.mjs`. The code is `docs/js/improvement.js` and `docs/css/improvement.css`; it is switched on by `"improvementEnabled": true` in `docs/data/config.json`. Expected answers are readable in `checks.json`. That is deliberate: this is a practice site whose questions are meant to be the exam questions.

My added functionality is an answer check that recognises trap answers. Your website lets students practise the exams and ask the AI tutor for help, but it never tells them whether the number they got is right. In Data Analytics in Accounting the hard part was rarely finding a number. It was getting one that looks right but is wrong: averaging menu-item rows instead of days, looking up PreparerID 102 without BusinessUnitID, comparing 2016 Gross_Wages with 2015 Reg_Pay only, or using > where the question says "or more". A student who makes one of these mistakes feels finished and brings the wrong method to the exam. On my site the student types the result, and it is compared with the answer computed from the data. If it matches a known wrong method, the site names the trap and explains why the method fails. The traps are not guessed. Each one is computed from the raw data with the wrong method (`scripts/build_checks.py`) and kept only if it differs from the right answer. 105 of the 179 questions get a check, 37 of them have at least one computed trap, and 246 of the 303 manipulation exams contain at least one trap question. An AI tutor cannot do this reliably, because it never ran the query on the 489,178 P-card rows, and none of the 70 AI suggestions mentions checking the student's result.

## Exam mode

Exam mode (nav: Exam mode) gives one task at a time from Excel, SQL, regression interpretation or a mix, with a timer of 8 or 10 minutes and a rules-based examiner that asks follow-up questions while you work. There is no AI model behind it. The examiner picks its questions from `docs/data/probes.json`: a trap probe when the answer box, or a number said in the transcript, matches a computed trap answer from the answer check; a question probe tied to the task's skills; a trigger probe when you say or type a term such as JOIN, VLOOKUP, GROUP BY or "causes"; and a generic "why" probe when nothing else applies. Answers under 15 words or without a reasoning word (because, so, since, otherwise, which means, the reason) count as thin and get a pushback. Three strictness presets (Supportive, Standard, Strict) set how often and how soon it cuts in, with at least 20 seconds between interruptions. After each task the debrief shows the transcript with time stamps, the probes asked, thin answers, trap tags, the expected answer, a self-assessment (practice, not a grade) and "Practise my weak spots", which starts a task tied to the most flagged tag. Counts from the data are in `docs/improvement-evidence.md`. The code is `docs/js/examiner.js`; it is switched on and off together with the answer check by `"improvementEnabled"` in `docs/data/config.json`.

Voice: the examiner speaks with the browser's speech synthesis, and you answer by microphone with the Web Speech API. Speech recognition works in Chrome and Edge on desktop and in recent Safari; Firefox has none, and the site then falls back to the text box, which is always available.

Privacy: nothing is stored or sent by the site (no localStorage, no server, no accounts, no analytics), but in Chrome and Edge the browser itself sends microphone audio to its vendor's speech service (Google or Microsoft), so do not say anything confidential.

<!-- KNUT: write this yourself -->
[KNUT: your text here] [[KNUT: why I built exam mode and how it relates to my own exam preparation]]

## The starting materials

The earlier cases each came with one dataset and one task. This one came with 31 files in eight formats across seven cases, and most of the work was turning them into questions that can be checked at all. Files did not match their descriptions. The IntegrateCo .csv files are pipe-delimited, ETL Case 1 breaks on the unquoted comma in "Apple, Inc.", the Excel assignment asks for a NYC_Film_Permits.csv that does not exist, and the P-card case is written for six CSV files that were replaced by a 94 MB database with dates stored as text. The 2015 and 2016 payroll files have different columns and a different grain, so even "how much did pay rise" needs both years rebuilt into one measure first. The solutions were uneven too. Some were complete, some were only images, three "solution" sheets were empty templates, and two answers disagree with the data: NYC question 13 has two valid years, and PWC question 22 says 49 albums where the data gives 41 distinct ones. So I could not copy answers. Every answer was recomputed from the raw files and checked against the materials (222 of 228 match, 4 need a person to judge, and the 2 disputed questions are left off the site). Finally, there was no list of requirements to meet, only a website to beat, so deciding what was worth building became part of the task.
