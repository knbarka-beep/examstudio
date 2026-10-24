# Materials notes (Run 1)

Written 23.10.2026 by the unattended Run 1. Source: `MATERIALS_SRC`, copied to `materials/` with `scripts/copy_materials.py`. Full extraction per file: `bank/inventory.json` (kept local, see "Git warning" at the end).

[[KNUT: one paragraph in your own words on why these materials were harder to build from than the earlier cases (Pokémon: one clean CSV; policies: one CSV; invoices: PDFs with JSON ground truth; P-cards: one SQLite table and one case document). The facts below are there to support it.]]

## Overview in numbers

- 31 files, 184.5 MB, in 14 folders over 7 cases (4 Excel, 3 SQL).
- The earlier cases each had one data file and one task document. Here there are 18 data files, 9 instruction files, 2 solution files, 1 slide deck and 1 note.

## Mix of formats

| Format | Files | Notes |
|---|---|---|
| .xlsx | 8 | NYC permits, question sheet, `solutions.xlsx`, ETL cases 2 to 4, IntegrateCo 2015 and 2016 payroll |
| .xlsm | 1 | Restaurant `data.xlsm` with a VBA project |
| .docx | 6 | ETL, IntegrateCo, Restaurant, PWC questions, PWC answers, P-card |
| .pptx | 1 | `PWC.pptx`, 77 slides, the only SQL teaching material |
| .csv | 5 | 1 comma-delimited (ETL Case 1), 4 pipe-delimited (IntegrateCo) |
| .txt | 5 | 1 comma-delimited data export (`NYC_Film_Permits.txt`, 11.1 MB), 3 requirement files, 1 note |
| .db | 4 | `movies.db` (68.9 MB), `songs.db`, `fiftyville.db`, `pcards.db` (94.0 MB) |
| .sqlite | 1 | `Chinook_Sqlite.sqlite` |

Eight file types. The two `.txt` roles (data export and plain instructions) and the two `.csv` delimiters mean the extension says little about the content.

## Delimiter, encoding and header problems

- All four IntegrateCo `.csv` files are pipe-delimited (`|`), as the case text admits ("pipe-delimited text files under the format .csv"). Opening them in Excel gives one column per row until Text to Columns is used.
- `Analytics_mindset_case_studies_ETL_Case1.csv` is comma-delimited but 3 of its 22 data rows split into 9 fields instead of 8, because "Apple, Inc." has an unquoted comma. Accounts Receivables is quoted with thousands separators in some rows ("1,600,000,000") and quoted without them in others ("4300000").
- Encodings: every text file decodes as UTF-8 without BOM. The CS50 requirement files contain curly quotes, so a Windows console shows them as garbage (cp1252). Line endings are CRLF except `mystery (OPTIONAL)/requirements.txt` (LF).
- Header rows are not always row 1: `Assignment_01_Excel-SQL.xlsx` and `solutions.xlsx` start at row 2; the three data dictionary sheets in `data.xlsm` start at row 4; the ETL Case 2 and Case 3 solution sheets have a merged title in row 1 and the real header in row 2.
- `ChartOfAccounts` (ETL Case 4) uses columns A to F but only has headers in A to D. The `Source` sheet reports dimensions A1:B788 but holds 8 rows.
- `PreparerInfo.PreparerName` packs name and job title into one cell with a pipe ("Carolyn Slater|Food Operations Manager") and pads several with non-breaking spaces (U+00A0). Two preparers are systems ("POS", "GUESTSYS").
- `ChartOfAccounts.GLAccountName` "Food Service Conference Accounts Receivable " has a trailing space.
- IntegrateCo job codes are three-digit text ("001"); opened in Excel they become numbers and lose the zeros. The `.xlsx` versions store `Job`/`Project` as numbers where possible (`2016payroll.xlsx` Project 15001 is a number).
- Dates come in many shapes: Excel dates (NYC `.xlsx`, ETL Case 4, restaurant), text `M/D/YYYY H:MM` (NYC `.txt`), text `M/D/YYYY` (IntegrateCo 2015 `.csv`), text `M/D/YYYY 0:00:00` (`pcards.db`), ISO text (Chinook), and separate year, month, day integer columns (`fiftyville.db`).
- ETL Case 4 EffectiveDate is in June 2020 while descriptions say "JUN 2016".

