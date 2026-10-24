# Run 3: site, downloads, README and deploy

Read `CLAUDE.md` first and follow it throughout. Work unattended. Run 2 must be finished: if `bank/exams.json` or `VALIDATION_REPORT.md` is missing, log it and stop.

## 0. Start

Append a "Run 3" heading to `LOG.md` with the start time and this checklist:
- [ ] 1 build script and public data
- [ ] 2 dataset downloads
- [ ] 3 site
- [ ] 4 improvement slot
- [ ] 5 smoke test
- [ ] 6 README
- [ ] 7 commit, push and log

## 1. Build script and public data

Write `scripts/build_site.py`. It reads `bank/` and writes to `docs/data/`:
- `questions.json`: validated and manual_check questions only, without `reference_solution`, `draft_solution`, `solution_file` and anything in `bank/expected/`, unless `docs/data/config.json` has `"showReferenceSolutions": true`.
- `exams.json`, `interpretation.json` (worked answers included, they are computed), `datasets.json`.
- `config.json` (create if missing): `{"showReferenceSolutions": false, "improvementEnabled": false, "repoUrl": "https://github.com/knbarka-beep/examstudio"}`. Never overwrite values Knut has changed.
- A `version` string (date plus short git hash) included in every JSON.

## 2. Dataset downloads

Copy each student dataset file from `materials/` into `docs/files/` with a clean file name (no spaces). Solutions, instructions and slides are never copied.
- Files over 50 MB: zip with Python `zipfile` (ZIP_DEFLATED) into `release-assets/` (gitignored), and link to `https://github.com/knbarka-beep/examstudio/releases/download/datasets-v1/<zipname>`. List every such file, with size, in `README.md` under "Manual step: upload release assets" so Knut can upload them.
- Files under 50 MB go in `docs/files/` directly. Record all sizes in `LOG.md`.

## 3. Site

Plain HTML, CSS and vanilla JS in `docs/`: `index.html`, `css/style.css`, `js/app.js`, `js/improvement.js`. Hash routing (`#/`, `#/manipulation/exams`, `#/manipulation/exams/E012`, `#/manipulation/questions`, `#/manipulation/questions/Q045`, `#/interpretation/exams`, `#/interpretation/exams/R004`). Everything loads from `docs/data/*.json` with `fetch`, so it needs the local server to test.

Views:
- Home: two short sections, data manipulation and data interpretation, each one sentence plus buttons. Text factual, no marketing. Put `[[KNUT: one or two sentences on what the oral exam asks for, in my words]]` as a visible placeholder line at the top.
- Manipulation exams list: "Pick an exam for me" (random, avoids the exam just shown) and a browsable list with the two data files of each exam.
- Exam view: exam id and duration; download buttons for both data files (and "download both"); a timer with Start, Pause and Reset showing time remaining and elapsed time, turning to an "Time is up" state at zero without alert dialogs; the question list on the left on desktop and above on mobile; the active question with subject, id, estimated time, prompt, and a collapsible "Dataset reference" showing the relevant sheets and headers or tables and columns from `datasets.json`; Previous and Next.
- Question bank: filters for subject, case, source file and skill, a text search, and pagination (25 per page). Each question opens on its own route with the same panel as in an exam.
- Interpretation exams: list and random pick; exam view with timer (5 minutes), four question tabs, variable definitions with units and ranges, the model equation, a regression output table (parameter, term, estimate, p-value), and "Show answer" revealing the worked answer.
- Every question view has a plain "Report an issue" link that opens a new GitHub issue in the repo with the question id and data version prefilled in the title and body via URL parameters. No backend.
- If `showReferenceSolutions` is true, a collapsed "Reference solution" block appears under the question. Default off.

Design: system font stack, one neutral palette (off-white background, near-black text, one muted accent such as dark green or navy), square or slightly rounded (max 4 px) buttons, visible focus outlines, 16 px side gutter on phones, no horizontal scroll at 360 px width, semantic HTML with labelled controls and keyboard-operable tabs. Follow rule 7 in `CLAUDE.md` strictly.

## 4. Improvement slot

Leave a clean extension point and nothing more:
- In every question view (exam and bank, manipulation and interpretation) render an empty `<section id="improvement-slot" hidden></section>` directly under the prompt.
- `js/improvement.js` exports `initImprovement(context)` that does nothing by default. `app.js` calls it after each question render, only when `config.improvementEnabled` is true, with `context = { question, exam, datasets, config, slot }` where `slot` is the section element.
- Comment both places with `// IMPROVEMENT: Knut adds his feature here`. The expected results in `bank/expected/` exist so a later feature could use them; do not wire them into the site.

## 5. Smoke test

Write `tests/smoke.py`: confirms every JSON in `docs/data/` parses, every question and exam referenced exists, every download link points either to a file in `docs/files/` or to a listed release asset, no file in `docs/` contains a solution field when `showReferenceSolutions` is false, no file in `docs/` or the git index contains strings that look like keys (`sk-`, `AIza`, `ghp_`, `xox`), and `docs/` contains no em dash characters. Run it and `py tests\validate.py`. Both must pass before pushing.

## 6. README.md

Sections: what the site is (two sentences); live link `https://knbarka-beep.github.io/examstudio/`; how to run locally (`py -m http.server 8000 --directory docs`, then open `http://localhost:8000`); repo structure; how content is built (`py scripts\build_bank.py`, `py tests\validate.py`, `py scripts\build_exams.py`, `py scripts\build_site.py`) and the exam seed; validation status summary from `VALIDATION_REPORT.md`; manual step for release assets; where the improvement goes; and two placeholders: `[[KNUT: paragraph on the added functionality and why it improves on the lecturer's site]]` and `[[KNUT: paragraph on how the starting materials made this case harder than earlier cases, see MATERIALS_NOTES.md]]`. Plain English, no em dashes.

## 7. Commit, push and log

- `git add -A`, check `git ls-files` for anything under `materials/`, `release-assets/` or any solution file; if found, unstage and fix `.gitignore`.
- `git commit -m "Run 3: site and downloads"` then `git push -u origin main`. If the push fails (authentication, repo missing, file too large), do not retry with other methods: write the exact error into `LOG.md` and stop.
- Finish `LOG.md`: end time, duration, file sizes, what Knut still has to do (enable Pages, upload release assets, fill the `[[KNUT]]` markers, active time and cost figures).
