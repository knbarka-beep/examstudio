# LOG

## Active time (Knut)

[[KNUT: active time entries]]

## Unattended runs

### Run 1

Start: 23.10.2026 21:42:43 (from `runs/run1.txt`; Python was not available to take the timestamp)

- [ ] 1 repo setup
- [ ] 2 copy materials and locate missing files
- [ ] 3 inventory of every file
- [ ] 4 question bank
- [ ] 5 interpretation bank
- [ ] 6 MATERIALS_NOTES.md
- [ ] 7 local commit and log

Failed before step 1. Claude Code ignored the allow list in `.claude/settings.json` because the workspace has not been trusted, so every `py` and `git` command and every read of `MATERIALS_SRC` needed approval, which an unattended run cannot give. Nothing was created apart from this log.

Fix: run `claude` interactively in the repo root once and accept the trust dialog, then rerun with `run_all.ps1 -Only 1`. The run resumes from the checklist above.

#### Run 1, attempt 2

Start: 23.10.2026 21:48:03 (Python `datetime`, Europe/Copenhagen). No items were ticked, so the run starts at item 1.

- [x] 1 repo setup
- [x] 2 copy materials and locate missing files
- [x] 3 inventory of every file
- [x] 4 question bank
- [x] 5 interpretation bank
- [x] 6 MATERIALS_NOTES.md
- [x] 7 local commit and log

End: 23.10.2026 22:09:19. Duration: 21 minutes.

Done:
- `git init -b main`, remote `origin` set, not pushed. `.gitignore`, folders, packages installed.
- 31 files copied (184.5 MB), none failed or empty. `movies.db` and `pcards.db` were already in `MATERIALS_SRC`; `pcards.db` has table `pcards` with 489,178 rows. The third file outside the uploaded set is `NYC_Film_Permits.txt` (11.12 MB).
- Files inventoried: 31 (`bank/inventory.json`): 18 dataset, 9 instructions, 2 solution, 1 slides, 1 note. `docs/data/datasets.json`: 18 student data files.
- Questions: 179 in `bank/questions.json` (82 Excel, 97 SQL; 28 variants, 22 optional, 40 with a reference from the materials).
  - Excel Part 1: 25, Excel Part 2: 27, Excel Part 3: 22, Excel Part 4: 8
  - SQL Part 1 PWC: 27, SQL Part 1 CS50: 33 (6 optional Fiftyville), SQL Part 2 P-card: 37 (16 optional)
  - Every SQL draft was run once against its database: all run, the slowest takes about 5 seconds.
- Models: 8 OLS models on `data.xlsm` (`bank/models.json`); 4 asked for by the instructions, 4 extra.
- Interpretation questions: 49 (`bank/interpretation.json`): 17 predict, 16 significance, 10 coefficient, 6 dummy.

Failed or open:
- `bank/inventory.json` (full case texts and solution text) was committed in `d8c0bfd` and untracked in `a700716`. Not pushed, history not rewritten. [[KNUT: decide before Run 3 pushes whether to squash the local commits so the file is not in the public history. See MATERIALS_NOTES.md, "Git warning".]]
- Two references may disagree with the data (NYC Q13, PWC Q22); left for Run 2 to check. See MATERIALS_NOTES.md, assumptions 8 and 22.
- IntegrateCo Part 4 Q9 left out: its formula is missing from the document.

### Run 2

Start: 23.10.2026 21:43:13 (from `runs/run2.txt`; `py` needed approval, so Python could not take the timestamp)

- [ ] 1 validation script
- [ ] 2 SQL checks
- [ ] 3 Excel checks
- [ ] 4 interpretation checks
- [ ] 5 fix or exclude
- [ ] 6 compose exams
- [ ] 7 report, commit and log

Stopped before step 1. Run 1 has not finished: `bank/questions.json` and `bank/inventory.json` do not exist, and there is no `bank/`, `docs/`, `materials/` or git repository yet. The prompt says to stop in that case. The same trust problem as Run 1 also applies here (`runs/run2.txt` shows the 19 allow entries were ignored), so `py` and `git` would need approval anyway.