## Same data given twice

- NYC film permits: `NYC_Film_Permits.xlsx` and `NYC_Film_Permits.txt` hold the same 33,502 rows and 14 columns (EventID sequence identical). The `.txt` is comma-delimited with text dates. The assignment asks for `NYC_Film_Permits.csv`, which exists in neither form.
- IntegrateCo 2015 payroll: `.csv` (pipe) and `.xlsx`, 4,981 rows each. All cells agree except Pay_Date (text in the csv, real dates in the xlsx).
- IntegrateCo 2016 payroll: `.csv` and `.xlsx`, 804 rows each, identical cell values.
- ETL Case 4: `Case 4 solution` repeats all 789 JELineItems rows in columns A to J.

## Schema differences between years (IntegrateCo 2015 vs 2016)

| 2015 (16 columns, one row per employee, pay date and job) | 2016 (11 columns, one row per employee and project, no dates) |
|---|---|
| Pay_Date, Payroll_ID | none |
| Emp_No | Employee_Number (plus a new Employee_ID) |
| First_Name, Last_Name | Employee_Name |
| Home_Div, Work_Div | none |
| Job | Project |
| Reg_Hrs, OT_Hrs | Hours, OT_Hours |
| Reg_Pay + OT_Pay | Gross_Wages |
| Fica_Medc, Futa, Suta, Work_Comp | SocSec_Medicare, FUTA, SUTA, Work_Comp |

