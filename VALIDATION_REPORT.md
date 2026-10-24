# Validation report

Written by `py tests\validate.py`. Re-run it after editing the bank; this file is replaced each time.

## Summary

| Subject | validated | manual_check | disputed | excluded | failed | Total |
|---|---:|---:|---:|---:|---:|---:|
| Excel | 77 | 4 | 1 | 0 | 0 | 82 |
| SQL | 96 | 0 | 1 | 0 | 0 | 97 |
| Interpretation | 49 | 0 | 0 | 0 | 0 | 49 |
| All | 222 | 4 | 2 | 0 | 0 | 228 |

## Questions that are not validated

| Id | Status | File | What failed and why |
|---|---|---|---|
| Q015 | disputed | NYC_Film_Permits.xlsx | solutions.xlsx says 2017. Shooting permits by year of StartDateTime: Brooklyn exceeds Manhattan in 2017 (1,719 vs 1,550) and also in 2018 (176 vs 138). The 2018 data stops in February, so 2017 is the only full year, but the question as set has two answers. |
| Q026 | manual_check | Analytics_mindset_case_studies_ETL_Case1.csv | The row count is computed (3); the cause (the unquoted comma in 'Apple, Inc.') is checked by a person. |
| Q028 | manual_check | Analytics_mindset_case_studies_ETL_Case1.csv | The value is computed; naming the two formats (parentheses and minus sign) is checked by a person. |
| Q031 | manual_check | Analytics_mindset_case_studies_ETL_Case1.csv | The company and the cleaned ticker are computed; the formula is checked by a person, since several formulas work. |
| Q082 | manual_check | data.xlsm | The count is computed; the reason it matters for a regression is checked by a person. |
| Q108 | disputed | Chinook_Sqlite.sqlite | PWC answers.docx says 49. With its own assumption (all tracks of an album on one invoice) there are 49 invoice and album pairs but only 41 distinct albums, because 8 albums are downloaded complete twice. The question asks for distinct albums, so 49 looks like a count of downloads, not of albums. |

## Fixes made to generated drafts

| Id | Problem | Fix |
|---|---|---|
| Q072 | The prompt did not say the payroll files are pipe-delimited. | Added '(pipe-delimited)' to the prompt (build_bank.py and questions.json). |
| Q073 | The prompt did not say the payroll files are pipe-delimited. | Added '(pipe-delimited)' to the prompt (build_bank.py and questions.json). |
| Q124 | Three films tie on 7.3 at fifth place, so 'the five highest rated' had no single answer. | Prompt now says ties go in alphabetical order of title; draft orders by rating DESC, title. |

## Observations (no change made)

- P-card: 12 cardholder names occur in 2014 in two letter cases (for example 'C Stover' and 'C STOVER'). The drafts follow the case text (Name = first initial and last name, as stored), so GROUP BY Name keeps them apart. This affects the per-person questions (Q152 to Q155, Q168 to Q170, Q172 to Q174, Q178).
- IntegrateCo: 2015 gross pay for job code 009 (Q058) is 0.00 while 2016 has wages on 009 (Q059). The zero is what the data gives, not a parsing error.
- Ties at a LIMIT cut-off are not detected automatically; Q085, Q107, Q109, Q124, Q129, Q140 and Q143 were checked by hand in Run 2.

## Exams

Seed 2026. Data manipulation exams: 304. Data interpretation exams: 30. Built by `py scripts\build_exams.py`.
- etl_case1 + chinook: 10
- etl_case1 + cs50_movies: 10
- etl_case1 + cs50_songs: 10
- etl_case1 + pcards: 10
- etl_case2 + chinook: 10
- etl_case2 + cs50_movies: 10
- etl_case2 + cs50_songs: 10
- etl_case2 + pcards: 10
- etl_case3 + chinook: 10
- etl_case3 + cs50_movies: 10
- etl_case3 + cs50_songs: 10
- etl_case4 + chinook: 10
- etl_case4 + cs50_movies: 10
- etl_case4 + cs50_songs: 10
- etl_case4 + pcards: 10
- ic_payroll2015_csv + chinook: 10
- ic_payroll2015_csv + cs50_movies: 10
- ic_payroll2015_csv + cs50_songs: 10
- ic_payroll2015_csv + pcards: 4
- ic_payroll2016_csv + chinook: 10
- ic_payroll2016_csv + cs50_movies: 10
- ic_payroll2016_csv + cs50_songs: 10
- ic_payroll2016_csv + pcards: 10
- nyc_film_permits_xlsx + chinook: 10
- nyc_film_permits_xlsx + cs50_movies: 10
- nyc_film_permits_xlsx + cs50_songs: 10
- nyc_film_permits_xlsx + pcards: 10
- restaurant_data + chinook: 10
- restaurant_data + cs50_movies: 10
- restaurant_data + cs50_songs: 10
- restaurant_data + pcards: 10
