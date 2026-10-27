# Run 6: the site as a spreadsheet

Read `CLAUDE.md` first and follow it, rule 7 above all. The owner sees the Run 5 changes but still finds the site boring. He chose a clear direction: the interface itself should look and behave like a workbook, because every student on this course spends the exam in a spreadsheet. This run is a real redesign of the layout, not a tweak of tokens.

Same scope and limits as `prompts/RUN4_design.md`: only `docs/index.html`, `docs/css/`, `docs/fonts/` and the render code in `docs/js/app.js`. No new features, no change to data, routes, downloads, timer logic, the cache busting in `build_site.py`, or `improvement.js`. Keep `<section id="improvement-slot" hidden>` directly under every prompt and the `runImprovement` call. Do not ask questions; log every choice.

Append a "Run 6" heading to `LOG.md` with the start time and this checklist:
- [ ] 1 workbook frame and tokens
- [ ] 2 formula bar and name box
- [ ] 3 grid content and selection style
- [ ] 4 sheet tabs and status bar
- [ ] 5 view by view
- [ ] 6 mobile
- [ ] 7 screenshots, critique
- [ ] 8 tests, commit, push, log

## The idea

Every page is a worksheet. The name box shows where you are, the formula bar shows the question, the content sits in a gridded sheet with column letters and row numbers, the questions of an exam are sheet tabs along the bottom, and a status bar at the very bottom carries real counts. A student should recognise it in one second, and it should still be calm and readable.

It must be a generic spreadsheet, not a copy of Microsoft Excel or Google Sheets: no Excel green, no ribbon, no product icons or names, no logos. Keep the Run 5 palette (paper, sheet, ink, pen, rule, band, red pencil) and IBM Plex. Drop the ledger margin and the ruled lines from Run 5; the grid replaces them.

## 1. Workbook frame and tokens

Add tokens: `--grid: #D5DBD1` (cell lines), `--head-cell: #ECEFE8` (column and row header cells), `--head-text: #586174`, `--select: var(--pen)`. Dark mode: grid `#2C3747`, head-cell `#18202B`, head-text `#9AA4B4`.

Page structure on desktop, top to bottom, all inside one framed workbook area that fills the width of `.wrap` (max 1200px):

```
ExamStudio practice                    Manipulation exams  Question bank  Interpretation exams
+-----------------------------------------------------------------------------------------+
| [ Q028      ] | fx | In the ETL Case 1 data, Total Depreciation shows negative...       |  <- name box + formula bar
+----+--------+--------------+--------------+--------------+--------------+---------------+
|    |   A    |      B       |      C       |      D       |      E       |      F        |  <- column letters
+----+--------+--------------+--------------+--------------+--------------+---------------+
|  1 | content laid out in cells ...                                                      |
|  2 |                                                                                    |
|  3 |                                                                                    |
+----+------------------------------------------------------------------------------------+
| [ 1 Excel ][ 2 Excel ][ 3 Excel ][ 4 SQL ][ 5 SQL ]                    Previous  Next   |  <- sheet tabs
+-----------------------------------------------------------------------------------------+
| Exam E012, question 1 of 5                                  Data version 27.10.2026-... |  <- status bar
+-----------------------------------------------------------------------------------------+
```

- The column letter strip and row number column are decorative chrome: `aria-hidden="true"`, `user-select: none`, Plex Sans 13px in `--head-text` on `--head-cell`, with `--grid` lines. Row numbers follow the actual content rows (generate them per row of content, not a fixed count), so they line up with what they label. Column letters span the real columns of whatever grid the view uses.
- Real content stays real HTML (headings, paragraphs, tables, buttons, lists) and real tables stay `<table>`. The grid look comes from borders and layout, never from content drawn in CSS.

## 2. Name box and formula bar

- On every question view (exam, bank question, interpretation): the name box (a small framed box, Plex Mono 15px) shows the question id; the `fx` label is muted italic Plex Serif; the formula bar holds the prompt in Plex Serif 24px (19px on mobile), wrapping to as many lines as needed, max 70ch, on `--sheet`. This is now the prompt's home: the h2 "Question Q028" goes away visually (keep a visually hidden heading for screen readers). The improvement slot sits directly below the formula bar, inside the frame.
- On list pages and home, the name box shows the page ("Exams", "Bank", "Start") and the formula bar a one-line plain description of the page.

## 3. Grid content and the selection style

- Lay each view's content into cells: label cells in Plex Sans 600 on the left, value cells beside them, with `--grid` borders. Use CSS grid. Never fake data to fill cells; empty cells are fine and look right in a sheet.
- Selection: the focus style for every interactive element becomes a spreadsheet selection, a 2px `--select` border around the element with a 6x6px square "fill handle" at the bottom-right corner (a pseudo-element). The current question tab, the active nav link and the row under keyboard focus in tables use the same language. This replaces the old outline; it must stay clearly visible in both themes.
- Numbers right-aligned, text left-aligned, as in a sheet. Tabular numerals.

