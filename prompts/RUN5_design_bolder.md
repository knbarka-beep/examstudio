# Run 5: make the design bolder and more distinctive

Read `CLAUDE.md` first and follow it, rule 7 above all. Run 4 made the site tidy but too quiet: the owner looked at the live site and could not see a difference from before. This run keeps everything that works (tokens, structure, routes, tests, the improvement slot) and gives the site a clear, memorable identity. Same scope and limits as `prompts/RUN4_design.md`: only `docs/index.html`, `docs/css/`, `docs/fonts/` and the render code in `docs/js/app.js`. No new features, no change to data, routes, downloads, timer logic or `improvement.js`. Keep `<section id="improvement-slot" hidden>` under every prompt and the `runImprovement` call. Do not ask questions; log every choice.

Append a "Run 5" heading to `LOG.md` with start time and this checklist:
- [ ] 1 type
- [ ] 2 timer bar
- [ ] 3 question sheet
- [ ] 4 home
- [ ] 5 cache busting
- [ ] 6 screenshots, before and after, critique
- [ ] 7 tests, commit, push, log

## The idea in one sentence

An exam paper on ledger paper, with an exam-hall clock: the question sits on a ruled sheet with a ledger margin, set in a printed-paper serif, and the clock is a dark, heavy bar that you cannot miss.

The one bold element is the clock. The one memorable texture is the ledger sheet. Everything else stays quiet.

## 1. Type: switch to IBM Plex

Atkinson Hyperlegible Next draws every zero with a slash, which reads as "EØ12" and "2Ø18" in ordinary text. Replace it with the IBM Plex superfamily, loaded from Google Fonts with `display=swap`:
- IBM Plex Sans 400, 600: interface, labels, body, tables.
- IBM Plex Serif 400, 600: question prompts and the page h1 only. This is the "printed exam paper" voice.
- IBM Plex Mono 400, 600: timer digits, formulas, SQL, regression equation, and literal sheet, table and column names. Nothing else.
The link to the subject is real: IBM's tabulating machines were built for accounting work. Keep the 17px base and the scale; prompts go up (see 3). Turn on `font-variant-numeric: tabular-nums` in tables and the timer, and `lining-nums` everywhere.

## 2. Timer bar: the exam-hall clock

- The sticky timer bar becomes solid `--ink` (`#1F2A44`) with light text (`#F5F7F3`). In dark mode it stays a distinct, deeper surface (`#0E141E`) with a `--rule` border so it still reads as the clock.
- Remaining time in Plex Mono 600 at 64px on desktop and 44px under 600px, no spaces around the colon. "remaining" after it in Plex Sans 15px at 75 % opacity. Elapsed time smaller, to the right.
- Directly under the digits, across the full width of the bar, a 4px progress rule showing the share of time used, in `--paper` on a slightly lighter ink track. At time-up the digits and rule turn red-pencil (use `#FF8A80` on the dark bar for contrast, check AA) and "Time is up" appears as text. No animation beyond the rule's width updating with the existing tick.
- Buttons inside the bar: Start as a solid paper-coloured button with ink text; Pause and Reset as outlined in paper colour. Disabled states must stay clearly visible on the dark bar.
- The bar may cast the site's only shadow when stuck. Use `IntersectionObserver` on a 1px sentinel above it to toggle a `stuck` class; no scroll listeners.

## 3. Question sheet: ledger paper

- The question panel (`--sheet`) gets a ledger margin: a double vertical rule 40px from the left edge, two 1px lines 3px apart, in a muted rose `#E2B4AE` (dark mode `#5A3A3A`). This colour is decorative ruling only and must not be reused for anything else; `--red-pencil` stays reserved for time-up and errors. Content starts to the right of the margin. Under 600px the margin moves to 16px and the content padding shrinks to match.
- Faint horizontal ruling behind the prompt only: lines in `--band` every 1,6em aligned with the prompt's line-height, made with a `repeating-linear-gradient` with hard stops (this is a ruled-line pattern, not a colour gradient). If it ever hurts legibility or misaligns at any width, drop it and log why.
- Prompt in IBM Plex Serif 400 at 26px desktop / 21px mobile, line-height 1,6, max 62ch.
- Meta line ("Q028, Excel Part 2, about 2 min") above the prompt in Plex Sans 15px `--muted`.
- Sheet tabs stay, but make them read as workbook tabs: the active tab is `--sheet` with a 3px `--pen` top edge, joined seamlessly to the sheet; inactive tabs sit on `--paper` with `--muted` text. On mobile, fade nothing; instead show a small "5 questions" count before the strip so it is clear more tabs exist.

## 4. Home: open with a real exam, not boxes

Replace the two bordered cards. Layout on desktop:

```
Practice for Data Analytics in Accounting                              (Plex Serif, 41px)
[[KNUT note, dashed]]

+--ledger sheet----------------------------------------------+   8:00
| ||  Exam E187, question 1 of 5                             |   5 questions, Excel and SQL
| ||                                                         |   2 data files
| ||  Show invoice IDs and totals above 10, highest first.   |
| ||  (Plex Serif 33px)                                      |   [Start exam E187]
| ||                                                         |   Show another exam
+------------------------------------------------------------+

Data manipulation                         Data interpretation
Five questions in 8 minutes, Excel and    Four questions in 5 minutes on regression
SQL on two files from the course cases.   output from the restaurant case.
Start a random exam                       Start a random exam
Browse 304 exams    Question bank (177)   Browse 30 exams
```
- The hero is a real manipulation exam picked at random: its first question shown on the same ledger sheet as the exam page, with the exam's id, its time in big Plex Mono, and its file count beside it. "Start exam E187" opens that exact exam. "Show another exam" re-picks without reloading.
- Below, the two sections are plain columns separated by whitespace and one `--rule`, not boxes. Counts come from the data.
- Do not show an interpretation sample on the home page.
- Under 800px everything stacks; the clock block goes below the sheet.

## 5. Cache busting

The owner could not see the Run 4 change, probably because GitHub Pages and the browser cached `style.css`. In `scripts/build_site.py`, rewrite the `href` of `css/style.css` and the `src` of `js/app.js` in `docs/index.html` with `?v=<version>` (the same version string as the JSON). Run the script so the committed `index.html` carries it. Keep the smoke test passing; extend it to check the query string is present.

## 6. Screenshots and critique

Use `scripts/screenshots.py` from Run 4. Before changing anything, copy `runs/screens/` to `runs/screens-run4/`. After the changes, shoot again and also add: home at 1280 and 375, light and dark; the exam page scrolled so the bar is stuck. Compare before and after side by side and write in `LOG.md`:
- Would someone who saw the Run 4 version notice the change within two seconds? If not, the clock or the sheet is not bold enough; push it further.
- Is the clock the first thing the eye lands on in an exam, and the question the second?
- Does the ledger margin look like ruling, or like a red error line? If the latter, mute it more.
- No horizontal scroll at 375px, AA contrast on the dark bar in both themes, focus outlines visible on the dark bar (use `--paper` outlines there).
- Any all-caps labels, eyebrows, middle dots, arrows, em dashes, gradients used as colour, pills, emoji? Remove.
Then remove one more thing that is not needed.

## 7. Tests, commit, push, log

`py tests\smoke.py` and `py tests\validate.py` must pass; no em dashes in `docs/`. Stage, confirm nothing under `materials/`, `release-assets/` or `runs/` is included, commit "Run 5: bolder design", `git push origin main`. Finish `LOG.md` with end time, duration and the critique.
