# Run 1: inventory, material notes and question bank

Read `CLAUDE.md` first and follow it throughout. Work unattended: do not stop to ask questions. When something is ambiguous, take the most reasonable reading, write the assumption in `MATERIALS_NOTES.md`, and carry on.

## 0. Start

- Append a "Run 1" heading to `LOG.md` (create the file with the three sections from `CLAUDE.md` if missing), record the start time, and copy this checklist under it:
  - [ ] 1 repo setup
  - [ ] 2 copy materials and locate missing files
  - [ ] 3 inventory of every file
  - [ ] 4 question bank
  - [ ] 5 interpretation bank
  - [ ] 6 MATERIALS_NOTES.md
  - [ ] 7 local commit and log

## 1. Repo setup

- If `.git` does not exist: `git init -b main`, then `git remote add origin https://github.com/knbarka-beep/examstudio.git`. Do not push in this run.
- Create `.gitignore` with at least: `materials/`, `release-assets/`, `__pycache__/`, `*.pyc`, `.env`, `.env.*`, `runs/`, `.venv/`.
- Create folders: `bank/`, `bank/expected/`, `scripts/`, `tests/`, `docs/`, `docs/data/`, `docs/files/`, `release-assets/`.
- Install what you need: `py -m pip install --user openpyxl python-docx python-pptx pandas statsmodels`.

## 2. Copy materials and locate missing files

