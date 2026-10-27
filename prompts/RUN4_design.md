# Run 4: visual redesign of the site

Read `CLAUDE.md` first and follow it, rule 7 above all. This run changes how the site looks and reads, not what it does. Work through the steps in order and do not ask questions; where something is unclear, take the reading that keeps the site quieter and log it.

## 0. Start

Append a "Run 4" heading to `LOG.md` with the start time and this checklist:
- [ ] 1 read the current site
- [ ] 2 fonts and tokens
- [ ] 3 shell: header, footer, home
- [ ] 4 exam view and timer
- [ ] 5 question bank and exam lists
- [ ] 6 interpretation view
- [ ] 7 screenshots and self-critique
- [ ] 8 tests, commit, push and log

## Scope

You may change: `docs/index.html`, `docs/css/style.css`, and the render code in `docs/js/app.js` (markup, class names, element order, copy). You may add files under `docs/css/` and `docs/fonts/`.

Do not change: anything in `bank/`, `scripts/`, `tests/`, `docs/data/`, `docs/files/`; the hash routes; what each view shows; the download behaviour; the timer logic (only its markup and look); the "Report an issue" link; `js/improvement.js`. Every question view must still render `<section id="improvement-slot" hidden>` directly under the prompt, and `runImprovement` must still be called after each render. Do not add features. Do not highlight significant p-values or anything else that hints at an answer.

## The brief

Who uses it: accounting students at SDU preparing for an oral exam where they get one full data manipulation exam (Excel and SQL, 8 minutes) and one data interpretation exam (regression output, 5 minutes). They use it on a laptop with Excel or a SQLite tool open beside the browser, often under time pressure.

The page's job: get a student into a timed exam in one click, make the question and the clock impossible to lose, and make files and dataset details easy to find. It should feel like a calm, well-made working tool from the accounting world, not a startup landing page and not a generic AI page.

Where the look comes from: accounting working papers and spreadsheets. Ledger and green-bar printout paper (pale green bands that guide the eye across long rows), the auditor's red pencil (used only for problems), blue-black pen ink, and workbook sheet tabs. Use these as structure, not decoration: banding only where rows are long, red only for time-up and errors, tabs only where there really are several sheets (questions in an exam).

## Design plan (tokens)

Colour, define as CSS custom properties on `:root`:
- `--paper: #F5F7F3` page background, cool off-white with a trace of green
- `--sheet: #FFFFFF` surfaces that hold a question or a table
- `--ink: #1F2A44` body text and headings, blue-black pen ink (not grey-black)
- `--muted: #586174` secondary text; check it passes WCAG AA on both `--paper` and `--sheet`
- `--rule: #C8D2C3` hairlines and borders, grey-green like ledger ruling
- `--band: #E9F0E4` green-bar banding on alternate rows of long tables
- `--pen: #2A4A96` the one action colour: links, primary buttons, active tab, focus ring
- `--red-pencil: #B42318` only for time-up, errors and disputed items
- `--tick: #2E6A3A` only for "done" states that already exist (none today; define it for later)

Add a dark theme under `@media (prefers-color-scheme: dark)`: paper `#141A24`, sheet `#1B2330`, ink `#E6EAF0`, muted `#A3ACBB`, rule `#344052`, band `#1F2A38`, pen `#8FB0F5`, red-pencil `#F2857A`. Same rules of use.

Type:
- Body and headings: Atkinson Hyperlegible Next (designed by the Braille Institute for reading under strain, which fits students reading prompts against a clock).
- Things a student reads character by character or types: Atkinson Hyperlegible Mono, used only for the timer digits, formulas, SQL, regression equations, and sheet, header, table and column names in the dataset reference. Not for ids, labels or metadata.
- Load both from Google Fonts with `display=swap` and a system fallback. First check that the families exist by fetching the CSS URL with Python; if either is missing, use Atkinson Hyperlegible for text and IBM Plex Mono for the mono role, and log the substitution.
- Scale: base 17px, ratio 1,25 (17 / 21 / 26,5 / 33). Body line-height 1,55, headings 1,2. Headings weight 700, body 400, meta 400 in `--muted`. Line length max about 70 characters for prompts and prose. Use `font-variant-numeric: tabular-nums` wherever numbers line up (tables, sizes, timer).
- Sentence case everywhere. No all-caps labels, no letter-spaced eyebrows above headings, no single word set in a different colour or style inside a heading.

Shape and depth: radius 3px on buttons and inputs, 2px on panels, 0 on table cells. Borders, not shadows; at most one shadow in the whole site, on the sticky timer bar when it is stuck. No gradients anywhere.

Motion: none on load. Only responses to actions: the active tab and the details disclosure may change instantly or within 120 ms. Time-up gets one change of state (red-pencil border and text), not a pulse. Respect `prefers-reduced-motion`.

## Layout, view by view

Header: one line. "ExamStudio practice" on the left in ink, the three section links on the right; the current section has a 2px `--pen` underline, not a filled pill. Under 600px the links wrap below the name. Header sits on `--sheet` with a `--rule` bottom border.

Home: do not open with a slogan. Open with what the site actually is: a real exam. Lay it out as two blocks side by side on desktop, stacked on mobile:

