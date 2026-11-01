# LOG

## Active time (Knut)

About 6 hours, estimated from the commit history. Commits are grouped into work sessions (a gap of more than 2 hours starts a new session), and each session gets 1 hour for reading and testing before its first commit.

| Session | Commits (first to last) | Span | Estimate |
|---|---|---:|---:|
| 1 | 24.10.2026 08:28 (one commit; Runs 1 to 3 were squashed into it) | 0 min | 1 h |
| 2 | 27.10.2026 14:44 to 15:43 (Runs 4 to 6, answer check) | 59 min | 2 h |
| 3 | 29.10.2026 12:19 to 12:28 (Run 7) | 9 min | 1 h 10 min |
| 4 | 01.11.2026 16:29 to 17:02 (Run 7 finish, Q015 and Q108, own text) | 33 min | 1.6 h |

This is below the 8 to 10 hours it felt like. The commit history misses work that left no commit: the evening of 23.10.2026 when Runs 1 to 3 ran (21:42 to 00:03 in this log, with permissions approved by hand) was squashed into one commit, and writing the run prompts, reading the materials and testing by hand happened outside the commits.

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

### Run 4

Start: 27.10.2026 14:36:54 (Python `datetime`, Europe/Copenhagen).

- [x] 1 read the current site
- [x] 2 fonts and tokens
- [x] 3 shell: header, footer, home
- [x] 4 exam view and timer
- [x] 5 question bank and exam lists
- [x] 6 interpretation view
- [x] 7 screenshots and self-critique
- [x] 8 tests, commit, push and log

End: 27.10.2026 14:51:57. Duration: 15 minutes.

Done:
- Tokens, light and dark theme, as in the brief. Contrast checked: muted is 5.77 on paper and 6.22 on sheet (light), 7.63 and 6.90 (dark); pen on sheet is 8.34 (light) and 7.29 (dark).
- Fonts: Atkinson Hyperlegible Next and Atkinson Hyperlegible Mono both exist on Google Fonts (CSS fetched with Python, 200). No substitution.
- New header, home (two blocks with a random sample question and "Start a random exam"), sticky timer bar, sheet tabs, sheet panel, banded exam lists and bank list with "Previous / Page 1 of 8 / Next", interpretation view in statistical output style, footer on one line.
- `scripts/screenshots.py`: 64 PNGs in `runs/screens/` (8 routes, 2 widths, 2 colour schemes). Time-up is reached by shifting `Date.now` from the script, with no change to the site.
- `py tests\smoke.py` passed; `py testsalidate.py`: 228 checked, 222 validated, 4 manual_check, 2 disputed, 0 failed. No em dashes in `docs/`.

Readings taken where the brief was open (the quieter option each time):
- No shadow at all, not even on the stuck timer bar; detecting "stuck" would need extra JavaScript. The bar has a 3px rule top border that turns red-pencil at time-up.
- The timer bar sits directly above the sheet tabs, not on the heading line, so it can stick within `main` and stays next to the question.
- On exam pages the h1 is 21px, the same size as the prompt, so the prompt is not outranked by the heading.
- Numbers stay in en-GB format (39.4 MB), as in Run 3.
- Interpretation sheet shows the model first, then the question, as the brief orders it.

Self-critique (first round of screenshots):
- Generic template look: no. Two bordered blocks on home only, no shadows, gradients, pills or slogan.
- Prompt and timer clearest on the exam page: yes at both widths. The timer bar takes about 100px at 375px because the buttons wrap; acceptable.
- Horizontal page scroll at 375px: none (checked by script). Model tables scroll inside their own box.
- Red: only time-up (digits, top border, "Time is up").
- Mono: timer, formulas, equation, sheet, table, column and variable names. The first version also set the model id (M1) in mono; fixed.
- All-caps, eyebrows, middle dots, arrows, em dashes: none.
- Dark mode: reads as well as light.
- Fixed after the first round: a bug where exam pages printed "[object HTMLHeadingElement]" instead of the heading (found because the screenshot script timed out), extra gaps in the home blocks, download size wrapping inside the label on mobile, 3-line h1 on mobile (now 26.5px under 600px), wide sheet padding on mobile, sticky bar caught mid-page in full-page shots (script now scrolls to top).
- Removed one thing: the hover colour change on header links; the underline on the current section is enough.