- Copy `MATERIALS_SRC` into `materials/` with a Python script (`scripts/copy_materials.py`, `shutil.copytree` with `dirs_exist_ok=True`; mirror the folder structure, do not move or alter the source). OneDrive may hold some files as cloud-only placeholders; if a copy fails or a file has size 0, log it in `MATERIALS_NOTES.md` under "Files I could not read".
- Three files did not upload to Knut's chat project because of size. Two are known: the CS50 `movies.db` and the P-card `pcards.db`. Find each one:
  1. inside `materials/` as copied;
  2. otherwise search `C:\Users\knbar\Documents\` and `C:\Users\knbar\OneDrive\Skrivebord\AI in Accounting and Business\` recursively for the file name.
  If found outside the materials, copy it into the matching place under `materials/` (`2. SQL part 1/Assignments/cs50 assignment/movies/` and `2. SQL part 2/Pcards Assignment/`). For `pcards.db` check it has a table `pcards`; record its row count.
- The third missing file is unknown. Compare everything in `materials/` against this list of files that did upload, and report every file on disk that is NOT on the list, with its size in MB, in `MATERIALS_NOTES.md` under "Files not in the uploaded set". Also report any file that the case documents refer to but that does not exist anywhere.

Uploaded set (paths relative to `materials/`):
```
1. Excel Part 1/PWC Excel Assignment/Assignment_01_Excel-SQL.xlsx
1. Excel Part 1/PWC Excel Assignment/solutions.xlsx
1. Excel Part 1/PWC Excel Assignment/NYC_Film_Permits.xlsx
1. Excel part 2/ETL Assignment/Analytics_mindset_case_studies_ETL.docx
1. Excel part 2/ETL Assignment/data/case 1/Analytics_mindset_case_studies_ETL_Case1.csv
1. Excel part 2/ETL Assignment/data/case 2/Analytics_mindset_case_studies_ETL_Case2_Excel.xlsx
1. Excel part 2/ETL Assignment/data/case 3/Analytics_mindset_case_studies_ETL_Case3_Excel.xlsx
1. Excel part 2/ETL Assignment/data/case 4/Analytics_mindset_case_studies_ETL_Case4_Excel.xlsx
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_Excel.docx
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2015payroll.csv
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2015payroll.xlsx
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2016payroll.csv
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_2016payroll.xlsx
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_locations.csv
1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_jobcodes.csv
1. Excel part 4/Regression Assignment/Restaurant/Instructions.docx
1. Excel part 4/Regression Assignment/Restaurant/data.xlsm
2. SQL part 1/Assignments/cs50 assignment/Note.txt
2. SQL part 1/Assignments/cs50 assignment/movies/requierements.txt
2. SQL part 1/Assignments/cs50 assignment/mystery (OPTIONAL)/requirements.txt
2. SQL part 1/Assignments/cs50 assignment/mystery OPTIONAL/fiftyville.db
2. SQL part 1/Assignments/cs50 assignment/songs/requierements.txt
2. SQL part 1/Assignments/cs50 assignment/songs/songs.db
2. SQL part 1/Assignments/pwc assignment/PWC.pptx
2. SQL part 1/Assignments/pwc assignment/PWC SQL.docx
2. SQL part 1/Assignments/pwc assignment/PWC answers.docx
2. SQL part 1/Assignments/pwc assignment/Chinook_Sqlite.sqlite
2. SQL part 2/Pcards Assignment/Analytics_mindset_case_studies_PCard.docx
```
Note: the upload shows two different mystery folders, `mystery (OPTIONAL)` and `mystery OPTIONAL`. Check what is actually on disk.

## 3. Inventory of every file

Write `scripts/inventory.py` and run it. It walks `materials/` and writes `bank/inventory.json` with one entry per file:

- docx: full text with headings and numbered tasks preserved (python-docx), plus tables as rows.
- pptx: text per slide, including notes.
- xlsx / xlsm: every sheet with name, dimensions, header row (detect it; it may not be row 1), row count, column types sampled, whether formulas exist, merged cells, hidden sheets. For xlsm, open the zip and record whether `vbaProject.bin` exists and the names of VBA modules if readable. Never execute macros.
- csv / txt: detect the delimiter (several files are pipe-delimited despite the .csv extension), encoding, BOM, header, row count, and a 5-row sample.
- sqlite / db: every table and view with columns, types, row count, and foreign keys.
- Everything: size in bytes and SHA-256.

Also write `docs/data/datasets.json`: the public subset students need for the "dataset reference" panel (one entry per student data file: id, human label, case, file name, size, sheets with headers or tables with columns). No case texts, no solutions.

Classify every file in `bank/inventory.json` as one of: `dataset`, `instructions`, `solution`, `slides`, `note`. `solutions.xlsx` and `PWC answers.docx` are solutions; check every other file for solution content mixed into it (for example a worksheet that already contains the answers).

## 4. Question bank

Write `scripts/build_bank.py` and run it to produce `bank/questions.json`. Base the questions on the tasks the case documents actually set (ETL docx, IntegrateCo docx, PWC SQL docx and pptx, Assignment_01_Excel-SQL.xlsx, cs50 requirement files, P-card docx), split into single practice questions a student can answer in roughly 1 to 3 minutes. Write the prompts yourself in plain short English; do not copy long passages of the case text.

You may add variants of a task only where the original task is parameterised by a value that exists in the data (another borough, another year, another division, another genre) and the skill stays identical. Every variant must be answerable from the same file.

Schema per question:
```json
{
  "id": "Q001",
  "subject": "Excel | SQL",
  "case": "Excel Part 1 | Excel Part 2 | Excel Part 3 | Excel Part 4 | SQL Part 1 PWC | SQL Part 1 CS50 | SQL Part 2 P-card",
  "source_doc": "relative path of the document the task comes from",
  "source_task": "task number or heading in that document",
  "dataset_ids": ["ids from datasets.json"],
  "required_objects": {"sheets": [], "headers": [], "tables": [], "columns": []},
  "prompt": "what the student must do",
  "skills": ["import", "filter", "sort", "lookup", "pivot", "conditional count", "date arithmetic", "text functions", "join", "group by", "having", "subquery", "data cleaning", "delimiter handling", "..."],
  "estimated_minutes": 2,
  "is_variant_of": null,
  "reference_solution": null,
  "solution_source": "materials | generated | none",
  "solution_file": null,
  "draft_solution": null,
  "expected_answer_hint": null,
  "status": "draft"
}
```
Rules:
- Every SQL question gets a `draft_solution` query (SQLite dialect), even when the materials give one, so Run 2 can execute it. If the materials give the query or the result, store that as `reference_solution` with `solution_source: "materials"`.
- For Excel questions with a numeric or tabular answer, put the method in `draft_solution` (formula or pivot steps) and, where the materials contain the answer (solutions.xlsx and similar), store it in `reference_solution`.
- P-card questions must respect the data: dates are text `M/D/YYYY 0:00:00` and need parsing; negative amounts are returns.
- Optional material (the fiftyville mystery) is tagged `"optional": true`.
- Keep every question within what the materials train. If a task cannot be turned into a checkable question, leave it out and note it in `MATERIALS_NOTES.md`.

## 5. Interpretation bank

The second oral exam part is data interpretation of regression output. Read `Excel part 4/Regression Assignment/Restaurant/Instructions.docx` and `data.xlsm`.

- Fit the model(s) the instructions ask for with statsmodels (OLS) on the real data. Record coefficients, standard errors, p-values, R squared and n in `bank/models.json`, with the variable definitions, units, ranges and dummy coding taken from the data and instructions.
- You may fit additional specifications on the same data (different predictor subsets, a dummy, an interaction only if the instructions cover it) to get more models. Every model must be fitted on `data.xlsm`, never invented.
- Write `bank/interpretation.json`: questions of four kinds, mirroring the skills in the Restaurant case: predict a value, interpret a coefficient in words with units, judge significance at 5 % from the p-value, and explain a dummy against its reference group. Each question holds its model id, the prompt, and a worked answer with the arithmetic shown (answers may be public; they are computed, not taken from a solution file). Use only predictor values inside the observed range and say the range in the question.

## 6. MATERIALS_NOTES.md

Write it for a human who has to explain, in one paragraph, why these materials were harder to build from than the earlier cases (Pokémon: one clean CSV; policies: one CSV; invoices: PDFs with JSON ground truth; P-cards: one SQLite table and one case document). Record, with file names and concrete numbers:
- the mix of formats (docx, pptx, xlsx, xlsm, csv, pipe-delimited csv, txt, sqlite) and how many of each;
- delimiter, encoding and header problems; same data given twice in different formats; schema differences between years (2015 vs 2016 payroll);
- macros in xlsm;
- solution files mixed in with assignment files, and any answers already present in data files;
- misspelled or inconsistent file and folder names (for example `requierements.txt`, the two mystery folders);
- missing or too-large files and where they were found;
- optional folders, notes and instructions spread over several documents;
- tasks that could not become checkable questions and why;
- every assumption you made.
End with a short "Biggest five obstacles" list ranked by how much they cost.

## 7. Finish

- `git add -A` then `git commit -m "Run 1: inventory, material notes, question bank"`. Check with `git ls-files` that nothing under `materials/` and no solution document is tracked.
- In `LOG.md`: tick the checklist, record end time and duration, counts (files inventoried, questions by subject and case, interpretation questions, models), and anything that failed.
