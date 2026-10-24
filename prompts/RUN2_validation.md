# Run 2: validation and exam composition

Read `CLAUDE.md` first and follow it throughout. Work unattended. Run 1 must be finished: if `bank/questions.json` or `bank/inventory.json` is missing, log that in `LOG.md` and stop.

## 0. Start

Append a "Run 2" heading to `LOG.md` with the start time and this checklist:
- [ ] 1 validation script
- [ ] 2 SQL checks
- [ ] 3 Excel checks
- [ ] 4 interpretation checks
- [ ] 5 fix or exclude
- [ ] 6 compose exams
- [ ] 7 report, commit and log

## 1. Validation script

Write `tests/validate.py`, runnable as `py tests\validate.py`. It exits with code 0 only when every question with status other than `excluded` passes. It prints a one-line summary and writes `VALIDATION_REPORT.md`. It must be re-runnable at any time, so Knut can use it after editing content.

Structural checks for every question: unique ids, required fields present, `dataset_ids` exist in `docs/data/datasets.json`, the dataset file exists in `materials/`, `is_variant_of` points to an existing id, skills not empty, estimated minutes between 0,5 and 5.

## 2. SQL checks

For every SQL question:
- Open the database read-only (`file:...?mode=ro` URI). Check every table and column in `required_objects` exists.
- Run `draft_solution` with a 30-second timeout (use `conn.set_progress_handler` or a thread). `pcards.db` is large; that is fine, just enforce the timeout.
- If `reference_solution` from the materials is a query, run it too and compare results. If it is a stated result (numbers or a table from `PWC answers.docx` or similar), compare against the draft's result.
- Comparison: same columns in the same order where order is asked for; rows compared as multisets unless the question asks for an order, then as sequences; floats rounded to 2 decimals; text trimmed.
- Save the canonical result to `bank/expected/<id>.json`: column names, row count, the first 20 rows, and a SHA-256 of the canonical full result. These files stay in `bank/`, never in `docs/`.
- A question passes when the draft runs, returns a non-empty result (unless empty is the correct answer and the question says so), and matches the materials' reference when one exists.

## 3. Excel checks

For every Excel question:
- The file opens, every sheet in `required_objects.sheets` exists and every header in `required_objects.headers` exists in that sheet's detected header row (case and whitespace sensitive; report near-misses such as trailing spaces separately).
- Where the answer is computable (counts, sums, averages, filters, sorts, lookups, pivots, date differences), compute it independently with pandas from the raw file and save it to `bank/expected/<id>.json` in the same format as SQL. If the materials give the answer (`solutions.xlsx` and others), compare the two and report the difference.
- Pipe-delimited CSVs must be read with the right delimiter; check the question tells the student that an import step is needed if the file needs one.
- Mark questions whose answer cannot be computed automatically (for example "explain how you would handle dates") as `manual_check` with a reason. They are allowed in the bank but listed in the report.

## 4. Interpretation checks

For every item in `bank/interpretation.json`: refit its model from `data.xlsm` and confirm coefficients match `bank/models.json` to 4 decimals, recompute the worked answer, confirm predictor values are inside the observed range, and confirm the stated significance verdict matches the p-value at 5 %.

## 5. Fix or exclude

- If a failure is clearly a bug in a generated draft (wrong column name, wrong join, typo), fix the draft and re-run. Record the fix in the report.
- Never change a materials reference to make a test pass. If the materials' answer looks wrong, keep the question, set status `disputed`, and explain in the report with evidence. Knut may raise these with the lecturer.
- Anything you cannot make pass gets status `excluded` and a reason. Do not delete questions.
- Set status `validated` on everything that passes.

## 6. Compose exams

Write `scripts/build_exams.py` producing `bank/exams.json` from validated questions only (`manual_check` questions may appear in exams).

Mirror the exam format of the lecturer's live Exam Studio, because the oral exam uses that format:
- Data manipulation exam: 5 questions, 3 Excel then 2 SQL, using exactly two data files (one Excel-side file, one database), 8 minutes in total. No two questions in one exam may be variants of each other.
- Data interpretation exam: 4 questions, 5 minutes, ideally one of each kind (predict, coefficient, significance, dummy), and each from a different model where possible.

Use a fixed random seed so the set is reproducible. Generate a sensible number, not an inflated one: for manipulation exams, up to 10 per valid file pair; for interpretation exams, up to 30. Give exams ids `E001` and `R001` onward. Write the seed and the counts into `README.md` later (Run 3) and into `LOG.md` now.

## 7. Report, commit and log

`VALIDATION_REPORT.md` contains: a summary table (subject by status: validated, manual_check, disputed, excluded), then every non-validated question with id, file, what failed and why, then every fix made to a draft, then the exam counts. Keep it factual.

Run `py tests\validate.py` one final time and record its exit code. Then `git add -A`, `git commit -m "Run 2: validation and exams"`, confirm with `git ls-files` that nothing in `materials/` is tracked, and finish the `LOG.md` entry with end time, duration and counts.