Failed: nothing.

### Run 5

Start: 27.10.2026 15:00:29 (Python `datetime`, Europe/Copenhagen).

- [x] 1 type
- [x] 2 timer bar
- [x] 3 question sheet
- [x] 4 home
- [x] 5 cache busting
- [x] 6 screenshots, before and after, critique
- [x] 7 tests, commit, push, log

End: 27.10.2026 15:08:18. Duration: 8 minutes.

Done:
- Type: IBM Plex Sans (interface), Plex Serif (prompts and h1), Plex Mono (timer, formulas, equation, sheet, table, column and variable names). All three exist on Google Fonts (CSS fetched with Python). No substitution.
- Timer bar: solid ink bar (`#0E141E` with a rule border in dark mode), 64px / 44px mono digits, a 4px progress rule updated by the existing tick, paper-coloured buttons, `stuck` class from an `IntersectionObserver` on a 1px sentinel (disconnected on route change). The only shadow on the site is on the stuck bar.
- Question sheet: rose double margin rule at 40px (16px on mobile), faint ruling behind the prompt with a hard-stop `repeating-linear-gradient` (lines in `--band`, aligned to the 1.6 line-height; it stays aligned at both widths, so it was kept), prompt in Plex Serif 26px / 21px, meta in Sans 15px. Tabs: active tab has a 3px pen top edge; a "5 questions" count shows before the strip under 600px.
- Home: real random manipulation exam as the hero (first question on the ledger sheet, time in 64px mono, question and file counts, "Start exam Exxx", "Show another exam" re-picks in place). The two sections below are plain columns under one rule. No interpretation sample.
- Cache busting: `scripts/build_site.py` stamps `?v=<version>` on `css/style.css` and `js/app.js` in `docs/index.html`; `tests/smoke.py` checks it matches `config.json`.
- `py tests\smoke.py` passed; `py testsalidate.py`: 228 checked, 222 validated, 4 manual_check, 2 disputed, 0 failed. No em dashes in `docs/`.

Choices logged:
- In dark mode the progress fill and the bar's focus outline use the bar text colour (`#E6EAF0`), not `--paper`, because dark `--paper` (`#141A24`) would disappear on the dark bar. In light mode they are the same colour as `--paper`.
- Contrast on the bar: text 13.23 (light) and 15.29 (dark); "remaining" at 75 % opacity 8.12 and 8.88; time-up `#FF8A80` 6.25 and 8.09; disabled buttons at 55 % opacity about 5.1 and 5.3. All pass AA.
- The mono digits get letter-spacing -0.06em so the colon does not look spaced out (Plex Mono gives the colon a full cell).
- Under 600px the stuck bar is about 140px high, because the buttons wrap below the digits.
- The stuck-bar screenshot uses a 560px-high viewport, because the exam page is too short at 800px to scroll the bar to the top.
- A regex escaping slip while editing `build_site.py` briefly wrote a control character into `index.html`; found on the first build, repaired, and the script was run twice to confirm it is idempotent.

Critique, comparing `runs/screens-run4/` with `runs/screens/`:
- Noticeable within two seconds: yes. The exam page now has a dark clock bar with 64px digits where Run 4 had a white strip with 33px digits, the prompt is in a serif on a ruled sheet with a margin, and home opens with a real exam and a big clock instead of two cards.
- Clock first, question second: yes at both widths and in both themes.
- Ledger margin: it reads as ruling, not an error line. At 1px the rose is soft, close to grey; it was not muted further.
- No horizontal scroll at 375px (checked by the script). AA on the bar in both themes (figures above). Focus outlines on the bar use the bar text colour.
- No all-caps, eyebrows, middle dots, arrows, em dashes, pills or emoji. The only gradient is the ruled-line pattern, which has hard stops and no colour blend.
- Removed one thing: the "5 questions, 8 minutes." part of the exam intro. The clock shows the time and the tabs show the questions, so the line now only says to open the files before starting the clock.

Failed: nothing.

### Run 6

Start: 27.10.2026 15:15:13 (Python `datetime`, Europe/Copenhagen).

- [x] 1 workbook frame and tokens
- [x] 2 formula bar and name box
- [x] 3 grid content and selection style
- [x] 4 sheet tabs and status bar
- [x] 5 view by view
- [x] 6 mobile
- [x] 7 screenshots, critique
- [x] 8 tests, commit, push, log