Fix: accept the trust dialog as described under Run 1, rerun `run_all.ps1 -Only 1`, then `run_all.ps1 -Only 2`.

#### Run 2, attempt 2

Start: 23.10.2026 22:09:54 (Python `datetime`, Europe/Copenhagen). Run 1 is finished (`bank/questions.json` and `bank/inventory.json` exist). No items were ticked, so the run starts at item 1.

- [x] 1 validation script
- [x] 2 SQL checks
- [x] 3 Excel checks
- [x] 4 interpretation checks
- [x] 5 fix or exclude
- [x] 6 compose exams
- [x] 7 report, commit and log

End: 23.10.2026 22:24:25. Duration: 15 minutes.

Done:
- `tests/validate.py` (re-runnable): structural checks, SQL drafts run read-only with a 30 s timeout, Excel answers computed independently with pandas, interpretation models refitted. Expected results in `bank/expected/` (179 files). Final `py tests\validate.py` exit code: 0.
- Results, 228 items: Excel 82 (77 validated, 4 manual_check, 1 disputed, 0 excluded), SQL 97 (96 validated, 1 disputed), interpretation 49 (49 validated). Nothing excluded. All 8 models match `bank/models.json` to 4 decimals.
- Disputed: Q015 (NYC: Brooklyn exceeds Manhattan in 2017 and in 2018, reference says 2017) and Q108 (PWC Q22: 49 is invoice and album pairs; distinct albums are 41). Evidence in `VALIDATION_REPORT.md`. [[KNUT: decide whether to raise Q015 and Q108 with the lecturer]]
- Fixes to generated drafts: Q072, Q073 (prompt now says the files are pipe-delimited), Q124 (tie at fifth place, title tie-break added). Made in both `scripts/build_bank.py` and `bank/questions.json`.
- Exams (`scripts/build_exams.py`, seed 2026): 304 data manipulation exams (E001 to E304) over 31 file pairs, up to 10 per pair (`ic_payroll2015_csv + pcards` gives only 4, `etl_case3 + pcards` none, because of the 8 minute limit); 30 data interpretation exams (R001 to R030), each with one predict, coefficient, significance and dummy item from four different models. Optional questions are left out of exams.

Failed or open:
- Nothing failed.
- P-card cardholder names occur in two letter cases for 12 people in 2014; drafts group them as stored, as the case text defines Name. Listed under observations in the report.
- Ties at a LIMIT cut-off are only checked by hand, not by the script.

### Run 3

Start: 23.10.2026 21:43:38 (from `runs/run3.txt`; `py` needed approval, so Python could not take the timestamp)

- [ ] 1 build script and public data
- [ ] 2 dataset downloads
- [ ] 3 site
- [ ] 4 improvement slot
- [ ] 5 smoke test
- [ ] 6 README
- [ ] 7 commit, push and log

Stopped before step 1. Run 2 has not finished: `bank/exams.json` and `VALIDATION_REPORT.md` do not exist (there is no `bank/` at all), and the prompt says to stop in that case. Nothing was built, committed or pushed. The trust problem from Run 1 also applies (`runs/run3.txt` shows the 19 allow entries were ignored).

Fix: accept the trust dialog as described under Run 1, then rerun `run_all.ps1 -Only 1`, `-Only 2` and `-Only 3` in order.

#### Run 3, attempt 2

Start: 23.10.2026 22:25:12 (Python `datetime`, Europe/Copenhagen). Run 2 is finished (`bank/exams.json` and `VALIDATION_REPORT.md` exist). No items were ticked, so the run starts at item 1.

- [x] 1 build script and public data
- [x] 2 dataset downloads
- [x] 3 site
- [x] 4 improvement slot
- [ ] 5 smoke test
- [ ] 6 README
- [ ] 7 commit, push and log

Attempt 2 was cut off after item 4 (committed as `db6b8ee`). `tests/smoke.py` and `README.md` were written but not committed or ticked.