## 4. Sheet tabs and status bar

- Exam questions become sheet tabs at the bottom of the frame, rectangular, the active one on `--sheet` with bold text and a 2px `--select` bottom edge, joined to the sheet above; inactive on `--head-cell`. Previous and Next sit at the right end of the tab row. On interpretation exams the tabs are "Question 1" to "Question 4".
- The tab row plus status bar stick to the bottom of the viewport on exam pages (`position: sticky; bottom: 0`), so tabs are always reachable, like a real workbook.
- Status bar: one line under the tabs in Plex Sans 13px `--head-text` on `--head-cell`. Left: where you are ("Exam E012, question 1 of 5", "Question bank, 177 questions, 23 shown", "Exam R004, question 2 of 4"). Right: the data version. Only real values; no fake "Ready", no fake sums.

## 5. The clock

Keep the Run 5 dark clock and its logic, but integrate it as a frozen row at the top of the sheet area on exam pages (sticky at the top, below the formula bar row, like frozen panes). Keep 64px / 44px digits, the progress rule and the time-up state. Keep the shadow only when stuck.

## 6. View by view

- Home: name box "Start", formula bar shows the first question of a randomly picked manipulation exam. Below, a grid laying out that exam: one row per question with columns A "Question" (id), B "Subject", C "Case", D "Time" (estimated minutes, right-aligned), and a final row with the total time 8:00 in large Plex Mono in column D and the "Start exam E249" button in column A to C. Then two more rows: "Data manipulation" and "Data interpretation", each with a one-line description and links (Start a random exam, Browse N exams, Question bank (N)). "Show another exam" re-picks without reloading. Keep the KNUT note, styled as a cell comment: a small cell with a dashed border and a red-pencil corner triangle (the comment marker), text visible.
- Exam view: formula bar = prompt; frozen clock row; then cells: "Files" (download buttons in the value cells), "Answer format", "Dataset reference" (the disclosure; inside it, headers and columns laid out as a real mini-grid: one header per cell in Plex Mono, required ones in bold, exactly the data that is shown today), "Report an issue". Tabs and status bar at the bottom.
- Question bank: the list becomes a true spreadsheet table: frozen header row with column letters above and real column names (Id, Prompt, Subject, Case, Skills) in row 1, row numbers on the left, gridlines, green-bar `--band` on alternate rows. Filters become an autofilter row directly under the header (selects and the search input sitting in the header cells, with visible labels for screen readers via `aria-label` and a visible small label). Pagination in the status bar row's left side is fine. A single bank question opens like an exam view without tabs.
- Exam lists: same spreadsheet table style.
- Interpretation exam: render the model as a regression summary sheet, the layout students know from the spreadsheet regression tool: a block titled "Regression statistics" (rows: R squared, Adjusted R squared, Observations, with the values we have; do not add statistics we do not have), then the variables block, then the coefficient table (Parameter, Term, Coefficient, Standard error, p-value), all in cells with gridlines, numbers right-aligned in tabular Plex Sans. The equation goes in the formula bar's second line under the prompt, in Plex Mono. "Show answer" stays a disclosure, in a cell below. No highlighting of significant p-values.

## 7. Mobile (under 700px)

Hide the column letter strip and row numbers. Name box and formula bar stack (name box above). Cells become label-above-value. Tabs and status bar still stick to the bottom; the tab strip scrolls sideways inside itself; the status bar may drop the data version. No horizontal page scroll at 375px; the bank table scrolls inside its own container.

## 8. Screenshots and critique

Copy `runs/screens/` to `runs/screens-run5/` first. Then shoot all routes from Run 4 and Run 5 at 1280 and 375, light and dark, plus the bank with a filter applied and keyboard focus on a tab (to show the selection style). Write in `LOG.md`:
- Does every page read as a worksheet within one second? Does it still read calmly, or has the chrome become noise? Remove chrome that carries no information.
- Is the prompt in the formula bar the clearest text on the exam page, with the clock second?
- Row numbers aligned with their rows at both themes and widths?
- Anything that looks like a specific commercial product (Excel green, ribbon, icons)? Remove.
- AA contrast on head cells, status bar and the dark clock; selection style visible everywhere.
- No horizontal scroll at 375px; no all-caps labels, eyebrows, middle dots, arrows, em dashes, pills, emoji, gradients used as colour.
Then remove one thing that is not needed.

Run `py tests\smoke.py` and `py tests\validate.py` (both must pass; extend the smoke test only if a check needs updating for the new markup, never to weaken it), check `docs/` for em dashes, stage, confirm nothing under `materials/`, `release-assets/` or `runs/` is included, commit "Run 6: spreadsheet interface", `git push origin main`. Finish `LOG.md` with end time, duration and the critique.