End: 27.10.2026 15:27:04. Duration: 12 minutes. Steps 1 to 6 were built in one pass and committed together with the screenshots, not after each step.

Done:
- Every page is a workbook frame: name box, italic `fx`, formula bar (the prompt in Plex Serif 24px / 19px, or a one-line page description), sheet body with aria-hidden column letters and row numbers, sheet tabs and a status bar. Run 5 ledger margin and ruled lines removed.
- Content is laid out in cells: label and value rows with CSS grid (`cells()`), real data in `<table>` drawn as sheet cells (`xl()`). Row numbers are generated per content row and continue across blocks on a page (the bank numbers its rows by position in the filtered list, starting at 3 under the header and filter rows).
- Selection style: 2px `--select` outline with a 6x6px fill handle on focused links, buttons and summaries, on the active nav link and on the current sheet tab; table rows show the same outline when something inside them has focus.
- Exam pages: the clock is a frozen row under the formula bar (sticky top, shadow only when stuck); tabs, Previous, Next and the status bar stick to the bottom. Interpretation tabs are "Question 1" to "Question 4".
- Home: name box "Start", the first question of a random manipulation exam in the formula bar, the exam laid out as a table (question, subject, case, estimated time), a final row with "Start exam Exxx", "Show another exam" and 8:00 in large mono, then rows for both exam types with real counts and links.
- Home note replaced with Knut's text: "In the oral exam you get one full data manipulation exam and one full data interpretation exam. Practise both here, with the same files and time limits." It is styled as a cell comment.
- Question bank: a spreadsheet table (Id, Prompt, Subject, Case, Skills, Source file) with an autofilter row under the header, green-bar banding and paging in the status bar.
- Interpretation: regression summary sheet with "Regression statistics" (model, R squared, adjusted R squared, observations), "Variables" and "Coefficients" (Parameter, Term, Coefficient, Standard error, p-value), numbers right-aligned, no highlighting. The equation is the formula bar's second line.
- `scripts/screenshots.py`: added the bank with a filter applied and keyboard focus on a sheet tab. Full-page shots now set the viewport to the page height, so the sticky bars sit where they belong.
- `py scriptsuild_site.py` rerun so the `?v=` stamp changes with this run (it is the data version, which only changes when the site is rebuilt).
- `py tests\smoke.py` passed; `py testsalidate.py`: 228 checked, 222 validated, 4 manual_check, 2 disputed, 0 failed. No em dashes in `docs/`. The smoke test did not need changes.

Choices logged:
- The bank gets a sixth column, "Source file". The source file filter already existed and had no column to sit in; dropping it would have removed a working filter.
- Interpretation tabs now use the same markup as manipulation tabs (buttons with `aria-current`, Tab key moves between them) instead of `role="tab"` with arrow keys. The question now lives partly in the formula bar and partly in the sheet, so there is no single tab panel to point to. They also get Previous and Next, as in the tab row of the brief.
- Fill handles are drawn on links, buttons and summaries only. Inputs and selects cannot have pseudo-elements, so they show the 2px selection border without the handle.
- The bank header row is not frozen: sticky table rows need fixed row heights and break inside the sideways-scrolling container on mobile. A page has at most 25 rows.
- The comment marker on the home note uses `--red-pencil`, as the brief asks. It is the only use of red outside time-up and errors.
- "Dataset reference" and "Report an issue" span both cells of their row instead of repeating their own name as a label.
- On mobile the bank table and the model tables scroll sideways inside their containers; the home exam table fits at 375px.