#### Run 3, attempt 3

Start: 24.10.2026 00:01:08 (Python `datetime`, Europe/Copenhagen). Items 1 to 4 checked quickly (public JSON, `docs/files/`, site files and the improvement slot in `app.js` and `improvement.js` exist); continued from item 5.

- [x] 1 build script and public data
- [x] 2 dataset downloads
- [x] 3 site
- [x] 4 improvement slot
- [x] 5 smoke test
- [x] 6 README
- [ ] 7 commit, push and log (committed locally, not pushed, see below)

End: 24.10.2026 00:03:30. Duration: 2 minutes (attempt 2 ran from 23.10.2026 22:25:12).

Done:
- `py tests\smoke.py`: passed (177 questions, 49 interpretation items, 334 exams, 18 datasets, 227 files scanned for keys). `py tests\validate.py`: 228 checked, 222 validated, 4 manual_check, 2 disputed, 0 excluded, 0 failed.
- `README.md` checked against the prompt: all sections and both `[[KNUT]]` placeholders are there.
- `git ls-files` has nothing under `materials/` or `release-assets/`, and no solution file. `watchdog.ps1` committed with the rest.
- Local commit "Run 3: site and downloads".

File sizes, `docs/files/` (all under 50 MB, in git):

| File | Bytes |
|---|---:|
| Analytics_mindset_case_studies_ETL_Case1.csv | 1,779 |
| Analytics_mindset_case_studies_ETL_Case2_Excel.xlsx | 48,502 |
| Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx | 48,326 |
| Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx | 114,035 |
| Analytics_mindset_case_studies_IntegrateCo_2015payroll.csv | 378,963 |
| Analytics_mindset_case_studies_IntegrateCo_2015payroll.xlsx | 399,922 |
| Analytics_mindset_case_studies_IntegrateCo_2016payroll.csv | 49,152 |
| Analytics_mindset_case_studies_IntegrateCo_2016payroll.xlsx | 62,745 |
| Analytics_mindset_case_studies_IntegrateCo_jobcodes.csv | 283 |
| Analytics_mindset_case_studies_IntegrateCo_locations.csv | 1,706 |
| Chinook_Sqlite.sqlite | 1,067,008 |
| data.xlsm | 540,404 |
| fiftyville.db | 270,336 |
| NYC_Film_Permits.txt | 11,120,891 |
| NYC_Film_Permits.xlsx | 3,506,591 |
| songs.db | 24,576 |

Release assets (`release-assets/`, not in git): `movies.zip` 39,419,579 bytes (from `movies.db`, 68,939,776 bytes), `pcards.zip` 22,048,698 bytes (from `pcards.db`, 94,003,200 bytes).

Not done: push. The push was deliberately not attempted. Commit `d8c0bfd` still contains `bank/inventory.json`, which holds the full case texts and the text of the two solution files. Pushing `main` would publish it with the history, which breaks hard rule 3, and the decision asked for under Run 1 ("Git warning" in `MATERIALS_NOTES.md`) has not been made. Rewriting history to remove it is not allowed for a run (rule 9). Also, `bank/questions.json` is tracked and holds 40 reference answers taken from the materials (`solution_source: "materials"`); they are not in `docs/`, but they would be public in the repository.

What Knut still has to do:
- [[KNUT: decide how to remove `bank/inventory.json` from commit `d8c0bfd` (for example squash all local commits into one) and whether `bank/questions.json` with the materials' reference answers may be public; then run `git push -u origin main`]]
- Enable GitHub Pages: Settings, Pages, branch `main`, folder `/docs`.
- Upload `release-assets/movies.zip` and `release-assets/pcards.zip` to a release tagged `datasets-v1` (see `README.md`).
- Fill the `[[KNUT]]` markers in `README.md`, `MATERIALS_NOTES.md`, `LOG.md` and the home page (`docs/js/app.js`).
- Decide on the disputed questions Q015 and Q108.
- Enter active time and cost figures below.

## Cost statement

[[KNUT: cost figures]]