```
Practice for Data Analytics in Accounting
[[KNUT note, styled as a dashed pencil note]]

+-------------------------------+  +-------------------------------+
| Data manipulation             |  | Data interpretation           |
| 5 questions, 8:00             |  | 4 questions, 5:00             |
| Excel and SQL on two files    |  | Regression output from the    |
| from the course cases.        |  | restaurant case.              |
|                               |  |                               |
| One question from the bank:   |  | One question from the bank:   |
| "Count shooting permits in    |  | "Predict ..."                 |
|  Brooklyn with BROADWAY ..."  |  |                               |
|                               |  |                               |
| [Start a random exam]         |  | [Start a random exam]         |
| Browse 304 exams              |  | Browse 30 exams               |
| Question bank (177)           |  |                               |
+-------------------------------+  +-------------------------------+
```
The sample prompt is a real question picked at random from the loaded data each visit, shown in a quote block, so the first thing a student sees is exactly what the exam asks. "5 questions, 8:00" uses the mono digits. "Start a random exam" goes straight to a random exam (reuse `pick`). Counts come from the data, never typed in. Keep the copy plain and short.

Exam view (manipulation), the most important page:
```
All manipulation exams
Exam E012                                     7:42 remaining   [Start] [Pause] [Reset]
5 questions, 8 minutes. Open both files before you start the clock.
[Download ETL case 1 data, csv, 2 KB]  [Download CS50 movies, zip, 39,4 MB]  [Download both]

 ________  ________  ________  ________  ________
| 1 Excel || 2 Excel || 3 Excel || 4 SQL  || 5 SQL  |
+-----------------------------------------------------------------+
| Q028, Excel Part 2, about 2 min                                 |
|                                                                 |
| In the ETL Case 1 data, Total Depreciation shows negative ...   |   prompt at 21px
|                                                                 |
| Answer format: two formats and a number.                        |
| [improvement-slot]                                              |
| > Dataset reference   (sheet and header names in mono)          |
| Report an issue                                   [Previous] [Next] |
+-----------------------------------------------------------------+
```
- The timer becomes a bar that sticks to the top of the viewport once the header scrolls away (`position: sticky`), holding remaining time in large mono digits (about 33px), elapsed time smaller, and the three buttons. Time-up turns the digits and the bar's top border `--red-pencil` and shows "Time is up" as text. Keep the `aria-live` status.
- The five questions become workbook sheet tabs directly above the question sheet: rectangular tabs, the active one in `--sheet` colour joined to the panel below with no border between them, inactive ones in `--paper` with a `--rule` border. Each tab shows the number and subject. Keep them as buttons with `aria-current`, and make the strip keyboard-friendly (arrow keys optional, Tab must work). On narrow screens the strip scrolls sideways inside itself; the page must not.
- Replace the pipe-separated meta line with a short sentence-style line: "Q028, Excel Part 2, about 2 min". No middle dots, no pipes.
- The prompt is the largest text on the page after the timer.
- Download buttons: secondary style (pen-coloured border and text on sheet), label in the form "Download ETL case 1 data", with file type and size after it in muted text. "Download both" stays.

Question bank: filters in one row above the list on desktop, wrapping on mobile, with visible labels. The list becomes a table-like list with green-bar banding: each row shows the id (link), the prompt (the main text), and the case and skills in muted text. Pagination at the bottom as "Previous" / "Page 1 of 8" / "Next". A single bank question opens in the same sheet panel as in an exam, without the tabs.

Exam lists: keep the table, add green-bar banding, keep "Pick an exam for me" as the primary button above it, and show the count from the data.

Interpretation exam: same sticky timer bar and sheet tabs (Question 1 to 4). Inside the sheet: the model heading, then the regression output styled like statistical output, a clean table with right-aligned tabular numbers, a heavier rule under the header row and above the first row, no zebra banding (it is short), the equation in mono on its own line. Variables table above it, same style. "Show answer" stays a disclosure; its content sits on `--band` with a 2px `--pen` left rule.

Footer: one muted line on `--paper` with the data version.

Focus: a 2px `--pen` outline with 2px offset on every interactive element. Hit targets at least 40px high on touch.

## Copy rules

English, British spelling, sentence case, plain verbs. Buttons say what happens: "Start a random exam", "Start", "Pause", "Reset", "Show answer". No arrows appended to links or buttons, no em dashes, no exclamation marks, no "Let's", no marketing adjectives. Keep every `[[KNUT: ...]]` marker visible and unchanged.

## 7. Screenshots and self-critique

Install Playwright for Python (`py -m pip install --user playwright`, then `py -m playwright install chromium`). Write `scripts/screenshots.py` that starts `http.server` on `docs/`, opens these routes at 1280x800 and at 375x812, in light and dark colour scheme, and saves full-page PNGs to `runs/screens/` (gitignored): `#/`, `#/manipulation/exams`, `#/manipulation/exams/E012`, the same exam with the timer started and scrolled down 600px, `#/manipulation/questions`, `#/manipulation/questions/Q045`, `#/interpretation/exams/R004` with "Show answer" opened, and an exam with the timer forced to time-up (set it via a URL parameter only in the screenshot script, or by waiting; do not add a debug feature to the site).

Look at every screenshot. Then write a short critique in `LOG.md` against this list and fix what fails, then shoot again:
- Does any page look like a generic AI or SaaS template (cards everywhere, soft shadows, gradients, pills, centred hero slogan)?
- Is the prompt and the timer the clearest thing on the exam page at both widths?
- Is there horizontal page scroll at 375px?
- Is red used for anything other than time-up, errors or disputes?
- Is mono used for anything other than timer digits, formulas, SQL and literal sheet, table and column names?
- Any all-caps labels, eyebrows, middle dots, arrows or em dashes?
- Does dark mode read as well as light?
Then remove one thing that is not needed.

## 8. Tests, commit, push and log

Run `py tests\smoke.py` and `py tests\validate.py`; both must pass. Check `docs/` for em dashes. `git add -A`, confirm nothing under `materials/`, `release-assets/` or `runs/` is staged, commit with "Run 4: visual redesign", and `git push origin main`. If the push fails, log the exact error and stop. Finish `LOG.md` with end time, duration, any font substitution, and the critique notes.