Critique, comparing `runs/screens-run5/` with `runs/screens/`:
- Reads as a worksheet within one second: yes on every page at 1280. Name box, `fx`, column letters, row numbers, gridlines, tabs and status bar are all there. At 375px the letters and row numbers are hidden as asked; the formula bar, cells, tabs and status bar still carry the idea.
- Calm or noisy: calm at 1280. The head cells are pale and small. Chrome that carried nothing was removed: the duplicate site footer (see below) and, under 700px, Previous and Next on exam pages, because the tabs do the same job and the sticky footer had grown to about 130px.
- Prompt first, clock second: the prompt sits first, at the top in 24px serif, and is the first thing read. The dark clock with 64px digits is still the heavier shape on the page; I kept it at the size the brief asks for. Knut's decision (01.11.2026): keep the current clock size.
- Row numbers: aligned with their rows in both themes after one fix. They were top-left in tables and are now centred to the first text line. Hidden under 700px.
- Commercial look-alikes: none. No green chrome, no ribbon, no icons, no product names. Gridlines are the Run 5 grey-green, and the selection colour is the site's pen blue.
- Contrast: head text on head cells 5.35 (light) and 6.52 (dark); pen on head cells 7.18 and 7.57; clock figures as in Run 5. The selection is visible in both themes (light screenshots and the dark time-up shot).
- No horizontal page scroll at 375px (script). No all-caps, eyebrows, middle dots, arrows, em dashes, pills or emoji. No gradients at all now that the ruled lines are gone.
- Fixed during review: row numbers not centred in tables; letter-by-letter wrapping in mobile tables (`overflow-wrap: anywhere` with automatic table layout); the home exam table and its Start row clipped at 375px; the sticky footer caught mid-page in full-page screenshots.
- Removed one thing: the site footer. Its data version is now in every status bar, and its sentence repeated the home page.

Failed: nothing.

### Improvement (interactive session with Claude, 27.10.2026, ended 27.10.2026 15:29)

- Built the answer check with trap answers in `docs/js/improvement.js` and `docs/css/improvement.css`, switched on in `config.json`.
- `scripts/build_checks.py` computes each trap from the raw data with the wrong method and keeps it only when it differs from the expected answer. Result: 103 checked questions, 36 with traps, 38 traps (wrong definition 11, wrong grain or key 9, boundary or parsing 9, wrong population 7, average of ratios 2). 240 of 304 manipulation exams contain at least one trap question.
- `tests/check_answers.mjs`: every expected answer grades as correct, every trap as its trap, plus 27 format cases. All passed.
- Q015 and Q108 stay off the site as disputed; they are described in the materials paragraph.
- Run 6 picked up the first version of these files in its commit; this entry covers the rest.

### Run 7 (interactive session with Claude)

Start: 29.10.2026 12:14:50 (Python `datetime`, Europe/Copenhagen). Prompt: `prompts/RUN7_examiner.md`, with Knut's decisions from the section 0 report: no AI examiner (2.5), no stored sessions and no Progress page, topics Excel, SQL, Regression interpretation and Mixed (no Power BI, it is not in the materials), no in-browser workspace, no claim about the real exam format, both KNUT marker formats, CLAUDE.md rules 5, 7 and 8 updated, exam mode built on the answer check as the single improvement.