- The job code is embedded in `Job`/`Project` (two-digit year, optional H or S, three-digit code, optional B or SG). It has to be extracted before the years can be compared.
- 68 of 804 rows in 2016 have no Employee_ID, Employee_Number or Employee_Name (the "phantom" entries the case asks about).
- One 2015 row has Job `14S1440`, giving job code 144, outside 001 to 012.
- 2015 has 37 distinct pay dates but 56 distinct Payroll_IDs, although the appendix says each date has one ID.
- The location file joins on full name only ("FirstName LastName"); all 2015 and 2016 names match it.
- Totals check out with the case: 2016 gross wages 1,352,789.75 minus 2015 gross pay 1,086,734.19 = 266,055.56 (the CFO's "approximately $266,000").

## Macros

- `data.xlsm` contains `xl/vbaProject.bin` with modules `Module1`, `ThisWorkbook` and six sheet modules (`Sheet6` to `Sheet11`). Module names were read from the OLE directory with `olefile`; nothing was executed. All reading uses openpyxl/pandas, which ignore macros.
- No other workbook has a VBA project or any formula cells.

## Solutions mixed in with assignments

- `1. Excel Part 1/PWC Excel Assignment/solutions.xlsx` sits next to the assignment and holds all 20 answers. The assignment workbook has an empty Answer column.
- `2. SQL part 1/Assignments/pwc assignment/PWC answers.docx` sits next to `PWC SQL.docx`. 20 of 23 answers are text; 3 (phone numbers without area code, countries by invoice total, downloads per price) have no text answer, only 2 embedded images.
- Some PWC answers are approximate or one answer covers two questions: "Approximately 55.5 years", "Approximately 5 years", and "256 tracks have been downloaded twice" for both Q19 and Q21.
- ETL Case 2, 3 and 4 workbooks each contain a sheet named "Case N solution". Checked cell by cell: they are empty templates. Case 2 and 3 fill only EmployeeCode, FirstName and LastName (3 of 14 header columns); Case 4 fills only the copied JELineItems columns A to J (10 of 17). No answers are present, so they are classed as datasets.
- No data file was found to contain answers already. `data.xlsm` has no regression output sheet.
- In `bank/inventory.json` the classes are: 18 dataset, 9 instructions, 2 solution, 1 slides, 1 note.

## Misspelled or inconsistent names

- `movies/requierements.txt` and `songs/requierements.txt` (misspelled), but `mystery (OPTIONAL)/requirements.txt` (correct).
- Folder case: `1. Excel Part 1` vs `1. Excel part 2`, `part 3`, `part 4`; `2. SQL part 1`, `2. SQL part 2`.
- Mystery folders: on disk there is only `mystery (OPTIONAL)`, holding both `requirements.txt` and `fiftyville.db`. The upload list's `mystery OPTIONAL/fiftyville.db` does not exist; it looks like an artefact of the upload.
- The case documents name files differently from disk: ETL docx says `Analytics_mindset_case_studies_Case2_Excel.xlsx` (disk: `..._ETL_Case2_Excel.xlsx`), tab "Case 2 data" (disk: "Case 2"), and tab "GLAccounts" (disk: "ChartOfAccounts"). IntegrateCo docx says `Analytics_mindset_case_studies_jobcodes.csv`, `..._2015payroll.csv`, `..._locations.csv` (disk: all with `IntegrateCo_`).
- ETL Case 3 says pay period codes are W, We, M or Mo; the data only has W (258), Mo (181) and M (158).
- P-card case: the master-query tip says "CustomerFirstInitial" (field is CardholderFirstInitial); Task 4 Q22 asks for the label PercDiffFrom2010 but compares with 2011; Q15 says "related to problem 12" but means Q14.
- Restaurant dictionaries: daysSinceLastPurch says first-time customers are 9,999 and then uses 99,999 in the example; "Faherenheit"; weather `date` is described as "date of the game".
- Songs requirement 1 says "two columns for the name of each song" (it means name and energy).

## Missing or too-large files

| File | Size | Where found |
|---|---|---|
| `2. SQL part 1/Assignments/cs50 assignment/movies/movies.db` | 68.94 MB | Already in `MATERIALS_SRC`; copied with the rest |
| `2. SQL part 2/Pcards Assignment/pcards.db` | 94.00 MB | Already in `MATERIALS_SRC`; copied with the rest. One table `pcards`, 489,178 rows |
| `1. Excel Part 1/PWC Excel Assignment/NYC_Film_Permits.txt` | 11.12 MB | Already in `MATERIALS_SRC`. This is the third file that did not upload |

No search outside the materials was needed.

### Files not in the uploaded set

| File on disk | Size |
|---|---|
| `1. Excel Part 1/PWC Excel Assignment/NYC_Film_Permits.txt` | 11.12 MB |
| `2. SQL part 1/Assignments/cs50 assignment/movies/movies.db` | 68.94 MB |
| `2. SQL part 1/Assignments/cs50 assignment/mystery (OPTIONAL)/fiftyville.db` | 0.27 MB (uploaded under the other folder name, see above) |
| `2. SQL part 2/Pcards Assignment/pcards.db` | 94.00 MB |

### Referred to but not present anywhere

- `NYC_Film_Permits.csv` (named in `Assignment_01_Excel-SQL.xlsx`). The `.txt` export is the same data.
- `Analytics_mindset_case_studies_PCard_FY2010.csv` to `..._FY2015.csv` (six files, P-card Task 2 and 3). The course skips those tasks and gives `pcards.db` instead.
- `sample.sqlite` (PWC.pptx appendix slide 74). Chinook is used instead.
- The prediction formula for IntegrateCo Part 4 Q9 ("you will use the following formula:"): the docx has no images and no formula text, so it is lost.
- 17 images in the ETL docx (sample tables, the Case 1 screenshot, the expected first rows for Case 2, 3 and 4) are not readable as text.
- The "attached worksheet" for P-card Task 6 exists only as a table inside the docx.

### Files I could not read

None. All 31 files copied with non-zero size and parsed without error.

## P-card data facts

- `pcards.db` is already restricted to OSU: all 489,178 rows have AgencyNumber 1000 "OKLAHOMA STATE UNIVERSITY". No TransactionDate is empty. The drafts still filter on both, as the case instructs.
- TransactionDate and PostedDate are text `M/D/YYYY 0:00:00`. The table also has Year and Month columns; they match the parsed TransactionDate in every row. The drafts parse the text as required.
- Calendar years 2010 to 2014; 2010 is partial (22,653 rows against about 116,000 for other years).
- 15,842 negative amounts (returns). 135 rows have an empty Description. FullName always equals first initial plus last name.
- The table has no indexes; the slowest draft (Task 5 control 4) runs in about 5 seconds.

## Optional material and spread-out instructions

- Optional: the Fiftyville mystery (folder and file both say OPTIONAL), P-card Task 4 queries 13 to 22, Task 6 (Access only) and Task 7. These are tagged `"optional": true`.
- P-card docx marks Part II and Part III "(we skip)"; Part IV says "First 12 queries are part of the assignment, the rest are optional".
- The ETL assignment is one docx with an overview case and four sub-cases, each with its own data folder.
- PWC SQL: questions in `PWC SQL.docx`, the same questions split into 5 exercises in `PWC.pptx`, answers in `PWC answers.docx`.
- CS50: tasks in two `requierements.txt` files plus a `Note.txt` that only points to an external CS50 web page.
- Restaurant: six tasks in a short docx; variable definitions only inside `data.xlsm` (three dictionary sheets).

## Tasks that did not become checkable questions

- ETL overview "Required" (the six questions from Mike): conceptual, no data.
- ETL Case 1 "document the steps": narrative. The data problems themselves became 7 questions.
- ETL Case 2 and 3: the Text to Columns and FlashFill techniques cannot be checked; the extracted values can, so the questions ask for counts derived from them.
- ETL Case 4: the full template sheet is split into single lookups.
- IntegrateCo Part 1 (questions to ask, the four V's), Part 2 formatting rules (highlight new columns, tab names), Part 3 Q3 (investigation) and Q4 (memo): judgement and writing.
- IntegrateCo Part 4 Q9: the formula is missing from the document.
- P-card Task 1 (two questions to test), Task 2 (four V's), Task 3 (skipped by the course; the CSV files are not provided), Task 6 (Access form) and the "Results and conclusion" column of Task 5.
- PWC.pptx slide 76 (draw an ERD in groups).
- Restaurant "Communicate" and "explain to Bob" parts: covered by the interpretation bank (predict, coefficient, significance, dummy), not by data questions.

## Assumptions

Excel Part 1 (NYC):
1. `NYC_Film_Permits.txt` is the `.csv` the assignment names. Questions use the `.xlsx` (same data, real dates).
2. Questions 10 to 20 consider only EventType "Shooting Permit", as question 9 says.
3. Invalid zip code = present but not five characters long (gives the reference 2).
4. More than one Community Board = the field contains a comma.
5. "On or near Broadway" = ParkingHeld contains "BROADWAY".
6. "Since 2013" uses EnteredOn on or after 01.01.2013.
7. "At least a partial day on a Friday" = any calendar day from the start date to the end date is a Friday.
8. Possible dispute for Run 2: Brooklyn shoots exceed Manhattan in both 2017 (1,719 vs 1,550) and 2018 (176 vs 138, data only to February); the reference says 2017.

Excel Part 2 (ETL):
9. Case 1 "no usable Inventories value" = blank, only spaces, or a dash; a real 0 counts as usable.
10. Case 2/3 counts use the extracted fields as defined in the case text.

Excel Part 3 (IntegrateCo):
11. 2015 gross pay = Reg_Pay + OT_Pay; total hours = Reg_Hrs + OT_Hrs, for both "per hour" figures.
12. Job code = the three digits after the two-digit year and an optional H or S.
13. Location is joined on "First_Name Last_Name" in 2015 and Employee_Name in 2016.
14. Part 4 Q4 treats all pay on one Pay_Date as one pay period, as the case says.

Excel Part 4 (Restaurant):
15. "Aggregated sales" = sum of netTotal over all menu items per date. Lag predictors (sales_7, sales_28, sales_364) are the sums of the item-level lag columns per date.
16. Dates missing from gameData get gameDay = 0 and homeGame = 0.
17. The prediction "7 days from the last day" targets 07.01.2019: sales_7 = sales on 31.12.2018 (3,252) and sales_364 = sales on 08.01.2018 (2,841), both inside the observed ranges.
18. Rows with missing weather are dropped only in models that use weather (n = 309 instead of 312).
19. Extra models M5 to M8 use only variables in the workbook; M4 is the interaction the instructions ask for, and no other interaction was fitted.

SQL Part 1 PWC:
20. Q2 "first 5 rows" means in CustomerId order. Q7 uses BillingCountry. Q12 is about employees (exercise 3 is about employees). Q14 age uses 365.25-day years.
21. Q21 breaks ties by TrackId, because 256 tracks share the top count of 2.
22. Possible dispute for Run 2: Q22 with the stated assumption (all tracks of an album on one invoice) gives 41 albums in my draft; the reference says 49.

SQL Part 1 CS50:
23. Variants use values present in the data (2010, 2012, rating 9.5, "Harry Potter", Ed Sheeran, XXXTENTACION).
24. The Fiftyville mystery is split into six steps; the thief, city and accomplice follow from the clues in the interviews.

SQL Part 2 P-card:
25. Name = CardholderFirstInitial + space + CardholderLastName.
26. Task 4 Q1 and Q2 would return 489,178 and about 116,000 rows; they are reduced to the first ten rows of the same sort.
27. Returned value is kept negative (sum of the negative amounts); "largest" return = most negative.
28. Q18: vendor "Amazon.com" in any letter case, purchases only (amount above 0).
29. Task 5 controls 5 and 6: "exclude double payments" = the vendor-day (or person-day) group has exactly two transactions.
30. Task 5 control 7 uses substring matches as written in the case, so "inn" also matches inside other words.
31. Task 7 Q2 to Q4 use 2014 only ("Using the OSU 2014 calendar year data").

General:
32. Every question without a reference in the materials has `solution_source: "generated"` and still needs Run 2.
33. `expected_answer_hint` only describes the form of the answer (for example "A whole number."), never the value.

## Biggest five obstacles (by cost)

1. IntegrateCo: two payroll systems with different columns, different aggregation (per pay date vs per project), pipe-delimited `.csv`, the job code buried inside a composite field, 68 phantom rows and an invalid job code. Every comparison question needs extraction and alignment first.
2. Solutions next to assignments, in uneven quality: `solutions.xlsx` is complete, `PWC answers.docx` has 3 answers only as images and several approximations, and the three "Case N solution" sheets look like answers but are empty templates. Two references may disagree with the data (NYC Q13, PWC Q22).
3. File locations and names: three large files outside the uploaded set, a P-card case written for six CSV files that are replaced by a 94 MB database, document file and tab names that do not match the disk, misspelled requirement files and a duplicated mystery folder name.
4. Many small messy-data problems that each need an exact definition before they can be checked (ETL Case 1, Case 3 codes, Case 4 lookups with composite keys and padded names, NYC zip codes and multi-value fields).
5. Format spread: eight file types, an `.xlsm` with macros that must not run, and at least six different date representations, including dates stored as text that SQLite cannot use without parsing.

## Git warning

`bank/inventory.json` holds the full extracted text of the case documents and of the two solution files. It was committed once by mistake in commit `d8c0bfd` and untracked in the next commit (now in `.gitignore`). Commits are local only; nothing has been pushed. I did not rewrite history (rule 9). [[KNUT: decide before the first push (Run 3 pushes) whether to remove `bank/inventory.json` from commit d8c0bfd, for example by squashing the local commits; otherwise the case texts and solution text become public with the repository history.]] Also note that `bank/questions.json` stores the materials' reference answers (for Run 2), so they are in the repository too, though not in `docs/`.