- [x] 0 read earlier runs, report (Run 6 was carried out: commit 9159337)
- [x] 1 redesign
- [x] 2 trap tags and probe bank
- [x] 3 exam mode
- [x] 4 debrief (built in step 3; looks and self-assessment left for Knut's manual test)
- [x] 5 evidence table
- [x] 6 390px (by reading the CSS) and secret scan; Chrome tests handed to Knut
- [x] 7 docs, commit, push, log

Paused 29.10.2026 12:28:06 (usage limit). State for resuming:
- Done and committed: redesign (white, system fonts, nav Practice, Exam mode, About; dark theme and workbook chrome removed), trap tags in `checks.json` (from `scripts/build_checks.py`; output unchanged apart from the tags), `docs/data/probes.json`, smoke test checks for probes, exam mode in `docs/js/examiner.js`.
- Fixed on the way: module imports now carry `?v=` (stamped by `build_site.py`) and data JSON is fetched with `cache: "no-cache"`. Without this a browser could combine a new `app.js` with an old `improvement.js` or `config.json`.
- Tested in Chrome, text only, Strict, Q080: a trigger term gives a probe after about 2 s; the trap answer 310,08 gives the grain trap probe; a thin answer gets its pushback exactly 20 s after the previous question.
- Debrief checked through the DOM: it renders time used, probes with reasons and tags, the thin answer, the trap answer (310.08, wrong grain) and the transcript. The Chrome screenshot tool timed out on that page; the page itself did not freeze. Still to check: how it looks, self-assessment, "Practise my weak spots".
- Next: steps 5 to 7: `docs/improvement-evidence.md` (count from data), test Supportive and Standard, an SQL and a Regression task, voice on, 390px, secret scan, README and push.

Resumed 01.11.2026 (reduced scope at Knut's request: no Chrome, no screenshots; start time not recorded). Ended 01.11.2026 16:28:47.
- `docs/improvement-evidence.md`: counts computed from `checks.json`, `probes.json`, `questions.json` and `interpretation.json` with the matching rules from `examiner.js`. 226 questions; 103 with an answer check, 36 with a computed trap (38 traps); 201 with a tied question probe; 35 probes (7 trap, 11 question, 13 trigger, 4 generic). Join and confounding have probes but no computed trap.
- 390px, by reading `style.css` and `improvement.css`: all tables sit in `.table-wrap` (overflow-x auto), the question tabs scroll inside themselves, segmented choices and button rows wrap, the exam layout drops to one column under 900px, the answer input shrinks (`min-width: 0`), `pre` wraps, and `body` has `overflow-wrap: break-word`. The header (ExamStudio plus three links) needs about 310px of the 358px available. Nothing found that would cause horizontal scroll, so no CSS change. Not checked visually.
- Secret scan: `git grep -i` for sk-ant, api_key, apikey, token, secret, password, x-api-key, and a regex over `git log --all -p` for key-shaped strings. Hits are only rule and prompt text (CLAUDE.md, `prompts/RUN7_examiner.md`), design tokens in CSS and LOG, a loop variable in `examiner.js`, a film title in `bank/expected/Q117.json` and words inside two course databases. No key, token or password. The smoke test's key scan (243 files) also passed.
- README: exam mode section, voice browser support, privacy line, KNUT markers; structure table updated for `checks.json`, `probes.json`, `examiner.js` and the evidence file.
- Tests: `py tests/smoke.py` passed; `node tests/check_answers.mjs` all passed (103 checks).
- Not done in this run: the Chrome and Edge tests (voice, Supportive and Standard, an SQL and a Regression task, the debrief's looks, self-assessment, "Practise my weak spots"). Knut tests these by hand.
- Skipped from the prompt by Knut's decision: the AI examiner (2.5), saved sessions and the Progress page.

Failed: nothing.

### Q015 and Q108 fixed (interactive session with Claude, 01.11.2026, ended 01.11.2026 16:52:45)

Knut's decision after reading the disputes.
- Q015 (NYC question 13): prompt now "...and count full calendar years only." Expected 2017, as in `solutions.xlsx`. `validate.py` keeps only years the data covers from the first to the last week (2018 stops in February), so the check gives 2017 alone.
- Q108 (PWC question 22): expected answer 41, `solution_source: "generated"`, with a `solution_note` that `PWC answers.docx` gives 49 because it counts complete-album purchases. 49 is a computed trap (Wrong grain or key, tag grain). New trap probe `T-grain-album`, tied to Q108 by a `questions` field; `examiner.js` now only asks a probe with `questions` on those questions.
- `build_site.py` strips `solution_note` from the public JSON like the other solution fields; the smoke test checks it, and that probe `questions` are on the site.
- Full build: 228 checked, 224 validated, 4 manual_check, 0 disputed, 0 failed. 179 questions on the site (82 Excel, 97 SQL), 49 interpretation items. Answer check 105 questions, 37 with traps, 39 traps. 303 manipulation exams (was 304: the shifted random stream gives payroll 2015 + P-card 3 exams instead of 4; that pair rarely fits in 8 minutes), 246 with a trap question; 30 interpretation exams. Smoke test passed; `check_answers.mjs` all passed (105 checks).
- README counts and `docs/improvement-evidence.md` updated. The README paragraph on the materials was later replaced with Knut's own text.

Failed: nothing.

### Own text and markers (interactive session with Claude, 01.11.2026, ended 01.11.2026 17:02:53)

- Knut's own text inserted verbatim: the improvement paragraph in the README exam mode section and on the About page ("Why I built it"); the materials paragraph in the README and in `MATERIALS_NOTES.md`. The empty KNUT marker in the About page's exam mode section was removed.
- LOG.md: active time estimated from the commit history, cost statement, clock size decision.

Failed: nothing.

## Cost statement

Claude Pro subscription only. No API cost: the site uses no AI, and no API key was used in any run.
