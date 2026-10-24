"""Build bank/questions.json from the tasks set in the course materials.

Each question is one small, checkable piece of a task in a case document.
SQL drafts are SQLite and self-contained. Excel drafts describe the formula or
pivot steps. Reference solutions are only filled where the materials state them
(solutions.xlsx, PWC answers.docx). Everything else is "generated" and is checked
in Run 2.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NYC_DOC = "1. Excel Part 1/PWC Excel Assignment/Assignment_01_Excel-SQL.xlsx"
NYC_SOL = "1. Excel Part 1/PWC Excel Assignment/solutions.xlsx"
ETL_DOC = "1. Excel part 2/ETL Assignment/Analytics_mindset_case_studies_ETL.docx"
IC_DOC = "1. Excel part 3/IntegrateCo Assignment/Analytics_mindset_case_studies_IntegrateCo_Excel.docx"
REST_DOC = "1. Excel part 4/Regression Assignment/Restaurant/Instructions.docx"
PWC_DOC = "2. SQL part 1/Assignments/pwc assignment/PWC SQL.docx"
PWC_SOL = "2. SQL part 1/Assignments/pwc assignment/PWC answers.docx"
MOV_DOC = "2. SQL part 1/Assignments/cs50 assignment/movies/requierements.txt"
SONG_DOC = "2. SQL part 1/Assignments/cs50 assignment/songs/requierements.txt"
FIFTY_DOC = "2. SQL part 1/Assignments/cs50 assignment/mystery (OPTIONAL)/requirements.txt"
PC_DOC = "2. SQL part 2/Pcards Assignment/Analytics_mindset_case_studies_PCard.docx"

NYC_HEAD = ["EventID", "EventType", "StartDateTime", "EndDateTime", "EnteredOn", "EventAgency", "ParkingHeld",
            "Borough", "CommunityBoard(s)", "PolicePrecinct(s)", "Category", "SubCategoryName", "Country", "ZipCode"]

QUESTIONS = []
KEYS = {}


def add(key, subject, case, source_doc, source_task, dataset_ids, prompt, skills, minutes, draft,
        sheets=(), headers=(), tables=(), columns=(), ref=None, ref_file=None, hint=None, variant_of=None,
        optional=False):
    q = {
        "id": f"Q{len(QUESTIONS) + 1:03d}",
        "subject": subject,
        "case": case,
        "source_doc": source_doc,
        "source_task": source_task,
        "dataset_ids": list(dataset_ids),
        "required_objects": {"sheets": list(sheets), "headers": list(headers), "tables": list(tables),
                             "columns": list(columns)},
        "prompt": prompt,
        "skills": list(skills),
        "estimated_minutes": minutes,
        "is_variant_of": KEYS[variant_of] if variant_of else None,
        "reference_solution": ref,
        "solution_source": "materials" if ref is not None else "generated",
        "solution_file": ref_file if ref is not None else None,
        "draft_solution": draft,
        "expected_answer_hint": hint,
        "status": "draft",
    }
    if optional:
        q["optional"] = True
    KEYS[key] = q["id"]
    QUESTIONS.append(q)


# ---------------------------------------------------------------- Excel Part 1
def nyc(key, n, prompt, skills, minutes, draft, headers, ref, hint, variant_of=None, task=None):
    add(key, "Excel", "Excel Part 1", NYC_DOC, task or f"Question {n}", ["nyc_film_permits_xlsx"], prompt, skills,
        minutes, draft, sheets=["NYC_Film_Permits"], headers=headers,
        ref=None if variant_of else ref, ref_file=NYC_SOL, hint=hint, variant_of=variant_of)


SP = "Consider only rows with EventType 'Shooting Permit'. "
nyc("nyc1", 1, "Open the NYC film permits data. How many records (data rows, not counting the header) does it have?",
    ["import", "count"], 1, "=COUNTA(A:A)-1, or the row number of the last row minus 1.", ["EventID"], 33502,
    "A whole number.")
nyc("nyc2", 2, "How many columns does the NYC film permits table have?", ["import", "count"], 0.5,
    "=COUNTA(1:1) on the header row.", NYC_HEAD, 14, "A whole number.")
nyc("nyc3", 3, "How many records have a missing ZipCode?", ["conditional count", "data cleaning"], 1,
    "=COUNTBLANK(N2:N33503)", ["ZipCode"], 11, "A whole number.")
nyc("nyc4", 4, "How many records have an invalid ZipCode, meaning a value that is present but is not five digits long?",
    ["conditional count", "text functions", "data cleaning"], 2,
    '=SUMPRODUCT((N2:N33503<>"")*(LEN(N2:N33503)<>5))', ["ZipCode"], 2, "A whole number.")
nyc("nyc5", 5, "Which column has the same value in every record? Give the exact column name.",
    ["data profiling", "distinct values"], 2,
    "For each column, =COUNTA(UNIQUE(range)); the column where the result is 1.", NYC_HEAD, "EventAgency",
    "A column name.")
nyc("nyc6", 6, "What is the oldest EnteredOn value? Give the full date and time.", ["date arithmetic", "min max"], 1,
    "=MIN(E2:E33503), formatted as date and time.", ["EnteredOn"], "2011-12-07 16:38:00", "A date and time.")
nyc("nyc7", 7, "What is the newest EnteredOn value? Give the full date and time.", ["date arithmetic", "min max"], 1,
    "=MAX(E2:E33503), formatted as date and time.", ["EnteredOn"], "2018-02-09 12:46:00", "A date and time.")
nyc("nyc8", 8, "How many different event types are there?", ["distinct values", "pivot"], 1,
    "=COUNTA(UNIQUE(B2:B33503)), or a pivot table with EventType in rows.", ["EventType"], 4, "A whole number.")
nyc("nyc9", 9, "What is the most common event type?", ["pivot", "conditional count"], 1,
    "Pivot table: EventType in rows, count of EventID in values, sort descending.", ["EventType"],
    "Shooting Permit", "An event type.")
nyc("nyc10", 10, SP + "What is the most common Category?", ["filter", "pivot"], 1.5,
    "Pivot table filtered on EventType = Shooting Permit, Category in rows, count in values, sort descending.",
    ["EventType", "Category"], "Television", "A category name.")
nyc("nyc11", 11, SP + "How many shooting permits were granted for student films (Category 'Student')?",
    ["conditional count"], 1, '=COUNTIFS(B:B,"Shooting Permit",K:K,"Student")', ["EventType", "Category"], 193,
    "A whole number.")
nyc("nyc11v1", 11, SP + "How many shooting permits were granted in the Category 'Documentary'?",
    ["conditional count"], 1, '=COUNTIFS(B:B,"Shooting Permit",K:K,"Documentary")', ["EventType", "Category"], None,
    "A whole number.", variant_of="nyc11")
nyc("nyc11v2", 11, SP + "How many shooting permits were granted in the Category 'Music Video'?",
    ["conditional count"], 1, '=COUNTIFS(B:B,"Shooting Permit",K:K,"Music Video")', ["EventType", "Category"], None,
    "A whole number.", variant_of="nyc11")
nyc("nyc12", 12, SP + "What percentage of shooting permits needed approval by more than one Community Board "
                      "(the CommunityBoard(s) field lists more than one board)?",
    ["conditional count", "text functions"], 2,
    '=COUNTIFS(B:B,"Shooting Permit",I:I,"*,*")/COUNTIF(B:B,"Shooting Permit")', ["EventType", "CommunityBoard(s)"],
    0.0784, "A percentage.")
nyc("nyc13", 13, SP + "In which year did the number of shoots in Brooklyn exceed the number in Manhattan? Use the "
                      "year of StartDateTime.",
    ["pivot", "date arithmetic"], 2,
    "Add a column =YEAR(C2). Pivot: year in rows, Borough in columns, count in values, filtered on Shooting Permit. "
    "Compare the Brooklyn and Manhattan columns.", ["EventType", "StartDateTime", "Borough"], 2017, "A year.")
nyc("nyc14", 14, SP + "What percentage of shoots in Manhattan take place on or near Broadway (ParkingHeld mentions "
                      "BROADWAY)? Round to the nearest percent.",
    ["conditional count", "text functions"], 2,
    '=COUNTIFS(B:B,"Shooting Permit",H:H,"Manhattan",G:G,"*BROADWAY*")/COUNTIFS(B:B,"Shooting Permit",H:H,"Manhattan")',
    ["EventType", "Borough", "ParkingHeld"], 0.2, "A percentage.")
nyc("nyc14v1", 14, SP + "What percentage of shoots in Brooklyn take place on or near Broadway (ParkingHeld mentions "
                        "BROADWAY)? Round to the nearest percent.",
    ["conditional count", "text functions"], 2,
    '=COUNTIFS(B:B,"Shooting Permit",H:H,"Brooklyn",G:G,"*BROADWAY*")/COUNTIFS(B:B,"Shooting Permit",H:H,"Brooklyn")',
    ["EventType", "Borough", "ParkingHeld"], None, "A percentage.", variant_of="nyc14")
nyc("nyc15", 15, SP + "How many shooting permit applications entered on or after 01.01.2013 came from a country other "
                      "than the United States of America?",
    ["conditional count", "date arithmetic"], 2,
    '=COUNTIFS(B:B,"Shooting Permit",E:E,">="&DATE(2013,1,1),M:M,"<>United States of America")',
    ["EventType", "EnteredOn", "Country"], 7, "A whole number.")
nyc("nyc15v1", 15, SP + "How many shooting permit applications entered on or after 01.01.2016 came from a country "
                        "other than the United States of America?",
    ["conditional count", "date arithmetic"], 2,
    '=COUNTIFS(B:B,"Shooting Permit",E:E,">="&DATE(2016,1,1),M:M,"<>United States of America")',
    ["EventType", "EnteredOn", "Country"], None, "A whole number.", variant_of="nyc15")
nyc("nyc16", 16, SP + "What is the average duration of a shooting permit (EndDateTime minus StartDateTime) in hours, "
                      "rounded to the nearest half hour?",
    ["date arithmetic", "average"], 2,
    "Add a column =(D2-C2)*24. Average it over Shooting Permit rows (AVERAGEIF), then =MROUND(x,0.5).",
    ["EventType", "StartDateTime", "EndDateTime"], 17, "A number of hours.")
nyc("nyc17", 17, SP + "What was the duration of the shortest shoot, in minutes?", ["date arithmetic", "min max"], 1.5,
    "Add a column =(D2-C2)*1440 and take MINIFS over Shooting Permit rows.",
    ["EventType", "StartDateTime", "EndDateTime"], 1, "A number of minutes.")
nyc("nyc18", 18, SP + "What is the average lead time in days between EnteredOn and StartDateTime? Round to the nearest "
                      "day.",
    ["date arithmetic", "average"], 2,
    "Add a column =C2-E2 (days). AVERAGEIF over Shooting Permit rows, then ROUND(x,0).",
    ["EventType", "StartDateTime", "EnteredOn"], 5, "A number of days.")
nyc("nyc19", 19, SP + "On which day of the week do shooting permits most often start? Give the full day name.",
    ["date arithmetic", "text functions", "pivot"], 2,
    'Add a column =TEXT(C2,"dddd"). Pivot on that column, count, sort descending.', ["EventType", "StartDateTime"],
    "Thursday", "A day name.")
nyc("nyc20", 20, SP + "What percentage of shooting permits include at least part of a Friday (any calendar day from "
                      "start to end is a Friday)? Round to two decimal places.",
    ["date arithmetic", "conditional count"], 3,
    "Per row: =IF(INT(D2)-INT(C2)>=6,1,--(SUMPRODUCT(--(WEEKDAY(ROW(INDIRECT(INT(C2)&\":\"&INT(D2))))=6))>0)). "
    "Average the flag over Shooting Permit rows.", ["EventType", "StartDateTime", "EndDateTime"], 0.2365,
    "A percentage.")
nyc("nyc20v1", 20, SP + "What percentage of shooting permits include at least part of a Saturday (any calendar day "
                        "from start to end is a Saturday)? Round to two decimal places.",
    ["date arithmetic", "conditional count"], 3,
    "Per row: =IF(INT(D2)-INT(C2)>=6,1,--(SUMPRODUCT(--(WEEKDAY(ROW(INDIRECT(INT(C2)&\":\"&INT(D2))))=7))>0)). "
    "Average the flag over Shooting Permit rows.", ["EventType", "StartDateTime", "EndDateTime"], None,
    "A percentage.", variant_of="nyc20")

# ---------------------------------------------------------------- Excel Part 2
C1_HEAD = ["Ticker", "Name", "Year", "Cash", "Accounts Receivables", "Inventories", "Total Current Assets",
           "Total Depreciation"]


def etl(key, task, ds, prompt, skills, minutes, draft, sheets=(), headers=(), hint=None, variant_of=None):
    add(key, "Excel", "Excel Part 2", ETL_DOC, task, [ds], prompt, skills, minutes, draft, sheets=sheets,
        headers=headers, hint=hint, variant_of=variant_of)


C1 = "Case 1, Required: identify and fix data problems"
etl("c1a", C1, "etl_case1", "Import the ETL Case 1 CSV with comma as delimiter. How many data rows end up with more "
                            "than 8 fields, and what in the data causes it?",
    ["import", "delimiter handling", "data cleaning"], 2,
    "Data > From Text/CSV, comma delimiter. Rows for Apple spill into a ninth column because the name 'Apple, Inc.' "
    "contains a comma and has no text qualifier.", headers=C1_HEAD, hint="A count and a cause.")
etl("c1b", C1, "etl_case1", "In the ETL Case 1 data, which column mixes plain numbers with values that carry a K or M "
                            "suffix? Write Apple's 2016 value in that column as a plain number in dollars.",
    ["data cleaning", "units of measurement"], 2,
    "Cash holds values such as '20500 M' and '900 K'. Convert with =VALUE(LEFT(D2,LEN(D2)-2))*1000000 for M "
    "(1000 for K).", headers=C1_HEAD, hint="A column name and a number.")
etl("c1c", C1, "etl_case1", "In the ETL Case 1 data, Total Depreciation shows negative numbers in two different ways. "
                            "Which two, and what is American Airlines' 2018 value as a plain number?",
    ["data cleaning", "text functions"], 2,
    "Some values use parentheses, e.g. (17400000000), others a minus sign. "
    "=IF(LEFT(H2)=\"(\",-VALUE(MID(H2,2,LEN(H2)-2)),VALUE(H2))", headers=C1_HEAD, hint="Two formats and a number.")
etl("c1d", C1, "etl_case1", "How many rows in the ETL Case 1 data are exact duplicates of an earlier row?",
    ["data cleaning", "duplicates"], 1.5,
    "Data > Remove Duplicates on all columns, or a helper column with COUNTIFS over all fields.", headers=C1_HEAD,
    hint="A whole number.")
etl("c1e", C1, "etl_case1", "How many rows in the ETL Case 1 data have no Ticker, and which company do they belong to?",
    ["data cleaning", "conditional count"], 1, '=COUNTBLANK(A2:A23), then filter on blank Ticker.', headers=C1_HEAD,
    hint="A count and a company name.")
etl("c1f", C1, "etl_case1", "One company's Ticker is written in three different ways in the ETL Case 1 data. Which "
                            "company, and which formula makes the tickers consistent?",
    ["data cleaning", "text functions"], 1.5, '=SUBSTITUTE(A2," ","") turns "A M Z N" and "AM ZN" into AMZN.',
    headers=C1_HEAD, hint="A company and a formula.")
etl("c1g", C1, "etl_case1", "After fixing the Apple rows, how many rows in the ETL Case 1 data have no usable "
                            "Inventories value (blank, only spaces, or a dash)?",
    ["data cleaning", "conditional count"], 2,
    '=SUMPRODUCT(--(TRIM(F2:F23)="")+--(TRIM(F2:F23)="-")) on the cleaned Inventories column.', headers=C1_HEAD,
    hint="A whole number.")

C2 = "Case 2, Required: extract fields from EmployeeCode"
C2S = ["Case 2"]
C2H = ["EmployeeCode", "FirstName", "LastName"]
etl("c2a", C2, "etl_case2", "In ETL Case 2, extract the Location (first three characters of EmployeeCode) with LEFT. "
                            "How many employees work in Germany (GER)?",
    ["text functions", "conditional count"], 1.5, '=LEFT(A2,3) in a helper column, then =COUNTIF(D:D,"GER").',
    C2S, C2H, "A whole number.")
etl("c2a1", C2, "etl_case2", "In ETL Case 2, extract the Location with LEFT. How many employees work in Japan (JAP)?",
    ["text functions", "conditional count"], 1.5, '=LEFT(A2,3), then =COUNTIF(D:D,"JAP").', C2S, C2H,
    "A whole number.", variant_of="c2a")
etl("c2a2", C2, "etl_case2", "In ETL Case 2, extract the Location with LEFT. How many employees work in the United "
                             "States (USA)?",
    ["text functions", "conditional count"], 1.5, '=LEFT(A2,3), then =COUNTIF(D:D,"USA").', C2S, C2H,
    "A whole number.", variant_of="c2a")
etl("c2b", C2, "etl_case2", "In ETL Case 2, extract EmpID (the four digits after the location code) with MID. What are "
                            "the smallest and largest EmpID?",
    ["text functions", "min max"], 1.5, "=VALUE(MID(A2,4,4)), then MIN and MAX of that column.", C2S, C2H,
    "Two whole numbers.")
etl("c2c", C2, "etl_case2", "In ETL Case 2, extract PlantID with MID and FIND (the digits after the hyphen) and build "
                            "LocationPlantID in the form USA-12. How many distinct LocationPlantID values are there?",
    ["text functions", "distinct values"], 2.5,
    '=MID(A2,FIND("-",A2)+1,2) for PlantID, =LEFT(A2,3)&"-"&PlantID, then =COUNTA(UNIQUE(range)).', C2S, C2H,
    "A whole number.")
etl("c2d", C2, "etl_case2", "In ETL Case 2, extract PayPeriod (last character of EmployeeCode) with RIGHT. How many "
                            "employees are paid weekly (W)?",
    ["text functions", "conditional count"], 1, '=RIGHT(A2,1), then =COUNTIF(G:G,"W").', C2S, C2H, "A whole number.")
etl("c2e", C2, "etl_case2", "In ETL Case 2, after building LocationPlantID (form USA-12), which LocationPlantID has the "
                            "most employees, and how many?",
    ["text functions", "pivot"], 2.5, "Build LocationPlantID, then a pivot with it in rows and count in values, "
                                      "sorted descending.", C2S, C2H, "An identifier and a count.")

C3 = "Case 3, Required: extract fields from messy EmployeeCode"
C3S = ["Case 3 data"]
etl("c3a", C3, "etl_case3", "In ETL Case 3, the Location is the letters before the first digit of EmployeeCode (codes "
                            "such as Canada, Japan, US vary in length). How many employees work in Canada?",
    ["text functions", "conditional count"], 2.5,
    'Position of first digit: =MIN(IFERROR(FIND({0,1,2,3,4,5,6,7,8,9},A2),99)); Location =LEFT(A2,pos-1); '
    'then =COUNTIF(range,"Canada").', C3S, C2H, "A whole number.")
etl("c3a1", C3, "etl_case3", "In ETL Case 3, extract the Location (letters before the first digit). How many employees "
                             "work in Japan?",
    ["text functions", "conditional count"], 2.5,
    'Same Location formula as for Canada, then =COUNTIF(range,"Japan").', C3S, C2H, "A whole number.",
    variant_of="c3a")
etl("c3b", C3, "etl_case3", "In ETL Case 3, PayPeriod is W or We for weekly and M or Mo for monthly. How many "
                            "employees are paid monthly?",
    ["text functions", "conditional count"], 2,
    'Pay code: =IF(ISNUMBER(VALUE(MID(A2,LEN(A2)-1,1))),RIGHT(A2,1),RIGHT(A2,2)); monthly if LEFT(code,1)="M".',
    C3S, C2H, "A whole number.")
etl("c3c", C3, "etl_case3", "In ETL Case 3, extract PlantID (the digits right after the hyphen). What is the highest "
                            "PlantID found?",
    ["text functions", "min max"], 2,
    'Take the text after the hyphen with MID(A2,FIND("-",A2)+1,9), keep the leading digits, VALUE it, then MAX.',
    C3S, C2H, "A whole number.")
etl("c3d", C3, "etl_case3", "In ETL Case 3, combine Location and PlantID into LocationPlantID (for example US-2). How "
                            "many distinct LocationPlantID values are there?",
    ["text functions", "distinct values"], 2.5, '=Location&"-"&PlantID, then =COUNTA(UNIQUE(range)).', C3S, C2H,
    "A whole number.")

C4 = "Case 4, Required: join the tabs into one flat file"
C4S = ["JELineItems"]
C4H = ["JENumber", "GLAccountNumber", "BusinessUnitID", "PreparerID", "SourceID", "EffectiveDate", "JEDescription",
       "Debit", "Credit", "Amount"]
etl("c4a", C4, "etl_case4", "In ETL Case 4, look up GLAccountName for a GLAccountNumber using INDEX/MATCH on the "
                            "ChartOfAccounts tab. What is the account name for GLAccountNumber 43440?",
    ["lookup"], 1, "=INDEX(ChartOfAccounts!A:A,MATCH(43440,ChartOfAccounts!B:B,0))",
    C4S + ["ChartOfAccounts"], C4H + ["GLAccountName"], "An account name.")
etl("c4b", C4, "etl_case4", "In ETL Case 4, add BusinessUnit to each journal line by lookup. What is the total of the "
                            "Debit column for the business unit HOTEL?",
    ["lookup", "conditional sum"], 2,
    '=INDEX(BusinessUnits!B:B,MATCH(C2,BusinessUnits!A:A,0)) for BusinessUnit, then =SUMIFS(H:H,K:K,"HOTEL").',
    C4S + ["BusinessUnits"], C4H + ["BusinessUnit"], "An amount.")
etl("c4b1", C4, "etl_case4", "In ETL Case 4, add BusinessUnit to each journal line by lookup. What is the total of the "
                             "Debit column for the business unit FOOD SERVICE?",
    ["lookup", "conditional sum"], 2,
    '=INDEX(BusinessUnits!B:B,MATCH(C2,BusinessUnits!A:A,0)), then =SUMIFS(H:H,K:K,"FOOD SERVICE").',
    C4S + ["BusinessUnits"], C4H + ["BusinessUnit"], "An amount.", variant_of="c4b")
etl("c4c", C4, "etl_case4", "In ETL Case 4, PreparerID is only unique together with BusinessUnitID. Which preparer "
                            "(name before the | sign on PreparerInfo) has PreparerID 102 in BusinessUnitID 2?",
    ["lookup", "text functions"], 2,
    "Two-key lookup: =INDEX(PreparerInfo!A:A,MATCH(1,(PreparerInfo!B:B=102)*(PreparerInfo!C:C=2),0)) as an array "
    'formula, then =LEFT(x,FIND("|",x)-1).', C4S + ["PreparerInfo"], C4H + ["PreparerName", "PreparerID",
                                                                              "BusinessUnitID"], "A person's name.")
etl("c4d", C4, "etl_case4", "In ETL Case 4, add Source to each journal line by lookup on SourceID. How many lines come "
                            "from the source PURCHASE CARD?",
    ["lookup", "conditional count"], 1.5,
    '=INDEX(Source!B:B,MATCH(E2,Source!A:A,0)), then =COUNTIF(range,"PURCHASE CARD").', C4S + ["Source"],
    C4H + ["SourceID", "Source"], "A whole number.")
etl("c4d1", C4, "etl_case4", "In ETL Case 4, add Source to each journal line by lookup on SourceID. How many lines come "
                             "from the source CHECK?",
    ["lookup", "conditional count"], 1.5, '=INDEX(Source!B:B,MATCH(E2,Source!A:A,0)), then =COUNTIF(range,"CHECK").',
    C4S + ["Source"], C4H + ["SourceID", "Source"], "A whole number.", variant_of="c4d")
etl("c4e", C4, "etl_case4", "In ETL Case 4, check that the journal balances: what is the sum of the Amount column on "
                            "JELineItems?",
    ["sum", "data validation"], 1, "=SUM(J2:J790); a balanced journal gives 0 (allow for rounding).", C4S, C4H,
    "An amount.")
etl("c4f", C4, "etl_case4", "In ETL Case 4, add AccountType to each journal line by lookup on GLAccountNumber. What is "
                            "the total Amount of lines whose AccountType is Revenue?",
    ["lookup", "conditional sum"], 2,
    '=INDEX(ChartOfAccounts!C:C,MATCH(B2,ChartOfAccounts!B:B,0)), then =SUMIFS(J:J,N:N,"Revenue").',
    C4S + ["ChartOfAccounts"], C4H + ["AccountType"], "An amount (revenue lines are credits, so negative).")

# ---------------------------------------------------------------- Excel Part 3
P15 = ["Pay_Date", "Payroll_ID", "Emp_No", "Home_Div", "Work_Div", "First_Name", "Last_Name", "Job", "Reg_Hrs",
       "OT_Hrs", "Reg_Pay", "OT_Pay", "Futa", "Suta", "Fica_Medc", "Work_Comp"]
P16 = ["Project", "Employee_ID", "Employee_Number", "Employee_Name", "Hours", "OT_Hours", "Gross_Wages",
       "SocSec_Medicare", "FUTA", "SUTA", "Work_Comp"]
IMP15 = "Import the 2015 payroll file (pipe-delimited, despite the .csv extension). "
IMP16 = "Import the 2016 payroll file (pipe-delimited, despite the .csv extension). "
JOBX = ('Job code = the three digits after the two-digit year and an optional H or S, e.g. '
        '=IF(ISNUMBER(VALUE(MID(H2,3,1))),MID(H2,3,3),MID(H2,4,3)). Keep it as text so 001 stays 001.')


def ic(key, task, ds, prompt, skills, minutes, draft, headers, hint, variant_of=None):
    add(key, "Excel", "Excel Part 3", IC_DOC, task, ds, prompt, skills, minutes, draft, headers=headers, hint=hint,
        variant_of=variant_of)


ic("ic1", "Part 2, load the data", ["ic_payroll2015_csv"], IMP15 + "How many data rows does it contain?",
   ["import", "delimiter handling", "count"], 1,
   "Data > From Text/CSV, delimiter |, or Text to Columns with Other: |. Count rows below the header.", P15,
   "A whole number.")
ic("ic2", "Part 2, load the data", ["ic_payroll2016_csv"], IMP16 + "How many data rows does it contain?",
   ["import", "delimiter handling", "count"], 1, "Import with delimiter |, then count rows below the header.", P16,
   "A whole number.")
ic("ic3", "Part 2, transform the data", ["ic_payroll2015_csv"],
   IMP15 + "Extract the three-digit job code from Job (14H002 gives 002). How many 2015 rows have job code 005?",
   ["import", "text functions", "conditional count"], 2, JOBX + ' Then =COUNTIF(Q:Q,"005").', P15, "A whole number.")
ic("ic4", "Appendix, jobcodes file: codes outside 001 to 012 are errors", ["ic_payroll2015_csv"],
   IMP15 + "After extracting the job code, which Job value gives a job code outside 001 to 012, and how many rows "
           "have it?", ["text functions", "data cleaning", "filter"], 2,
   JOBX + " Filter the job code column for values not in 001 to 012.", P15, "A Job value and a count.")
ic("ic5", "Part 3, Q1", ["ic_payroll2015_csv"],
   IMP15 + "What is the 2015 gross pay (Reg_Pay + OT_Pay) for job code 001? Round to two decimals.",
   ["import", "text functions", "conditional sum"], 2.5,
   JOBX + ' Gross pay column =K2+L2, then =ROUND(SUMIFS(R:R,Q:Q,"001"),2).', P15, "An amount.")
ic("ic5v1", "Part 3, Q1", ["ic_payroll2015_csv"],
   IMP15 + "What is the 2015 gross pay (Reg_Pay + OT_Pay) for job code 009? Round to two decimals.",
   ["import", "text functions", "conditional sum"], 2.5,
   JOBX + ' Gross pay column =K2+L2, then =ROUND(SUMIFS(R:R,Q:Q,"009"),2).', P15, "An amount.", variant_of="ic5")
ic("ic6", "Part 3, Q1", ["ic_payroll2016_csv"],
   IMP16 + "Extract the job code from Project. What are the 2016 Gross_Wages for job code 009? Round to two decimals.",
   ["import", "text functions", "conditional sum"], 2.5,
   JOBX.replace("H2", "A2") + ' Then =ROUND(SUMIFS(G:G,L:L,"009"),2).', P16, "An amount.")
ic("ic7", "Background and Part 3, Q1", ["ic_payroll2015_csv", "ic_payroll2016_csv"],
   "Import both payroll files (pipe-delimited). Total 2016 Gross_Wages minus total 2015 gross pay (Reg_Pay + OT_Pay): "
   "how big is the increase the CFO noticed? Round to two decimals.",
   ["import", "sum", "data cleaning"], 2,
   "=SUM('2016Data'!G:G)-(SUM('2015Data'!K:K)+SUM('2015Data'!L:L))", P15 + P16, "An amount.")
ic("ic8", "Part 3, Q1", ["ic_payroll2015_csv"],
   IMP15 + "What is the 2015 gross pay per hour for job code 005, using gross pay (Reg_Pay + OT_Pay) divided by total "
           "hours (Reg_Hrs + OT_Hrs)? Round to two decimals.",
   ["text functions", "conditional sum", "ratio"], 2.5,
   JOBX + ' =ROUND(SUMIFS(gross,Q:Q,"005")/(SUMIFS(I:I,Q:Q,"005")+SUMIFS(J:J,Q:Q,"005")),2)', P15, "An amount per hour.")
ic("ic9", "Part 4, Q1", ["ic_payroll2015_csv"],
   IMP15 + "Which employee earned the most overtime pay in the first six months of 2015? Give Emp_No, name and total "
           "OT_Pay.", ["pivot", "sort"], 2,
   "Pivot: Emp_No, First_Name, Last_Name in rows; sum of OT_Hrs and OT_Pay in values; filter OT_Hrs > 0; sort OT_Pay "
   "descending.", P15, "An employee and an amount.")
ic("ic10", "Part 4, Q2", ["ic_payroll2015_csv"],
   IMP15 + "Which job code had the most overtime pay in 2015, and how much was it?",
   ["text functions", "pivot", "sort"], 2.5,
   JOBX + " Pivot: job code in rows, sum of OT_Hrs and OT_Pay in values, sort OT_Pay descending.", P15,
   "A job code and an amount.")
ic("ic11", "Part 4, Q3", ["ic_payroll2016_csv"],
   IMP16 + "How many 2016 rows have no Employee_Number, and what is the total Gross_Wages of these 'phantom' rows?",
   ["import", "conditional count", "conditional sum", "data cleaning"], 2,
   '=COUNTBLANK(C2:C805) and =SUMIFS(G:G,C:C,"")', P16, "A count and an amount.")
ic("ic12", "Part 4, Q4", ["ic_payroll2015_csv"],
   IMP15 + "Treat all pay on the same Pay_Date as one pay period. How many employee and pay date combinations have "
           "overtime hours above 0 but fewer than 40 regular hours?",
   ["pivot", "filter", "group by"], 3,
   "Pivot: First_Name, Last_Name and Pay_Date in rows; sum of Reg_Hrs and OT_Hrs. Filter OT_Hrs > 0 and Reg_Hrs < 40, "
   "then count the rows.", P15, "A whole number.")
ic("ic13", "Part 4, Q5", ["ic_payroll2016_csv"],
   IMP16 + "What was the total employee cost in 2016: Gross_Wages + SocSec_Medicare + FUTA + SUTA + Work_Comp? Round to "
           "two decimals.", ["import", "sum"], 1.5, "=ROUND(SUM(G2:K805),2)", P16, "An amount.")
ic("ic14", "Part 4, Q6", ["ic_payroll2015_csv", "ic_locations"],
   IMP15 + "Also import the locations file (pipe-delimited). Join location to each 2015 row by employee name "
           "(First_Name & \" \" & Last_Name). What were the 2015 gross wages (Reg_Pay + OT_Pay) for location 1?",
   ["import", "lookup", "conditional sum"], 3,
   '=F2&" "&G2 for the name, =XLOOKUP(name,Location!A:A,Location!B:B) for location, then SUMIFS on gross pay.',
   P15 + ["Employee_Name", "Location"], "An amount.")
ic("ic14v1", "Part 4, Q6", ["ic_payroll2015_csv", "ic_locations"],
   IMP15 + "Also import the locations file (pipe-delimited). Join location to each 2015 row by employee name. What were "
           "the 2015 gross wages (Reg_Pay + OT_Pay) for location 2?",
   ["import", "lookup", "conditional sum"], 3,
   '=F2&" "&G2, =XLOOKUP(name,Location!A:A,Location!B:B), then SUMIFS on gross pay for location 2.',
   P15 + ["Employee_Name", "Location"], "An amount.", variant_of="ic14")
ic("ic15", "Part 4, Q6", ["ic_payroll2016_csv", "ic_locations"],
   IMP16 + "Also import the locations file. Excluding rows without an employee name, what is the 2016 average pay per "
           "hour (Gross_Wages divided by Hours + OT_Hours) at location 1? Round to two decimals.",
   ["import", "lookup", "conditional sum", "ratio"], 3,
   "=XLOOKUP(D2,Location!A:A,Location!B:B), then SUMIFS(G:G,loc,1)/(SUMIFS(E:E,loc,1)+SUMIFS(F:F,loc,1)).",
   P16 + ["Employee_Name", "Location"], "An amount per hour.")
ic("ic16", "Part 4, Q7", ["ic_payroll2016_csv"],
   IMP16 + "What percentage of Dale Hamilton's 2016 Gross_Wages falls in job code 001? Round to two decimals.",
   ["text functions", "pivot", "ratio"], 2.5,
   JOBX.replace("H2", "A2") + " Pivot: Employee_Name in rows, job code in columns, Gross_Wages shown as % of row total.",
   P16, "A percentage.")
ic("ic17", "Part 4, Q8", ["ic_payroll2015_csv"],
   IMP15 + "Group 2015 gross pay (Reg_Pay + OT_Pay) by month of Pay_Date. Which month has the highest gross pay, and "
           "how far above the six-month monthly average is it? Round to two decimals.",
   ["date arithmetic", "pivot", "average"], 3,
   "Add =MONTH(A2) and =K2+L2. Pivot month by sum of gross pay; subtract =AVERAGE of the six monthly totals.", P15,
   "A month and an amount.")
ic("ic18", "Part 4, Q10", ["ic_payroll2015_csv", "ic_payroll2016_csv"],
   "Import both payroll files (pipe-delimited). Apply each 2015 month's share of six-month gross pay (by month of Pay_Date) to the 2016 "
   "total Gross_Wages. What is the estimated 2016 gross pay for March? Round to two decimals.",
   ["date arithmetic", "pivot", "ratio"], 3,
   "Monthly 2015 gross pay / total 2015 gross pay gives the share; multiply the March share by SUM('2016Data'!G:G).",
   P15 + P16, "An amount.")
ic("ic19", "Part 3, Q2", ["ic_payroll2015_csv", "ic_payroll2016_csv"],
   "Import both payroll files (pipe-delimited) and extract the job code in each. How many employee and job code combinations have more "
   "than zero hours and more than zero wages in both 2015 and 2016? Match employees on Emp_No and Employee_Number.",
   ["text functions", "pivot", "lookup"], 3,
   "Pivot each year by employee number and job code (sum of hours and wages). Keep combinations with hours > 0 and "
   "wages > 0 in both years, matched with a lookup on a key =EmpNo&\"-\"&JobCode.", P15 + P16, "A whole number.")
ic("ic20", "Appendix, 2015 file: each pay date should have its own Payroll_ID", ["ic_payroll2015_csv"],
   IMP15 + "The appendix says each pay date should have one unique Payroll_ID. How many distinct Pay_Date values and "
           "how many distinct Payroll_ID values are there?",
   ["distinct values", "data validation"], 1.5, "=COUNTA(UNIQUE(A2:A4982)) and =COUNTA(UNIQUE(B2:B4982))", P15,
   "Two whole numbers.")

# ---------------------------------------------------------------- Excel Part 4 (ETL step of the restaurant case)
RS = ["salesData"]
RH = ["date", "LineItem", "netTotal"]


def rest(key, prompt, skills, minutes, draft, sheets, headers, hint, variant_of=None):
    add(key, "Excel", "Excel Part 4", REST_DOC, "ETL: merge the data from the 3 sheets", ["restaurant_data"], prompt,
        skills, minutes, draft, sheets=sheets, headers=headers, hint=hint, variant_of=variant_of)


rest("r1", "In the restaurant workbook, aggregate salesData netTotal by date. What were total net sales on 31.12.2018?",
     ["pivot", "conditional sum"], 1.5, '=SUMIFS(salesData!F:F,salesData!A:A,DATE(2018,12,31))', RS, RH, "An amount.")
rest("r1v1", "In the restaurant workbook, aggregate salesData netTotal by date. What were total net sales on "
             "08.01.2018?", ["pivot", "conditional sum"], 1.5,
     '=SUMIFS(salesData!F:F,salesData!A:A,DATE(2018,1,8))', RS, RH, "An amount.", variant_of="r1")
rest("r2", "salesData has one row per menu item per day and 15 menu items. How many distinct dates are there, and on "
           "how many of those dates are fewer than 15 items recorded?",
     ["pivot", "distinct values", "data validation"], 2,
     "Pivot: date in rows, count of LineItem in values; count dates, then count rows with value < 15.", RS, RH,
     "Two whole numbers.")
rest("r3", "Which date has the highest total net sales (sum of netTotal over all menu items), and what is the total?",
     ["pivot", "sort"], 1.5, "Pivot: date in rows, sum of netTotal, sort descending.", RS, RH,
     "A date and an amount.")
rest("r4", "Merge weatherData into daily sales by date. What was tmax on the date with the highest total net sales?",
     ["pivot", "lookup"], 2,
     "Pivot daily totals, then =XLOOKUP(date,weatherData!A:A,weatherData!D:D).", RS + ["weatherData"],
     RH + ["tmax"], "A temperature in Fahrenheit.")
rest("r5", "Merge gameData into daily sales by date; dates not in gameData get gameDay = 0. What is the average daily "
           "total net sales on game days?",
     ["lookup", "average", "pivot"], 2.5,
     "Daily totals by pivot; gameDay =IFERROR(XLOOKUP(date,gameData!A:A,gameData!E:E),0); then AVERAGEIFS.",
     RS + ["gameData"], RH + ["gameDay"], "An amount.")
rest("r5v1", "Merge gameData into daily sales by date; dates not in gameData get gameDay = 0. What is the average daily "
             "total net sales on days without a game?",
     ["lookup", "average", "pivot"], 2.5,
     "Daily totals by pivot; gameDay =IFERROR(XLOOKUP(date,gameData!A:A,gameData!E:E),0); then AVERAGEIFS with 0.",
     RS + ["gameData"], RH + ["gameDay"], "An amount.", variant_of="r5")
rest("r6", "How many dates in weatherData have no value for prcp? Why does that matter before running a regression?",
     ["data cleaning", "conditional count"], 1.5, "=COUNTBLANK(weatherData!B2:B366); blank rows drop out of a "
                                                  "regression or must be handled.", ["weatherData"], ["date", "prcp"],
     "A whole number and a reason.")

# ---------------------------------------------------------------- SQL Part 1 PWC (Chinook)


def pwc(key, n, prompt, skills, minutes, draft, tables, columns, ref=None, hint=None, variant_of=None, slide=None):
    add(key, "SQL", "SQL Part 1 PWC", PWC_DOC, f"Question {n}" + (f" (PWC.pptx exercise {slide})" if slide else ""),
        ["chinook"], prompt, skills, minutes, draft, tables=tables, columns=columns,
        ref=None if variant_of else ref, ref_file=PWC_SOL, hint=hint, variant_of=variant_of)


pwc("p1", 1, "How many columns does the Customer table have?", ["schema"], 0.5,
    "SELECT COUNT(*) AS columns FROM pragma_table_info('Customer');", ["Customer"], [], 13, "A whole number.", slide=1)
pwc("p2", 2, "Select only the first 5 rows of Customer (in CustomerId order). What is the Country in the last of them?",
    ["select", "limit"], 1, "SELECT Country FROM Customer ORDER BY CustomerId LIMIT 1 OFFSET 4;", ["Customer"],
    ["Customer.Country", "Customer.CustomerId"], "Czech Republic", "A country.", slide=1)
pwc("p3", 3, "Sort Customer by LastName. What is the LastName in the third row?", ["sort", "limit"], 1,
    "SELECT LastName FROM Customer ORDER BY LastName LIMIT 1 OFFSET 2;", ["Customer"], ["Customer.LastName"],
    "Bernard", "A last name.", slide=1)
pwc("p4", 4, "How many rows are in the Invoice table?", ["count"], 0.5, "SELECT COUNT(*) FROM Invoice;", ["Invoice"], [],
    412, "A whole number.", slide=1)
pwc("p5", 5, "How many invoices have a Total greater than $20?", ["filter", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE Total > 20;", ["Invoice"], ["Invoice.Total"], 4, "A whole number.", slide=2)
pwc("p5v1", 5, "How many invoices have a Total greater than $15?", ["filter", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE Total > 15;", ["Invoice"], ["Invoice.Total"], hint="A whole number.",
    variant_of="p5", slide=2)
pwc("p6", 6, "How many invoices have a Total greater than $10 and less than $20?", ["filter", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE Total > 10 AND Total < 20;", ["Invoice"], ["Invoice.Total"], 60,
    "A whole number.", slide=2)
pwc("p7", 7, "How many invoices are from customers in Brazil, Argentina or Chile? Use BillingCountry.",
    ["filter", "in", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE BillingCountry IN ('Brazil', 'Argentina', 'Chile');", ["Invoice"],
    ["Invoice.BillingCountry"], 49, "A whole number.", slide=2)
pwc("p7v1", 7, "How many invoices are from customers in Germany, France or Spain? Use BillingCountry.",
    ["filter", "in", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE BillingCountry IN ('Germany', 'France', 'Spain');", ["Invoice"],
    ["Invoice.BillingCountry"], hint="A whole number.", variant_of="p7", slide=2)
pwc("p8", 8, "How many invoices have a BillingCountry that starts with C?", ["filter", "like", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE BillingCountry LIKE 'C%';", ["Invoice"], ["Invoice.BillingCountry"], 77,
    "A whole number.", slide=2)
pwc("p8v1", 8, "How many invoices have a BillingCountry that starts with U?", ["filter", "like", "count"], 1,
    "SELECT COUNT(*) FROM Invoice WHERE BillingCountry LIKE 'U%';", ["Invoice"], ["Invoice.BillingCountry"],
    hint="A whole number.", variant_of="p8", slide=2)
pwc("p9", 9, "How many customers list their company (Company is not NULL)?", ["null handling", "count"], 1,
    "SELECT COUNT(*) FROM Customer WHERE Company IS NOT NULL;", ["Customer"], ["Customer.Company"], 10,
    "A whole number.", slide=2)
pwc("p10", 10, "How many employees does Chinook have?", ["count"], 0.5, "SELECT COUNT(*) FROM Employee;", ["Employee"],
    [], 8, "A whole number.", slide=3)
pwc("p11", 11, "Show each employee's name with a new column holding their Phone number without the country and area "
               "code (Phone looks like +1 (403) 262-3443).", ["text functions", "derived column"], 2,
    "SELECT FirstName, LastName, Phone, SUBSTR(Phone, INSTR(Phone, ')') + 2) AS PhoneNoArea FROM Employee;",
    ["Employee"], ["Employee.Phone", "Employee.FirstName", "Employee.LastName"], hint="A table, one row per employee.",
    slide=3)
pwc("p12", 12, "How long is the longest employee LastName, in characters?", ["text functions", "min max"], 1,
    "SELECT MAX(LENGTH(LastName)) FROM Employee;", ["Employee"], ["Employee.LastName"], 8, "A whole number.", slide=3)
pwc("p13", 13, "How many employees were born on a Sunday?", ["date functions", "filter", "count"], 1.5,
    "SELECT COUNT(*) FROM Employee WHERE STRFTIME('%w', BirthDate) = '0';", ["Employee"], ["Employee.BirthDate"], 2,
    "A whole number.", slide=3)
pwc("p13v1", 13, "How many employees were born on a Monday?", ["date functions", "filter", "count"], 1.5,
    "SELECT COUNT(*) FROM Employee WHERE STRFTIME('%w', BirthDate) = '1';", ["Employee"], ["Employee.BirthDate"],
    hint="A whole number.", variant_of="p13", slide=3)
pwc("p14", 14, "How old was the oldest employee at the time they were hired, in years?", ["date functions", "min max"],
    2, "SELECT ROUND(MAX((JULIANDAY(HireDate) - JULIANDAY(BirthDate)) / 365.25), 1) AS AgeAtHire FROM Employee;",
    ["Employee"], ["Employee.HireDate", "Employee.BirthDate"], "Approximately 55.5 years", "A number of years.",
    slide=3)
pwc("p15", 15, "List countries by the total value of their invoices, highest first. Use BillingCountry.",
    ["group by", "sum", "sort"], 1.5,
    "SELECT BillingCountry, ROUND(SUM(Total), 2) AS TotalValue FROM Invoice GROUP BY BillingCountry "
    "ORDER BY TotalValue DESC;", ["Invoice"], ["Invoice.BillingCountry", "Invoice.Total"],
    hint="A table of countries and totals.", slide=4)
pwc("p16", 16, "How many invoice line items are there?", ["count"], 0.5, "SELECT COUNT(*) FROM InvoiceLine;",
    ["InvoiceLine"], [], 2240, "A whole number.", slide=4)
pwc("p17", 17, "How many distinct unit prices appear on invoice lines?", ["distinct values", "count"], 1,
    "SELECT COUNT(DISTINCT UnitPrice) FROM InvoiceLine;", ["InvoiceLine"], ["InvoiceLine.UnitPrice"], 2,
    "A whole number.", slide=4)
pwc("p18", 18, "How many downloads (invoice lines) have there been at each unit price?", ["group by", "count"], 1,
    "SELECT UnitPrice, COUNT(*) AS Downloads FROM InvoiceLine GROUP BY UnitPrice ORDER BY UnitPrice;",
    ["InvoiceLine"], ["InvoiceLine.UnitPrice"], hint="A small table: price and count.", slide=4)
pwc("p19", 19, "What is the highest number of times any single track has been downloaded, and how many tracks reach "
               "that number?", ["group by", "subquery", "count"], 2.5,
    "SELECT Times, COUNT(*) AS Tracks FROM (SELECT TrackId, COUNT(*) AS Times FROM InvoiceLine GROUP BY TrackId) "
    "WHERE Times = (SELECT MAX(c) FROM (SELECT COUNT(*) AS c FROM InvoiceLine GROUP BY TrackId)) GROUP BY Times;",
    ["InvoiceLine"], ["InvoiceLine.TrackId"], "256 tracks have been downloaded twice", "Two whole numbers.", slide=4)
pwc("p20", 20, "What range of invoice dates does the database cover? Give the first date, the last date and the span "
               "in years.", ["date functions", "min max"], 1.5,
    "SELECT MIN(InvoiceDate) AS FirstDate, MAX(InvoiceDate) AS LastDate, "
    "ROUND((JULIANDAY(MAX(InvoiceDate)) - JULIANDAY(MIN(InvoiceDate))) / 365.25, 1) AS Years FROM Invoice;",
    ["Invoice"], ["Invoice.InvoiceDate"], "Approximately 5 years", "Two dates and a number of years.", slide=4)
pwc("p21", 21, "Return the top five most downloaded tracks with the full track name and the number of downloads. Break "
               "ties by TrackId.", ["join", "group by", "sort", "limit"], 2.5,
    "SELECT t.Name, COUNT(*) AS Downloads FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId "
    "GROUP BY t.TrackId, t.Name ORDER BY Downloads DESC, t.TrackId LIMIT 5;", ["InvoiceLine", "Track"],
    ["InvoiceLine.TrackId", "Track.TrackId", "Track.Name"], "256 tracks have been downloaded twice",
    "Five rows: track name and count.", slide=5)
pwc("p22", 22, "Count an album as downloaded when all of its tracks appear on one invoice. How many distinct albums "
               "have been downloaded?", ["join", "group by", "subquery"], 3,
    "WITH album_size AS (SELECT AlbumId, COUNT(*) AS n FROM Track GROUP BY AlbumId), "
    "per_invoice AS (SELECT il.InvoiceId, t.AlbumId, COUNT(DISTINCT il.TrackId) AS n FROM InvoiceLine il "
    "JOIN Track t ON t.TrackId = il.TrackId GROUP BY il.InvoiceId, t.AlbumId) "
    "SELECT COUNT(DISTINCT p.AlbumId) FROM per_invoice p JOIN album_size a ON a.AlbumId = p.AlbumId WHERE p.n = a.n;",
    ["InvoiceLine", "Track"], ["InvoiceLine.InvoiceId", "InvoiceLine.TrackId", "Track.AlbumId"],
    "Assuming an album is downloaded when all of its tracks were present on a single invoice: 49", "A whole number.",
    slide=5)
pwc("p23", 23, "What is the most popular genre, measured by number of invoice lines (downloads)?",
    ["join", "group by", "sort"], 2,
    "SELECT g.Name, COUNT(*) AS Downloads FROM InvoiceLine il JOIN Track t ON t.TrackId = il.TrackId "
    "JOIN Genre g ON g.GenreId = t.GenreId GROUP BY g.GenreId, g.Name ORDER BY Downloads DESC LIMIT 1;",
    ["InvoiceLine", "Track", "Genre"], ["Track.GenreId", "Genre.GenreId", "Genre.Name"], "Rock", "A genre.", slide=5)

# ---------------------------------------------------------------- SQL Part 1 CS50


def mov(key, n, prompt, skills, minutes, draft, tables, columns, hint, variant_of=None):
    add(key, "SQL", "SQL Part 1 CS50", MOV_DOC, f"movies {n}.sql", ["cs50_movies"], prompt, skills, minutes, draft,
        tables=tables, columns=columns, hint=hint, variant_of=variant_of)


mov("m1", 1, "List the titles of all movies released in 2007.", ["select", "filter"], 0.5,
    "SELECT title FROM movies WHERE year = 2007;", ["movies"], ["movies.title", "movies.year"], "One column: title.")
mov("m1v1", 1, "List the titles of all movies released in 2010.", ["select", "filter"], 0.5,
    "SELECT title FROM movies WHERE year = 2010;", ["movies"], ["movies.title", "movies.year"], "One column: title.",
    variant_of="m1")
mov("m2", 2, "What is Johnny Depp's birth year? Assume only one person has that name.", ["select", "filter"], 0.5,
    "SELECT birth FROM people WHERE name = 'Johnny Depp';", ["people"], ["people.name", "people.birth"],
    "One value: a year.")
mov("m3", 3, "List the titles of all movies released in 2017 or later, in alphabetical order.",
    ["filter", "sort"], 1, "SELECT title FROM movies WHERE year >= 2017 ORDER BY title;", ["movies"],
    ["movies.title", "movies.year"], "One column: title, sorted.")
mov("m4", 4, "How many movies have an IMDb rating greater than 9.0?", ["filter", "count"], 0.5,
    "SELECT COUNT(*) FROM ratings WHERE rating > 9.0;", ["ratings"], ["ratings.rating"], "One whole number.")
mov("m4v1", 4, "How many movies have an IMDb rating greater than 9.5?", ["filter", "count"], 0.5,
    "SELECT COUNT(*) FROM ratings WHERE rating > 9.5;", ["ratings"], ["ratings.rating"], "One whole number.",
    variant_of="m4")
mov("m5", 5, "List the titles and release years of all Toy Story movies (titles starting with 'Toy Story'), oldest "
             "first.", ["filter", "like", "sort"], 1,
    "SELECT title, year FROM movies WHERE title LIKE 'Toy Story%' ORDER BY year;", ["movies"],
    ["movies.title", "movies.year"], "Two columns: title and year.")
mov("m5v1", 5, "List the titles and release years of all movies whose title starts with 'Harry Potter', oldest first.",
    ["filter", "like", "sort"], 1, "SELECT title, year FROM movies WHERE title LIKE 'Harry Potter%' ORDER BY year;",
    ["movies"], ["movies.title", "movies.year"], "Two columns: title and year.", variant_of="m5")
mov("m6", 6, "What is the average rating of all movies released in 2013?", ["join", "average"], 1,
    "SELECT AVG(rating) FROM ratings JOIN movies ON movies.id = ratings.movie_id WHERE year = 2013;",
    ["movies", "ratings"], ["movies.id", "movies.year", "ratings.movie_id", "ratings.rating"], "One number.")
mov("m6v1", 6, "What is the average rating of all movies released in 2012?", ["join", "average"], 1,
    "SELECT AVG(rating) FROM ratings JOIN movies ON movies.id = ratings.movie_id WHERE year = 2012;",
    ["movies", "ratings"], ["movies.id", "movies.year", "ratings.movie_id", "ratings.rating"], "One number.",
    variant_of="m6")
mov("m7", 7, "List all movies released in 2011 with their ratings, highest rating first; ties in alphabetical order "
             "of title. Leave out movies without a rating.", ["join", "sort"], 1.5,
    "SELECT title, rating FROM movies JOIN ratings ON movies.id = ratings.movie_id WHERE year = 2011 "
    "ORDER BY rating DESC, title;", ["movies", "ratings"],
    ["movies.id", "movies.title", "movies.year", "ratings.movie_id", "ratings.rating"], "Two columns: title, rating.")
mov("m8", 8, "List the names of all people who starred in Harry Potter and the Sorcerer's Stone.", ["join"], 1.5,
    "SELECT name FROM people JOIN stars ON people.id = stars.person_id JOIN movies ON movies.id = stars.movie_id "
    "WHERE title = 'Harry Potter and the Sorcerer''s Stone';", ["people", "stars", "movies"],
    ["people.id", "people.name", "stars.person_id", "stars.movie_id", "movies.id", "movies.title"],
    "One column: name.")
mov("m9", 9, "List the names of all people who starred in a movie released in 2003, ordered by birth year. Each person "
             "only once.", ["subquery", "sort", "distinct values"], 2,
    "SELECT name FROM people WHERE id IN (SELECT person_id FROM stars JOIN movies ON movies.id = stars.movie_id "
    "WHERE year = 2003) ORDER BY birth;", ["people", "stars", "movies"],
    ["people.id", "people.name", "people.birth", "stars.person_id", "stars.movie_id", "movies.year"],
    "One column: name.")
mov("m10", 10, "List the names of all people who directed a movie with a rating of at least 8.0. Each person only "
               "once.", ["subquery", "join", "distinct values"], 2,
    "SELECT name FROM people WHERE id IN (SELECT person_id FROM directors JOIN ratings ON "
    "directors.movie_id = ratings.movie_id WHERE rating >= 8.0);", ["people", "directors", "ratings"],
    ["people.id", "people.name", "directors.person_id", "directors.movie_id", "ratings.movie_id", "ratings.rating"],
    "One column: name.")
mov("m11", 11, "List the titles of the five highest rated movies that Helena Bonham Carter starred in, highest first; ties in alphabetical order of title.",
    ["join", "sort", "limit"], 2,
    "SELECT title FROM movies JOIN stars ON movies.id = stars.movie_id JOIN people ON people.id = stars.person_id "
    "JOIN ratings ON movies.id = ratings.movie_id WHERE name = 'Helena Bonham Carter' ORDER BY rating DESC, title LIMIT 5;",
    ["movies", "stars", "people", "ratings"],
    ["movies.id", "movies.title", "stars.movie_id", "stars.person_id", "people.id", "people.name", "ratings.rating"],
    "One column: title, five rows.")
mov("m12", 12, "List the titles of all movies in which both Johnny Depp and Helena Bonham Carter starred.",
    ["subquery", "join"], 2.5,
    "SELECT title FROM movies WHERE id IN (SELECT movie_id FROM stars WHERE person_id = "
    "(SELECT id FROM people WHERE name = 'Johnny Depp')) AND id IN (SELECT movie_id FROM stars WHERE person_id = "
    "(SELECT id FROM people WHERE name = 'Helena Bonham Carter'));", ["movies", "stars", "people"],
    ["movies.id", "movies.title", "stars.movie_id", "stars.person_id", "people.id", "people.name"],
    "One column: title.")
mov("m13", 13, "List the names of all people who starred in a movie with Kevin Bacon (the one born in 1958). Leave "
               "Kevin Bacon himself out.", ["subquery", "join"], 3,
    "SELECT name FROM people WHERE id IN (SELECT person_id FROM stars WHERE movie_id IN (SELECT movie_id FROM stars "
    "WHERE person_id = (SELECT id FROM people WHERE name = 'Kevin Bacon' AND birth = 1958))) AND id <> "
    "(SELECT id FROM people WHERE name = 'Kevin Bacon' AND birth = 1958);", ["people", "stars"],
    ["people.id", "people.name", "people.birth", "stars.movie_id", "stars.person_id"], "One column: name.")


def song(key, n, prompt, skills, minutes, draft, tables, columns, hint, variant_of=None):
    add(key, "SQL", "SQL Part 1 CS50", SONG_DOC, f"songs {n}.sql", ["cs50_songs"], prompt, skills, minutes, draft,
        tables=tables, columns=columns, hint=hint, variant_of=variant_of)


song("s1", 1, "List the name and energy of every song.", ["select"], 0.5, "SELECT name, energy FROM songs;", ["songs"],
     ["songs.name", "songs.energy"], "Two columns: name, energy.")
song("s2", 2, "List the names of all songs in decreasing order of tempo.", ["sort"], 0.5,
     "SELECT name FROM songs ORDER BY tempo DESC;", ["songs"], ["songs.name", "songs.tempo"], "One column: name.")
song("s3", 3, "List the names of the three longest songs, longest first.", ["sort", "limit"], 1,
     "SELECT name FROM songs ORDER BY duration_ms DESC LIMIT 3;", ["songs"], ["songs.name", "songs.duration_ms"],
     "One column: name, three rows.")
song("s4", 4, "List the names of songs with danceability, energy and valence all greater than 0.6.",
     ["filter", "and or"], 1,
     "SELECT name FROM songs WHERE danceability > 0.6 AND energy > 0.6 AND valence > 0.6;", ["songs"],
     ["songs.name", "songs.danceability", "songs.energy", "songs.valence"], "One column: name.")
song("s5", 5, "What is the average tempo of all songs?", ["average"], 0.5, "SELECT AVG(tempo) FROM songs;", ["songs"],
     ["songs.tempo"], "One number.")
song("s6", 6, "List the names of songs by Drake, without assuming Drake's artist_id.", ["subquery"], 1,
     "SELECT name FROM songs WHERE artist_id = (SELECT id FROM artists WHERE name = 'Drake');", ["songs", "artists"],
     ["songs.name", "songs.artist_id", "artists.id", "artists.name"], "One column: name.")
song("s6v1", 6, "List the names of songs by Ed Sheeran, without assuming his artist_id.", ["subquery"], 1,
     "SELECT name FROM songs WHERE artist_id = (SELECT id FROM artists WHERE name = 'Ed Sheeran');",
     ["songs", "artists"], ["songs.name", "songs.artist_id", "artists.id", "artists.name"], "One column: name.",
     variant_of="s6")
song("s7", 7, "What is the average energy of songs by Post Malone, without assuming his artist_id?",
     ["subquery", "average"], 1,
     "SELECT AVG(energy) FROM songs WHERE artist_id = (SELECT id FROM artists WHERE name = 'Post Malone');",
     ["songs", "artists"], ["songs.energy", "songs.artist_id", "artists.id", "artists.name"], "One number.")
song("s7v1", 7, "What is the average energy of songs by XXXTENTACION, without assuming the artist_id?",
     ["subquery", "average"], 1,
     "SELECT AVG(energy) FROM songs WHERE artist_id = (SELECT id FROM artists WHERE name = 'XXXTENTACION');",
     ["songs", "artists"], ["songs.energy", "songs.artist_id", "artists.id", "artists.name"], "One number.",
     variant_of="s7")
song("s8", 8, "List the names of songs that feature other artists (the name contains 'feat.').", ["like"], 0.5,
     "SELECT name FROM songs WHERE name LIKE '%feat.%';", ["songs"], ["songs.name"], "One column: name.")


def fifty(key, task, prompt, skills, minutes, draft, tables, columns, hint):
    add(key, "SQL", "SQL Part 1 CS50", FIFTY_DOC, task, ["cs50_fiftyville"], prompt, skills, minutes, draft,
        tables=tables, columns=columns, hint=hint, optional=True)


fifty("f1", "Mystery, step 1 (hint: start with crime_scene_reports)",
      "Optional (Fiftyville). Find the crime scene report for 28.07.2020 on Chamberlin Street. What does it say?",
      ["filter"], 1,
      "SELECT description FROM crime_scene_reports WHERE year = 2020 AND month = 7 AND day = 28 "
      "AND street = 'Chamberlin Street';", ["crime_scene_reports"],
      ["crime_scene_reports.year", "crime_scene_reports.month", "crime_scene_reports.day",
       "crime_scene_reports.street", "crime_scene_reports.description"], "One text value.")
fifty("f2", "Mystery, step 2",
      "Optional (Fiftyville). List the names and transcripts of interviews from 28.07.2020 that mention the courthouse.",
      ["filter", "like"], 1,
      "SELECT name, transcript FROM interviews WHERE year = 2020 AND month = 7 AND day = 28 "
      "AND transcript LIKE '%courthouse%';", ["interviews"],
      ["interviews.name", "interviews.transcript", "interviews.year", "interviews.month", "interviews.day"],
      "Two columns: name, transcript.")
fifty("f3", "Mystery, step 3",
      "Optional (Fiftyville). Which people own a car that exited the courthouse car park on 28.07.2020 between 10:15 and "
      "10:25?", ["join", "filter"], 2,
      "SELECT DISTINCT p.name FROM courthouse_security_logs c JOIN people p ON p.license_plate = c.license_plate "
      "WHERE c.year = 2020 AND c.month = 7 AND c.day = 28 AND c.hour = 10 AND c.minute BETWEEN 15 AND 25 "
      "AND c.activity = 'exit' ORDER BY p.name;", ["courthouse_security_logs", "people"],
      ["courthouse_security_logs.license_plate", "courthouse_security_logs.activity", "courthouse_security_logs.hour",
       "courthouse_security_logs.minute", "people.license_plate", "people.name"], "One column: name.")
fifty("f4", "Mystery, step 4",
      "Optional (Fiftyville). Which city does the earliest flight out of Fiftyville on 29.07.2020 go to?",
      ["join", "sort", "limit"], 2,
      "SELECT a2.city FROM flights f JOIN airports a1 ON a1.id = f.origin_airport_id JOIN airports a2 "
      "ON a2.id = f.destination_airport_id WHERE a1.city = 'Fiftyville' AND f.year = 2020 AND f.month = 7 "
      "AND f.day = 29 ORDER BY f.hour, f.minute LIMIT 1;", ["flights", "airports"],
      ["flights.origin_airport_id", "flights.destination_airport_id", "flights.hour", "flights.minute",
       "airports.id", "airports.city"], "A city.")
FIFTY_THIEF = (
    "WITH cars AS (SELECT p.id FROM courthouse_security_logs c JOIN people p ON p.license_plate = c.license_plate "
    "WHERE c.year = 2020 AND c.month = 7 AND c.day = 28 AND c.hour = 10 AND c.minute BETWEEN 15 AND 25 "
    "AND c.activity = 'exit'), "
    "atm AS (SELECT b.person_id AS id FROM atm_transactions t JOIN bank_accounts b ON b.account_number = t.account_number "
    "WHERE t.year = 2020 AND t.month = 7 AND t.day = 28 AND t.atm_location = 'Fifer Street' "
    "AND t.transaction_type = 'withdraw'), "
    "calls AS (SELECT p.id FROM phone_calls pc JOIN people p ON p.phone_number = pc.caller "
    "WHERE pc.year = 2020 AND pc.month = 7 AND pc.day = 28 AND pc.duration < 60), "
    "flight AS (SELECT f.id FROM flights f JOIN airports a ON a.id = f.origin_airport_id WHERE a.city = 'Fiftyville' "
    "AND f.year = 2020 AND f.month = 7 AND f.day = 29 ORDER BY f.hour, f.minute LIMIT 1), "
    "pax AS (SELECT p.id FROM passengers ps JOIN people p ON p.passport_number = ps.passport_number "
    "WHERE ps.flight_id = (SELECT id FROM flight)) ")
fifty("f5", "Mystery: who the thief is",
      "Optional (Fiftyville). Combine the clues: left the courthouse car park 10:15 to 10:25, withdrew cash at the ATM "
      "on Fifer Street that morning, made a call under a minute that day, and took the earliest flight out on "
      "29.07.2020. Who is the thief?", ["subquery", "join", "intersect"], 3,
      FIFTY_THIEF + "SELECT name FROM people WHERE id IN (SELECT id FROM cars) AND id IN (SELECT id FROM atm) "
                    "AND id IN (SELECT id FROM calls) AND id IN (SELECT id FROM pax);",
      ["courthouse_security_logs", "people", "atm_transactions", "bank_accounts", "phone_calls", "flights",
       "airports", "passengers"],
      ["atm_transactions.atm_location", "atm_transactions.transaction_type", "bank_accounts.person_id",
       "phone_calls.caller", "phone_calls.duration", "passengers.passport_number", "passengers.flight_id"],
      "One name.")
fifty("f6", "Mystery: who the accomplice is",
      "Optional (Fiftyville). The thief called the accomplice for less than a minute on 28.07.2020. Who received that "
      "call?", ["subquery", "join"], 3,
      FIFTY_THIEF + ", thief AS (SELECT id, phone_number FROM people WHERE id IN (SELECT id FROM cars) "
                    "AND id IN (SELECT id FROM atm) AND id IN (SELECT id FROM calls) AND id IN (SELECT id FROM pax)) "
                    "SELECT p.name FROM phone_calls pc JOIN people p ON p.phone_number = pc.receiver "
                    "WHERE pc.caller = (SELECT phone_number FROM thief) AND pc.year = 2020 AND pc.month = 7 "
                    "AND pc.day = 28 AND pc.duration < 60;",
      ["phone_calls", "people"], ["phone_calls.caller", "phone_calls.receiver", "phone_calls.duration"], "One name.")

# ---------------------------------------------------------------- SQL Part 2 P-card
# Master query, as the case suggests: OSU only, non-null TransactionDate, parsed date parts and a combined name.
# Dates are text 'M/D/YYYY 0:00:00', so the parts are cut out with INSTR/SUBSTR.
PC = (
    "WITH t AS (SELECT p.*, SUBSTR(TransactionDate, INSTR(TransactionDate, '/') + 1) AS tr, "
    "SUBSTR(PostedDate, INSTR(PostedDate, '/') + 1) AS pr FROM pcards p "
    "WHERE AgencyName = 'OKLAHOMA STATE UNIVERSITY' AND TransactionDate IS NOT NULL AND TransactionDate <> ''), "
    "osu AS (SELECT t.*, "
    "CAST(SUBSTR(tr, INSTR(tr, '/') + 1, 4) AS INTEGER) AS TYear, "
    "CAST(SUBSTR(TransactionDate, 1, INSTR(TransactionDate, '/') - 1) AS INTEGER) AS TMonth, "
    "CAST(SUBSTR(tr, 1, INSTR(tr, '/') - 1) AS INTEGER) AS TDay, "
    "CAST(SUBSTR(pr, INSTR(pr, '/') + 1, 4) AS INTEGER) AS PYear, "
    "CAST(SUBSTR(PostedDate, 1, INSTR(PostedDate, '/') - 1) AS INTEGER) AS PMonth, "
    "CAST(SUBSTR(pr, 1, INSTR(pr, '/') - 1) AS INTEGER) AS PDay, "
    "CardholderFirstInitial || ' ' || CardholderLastName AS Name FROM t), "
    "m AS (SELECT osu.*, PRINTF('%04d-%02d-%02d', TYear, TMonth, TDay) AS TDate, "
    "PRINTF('%04d-%02d-%02d', PYear, PMonth, PDay) AS PDate FROM osu) "
)
PCT = ["pcards"]
PCC = ["pcards.AgencyName", "pcards.TransactionDate", "pcards.CardholderFirstInitial", "pcards.CardholderLastName",
       "pcards.Amount"]
PCNOTE = ("Use only OSU transactions with a TransactionDate. TransactionDate is text like 7/26/2014 0:00:00; take the "
          "year, month and day from it. Name = first initial and last name. ")


def pc(key, task, prompt, skills, minutes, body, columns=(), hint=None, variant_of=None, optional=False):
    add(key, "SQL", "SQL Part 2 P-card", PC_DOC, task, ["pcards"], PCNOTE + prompt, skills, minutes, PC + body,
        tables=PCT, columns=PCC + list(columns), hint=hint, variant_of=variant_of, optional=optional)


V = ["pcards.Vendor"]
pc("t4q1", "Task 4, Q1", "List the ten most expensive transactions, most expensive first. Show year, month, name, "
                         "amount and vendor.", ["sort", "limit", "date parsing"], 1.5,
   "SELECT TYear AS Year, TMonth AS Month, Name, Amount, Vendor FROM m ORDER BY Amount DESC LIMIT 10;", V,
   "Ten rows.")
pc("t4q2", "Task 4, Q2", "For calendar year 2014, sort transactions by month, then most expensive first, then by name. "
                         "Show the first ten rows: year, month, name, amount and vendor.",
   ["filter", "sort", "date parsing"], 2,
   "SELECT TYear AS Year, TMonth AS Month, Name, Amount, Vendor FROM m WHERE TYear = 2014 "
   "ORDER BY TMonth, Amount DESC, Name LIMIT 10;", V, "Ten rows.")
pc("t4q3", "Task 4, Q3", "Show all 2014 transactions over $3,000, sorted by month, then most expensive first, then by "
                         "name. Show year, month, name, amount and vendor.", ["filter", "sort", "date parsing"], 2,
   "SELECT TYear AS Year, TMonth AS Month, Name, Amount, Vendor FROM m WHERE TYear = 2014 AND Amount > 3000 "
   "ORDER BY TMonth, Amount DESC, Name;", V, "A table.")
pc("t4q4", "Task 4, Q4", "Show all 2014 transactions over $3,000 from a vendor with Amazon anywhere in its name. Show "
                         "vendor, name, amount, year and month, smallest amount first.",
   ["filter", "like", "sort", "date parsing"], 2,
   "SELECT Vendor, Name, Amount, TYear AS Year, TMonth AS Month FROM m WHERE TYear = 2014 AND Amount > 3000 "
   "AND Vendor LIKE '%amazon%' ORDER BY Amount;", V, "A table.")
pc("t4q5", "Task 4, Q5", "What is the total number of P-card transactions? Label the column TotalTrans.", ["count"], 1,
   "SELECT COUNT(*) AS TotalTrans FROM m;", hint="One whole number.")
pc("t4q6", "Task 4, Q6", "How many transactions are for $5,000 or more? Label the column TotalTransGT5k.",
   ["filter", "count"], 1, "SELECT COUNT(*) AS TotalTransGT5k FROM m WHERE Amount >= 5000;", hint="One whole number.")
pc("t4q7", "Task 4, Q7", "What is the total dollar amount of returns (negative amounts) from January to March 2014, "
                         "inclusive? Label the column TotalReturns2014Q1.",
   ["filter", "sum", "date parsing"], 1.5,
   "SELECT ROUND(SUM(Amount), 2) AS TotalReturns2014Q1 FROM m WHERE Amount < 0 AND TYear = 2014 "
   "AND TMonth BETWEEN 1 AND 3;", hint="One amount (negative).")
pc("t4q7v1", "Task 4, Q7", "What is the total dollar amount of returns (negative amounts) from January to March 2013, "
                           "inclusive? Label the column TotalReturns2013Q1.",
   ["filter", "sum", "date parsing"], 1.5,
   "SELECT ROUND(SUM(Amount), 2) AS TotalReturns2013Q1 FROM m WHERE Amount < 0 AND TYear = 2013 "
   "AND TMonth BETWEEN 1 AND 3;", hint="One amount (negative).", variant_of="t4q7")
pc("t4q8", "Task 4, Q8", "How many transactions are there in each year? Most recent year first; label the count "
                         "TotalTrans.", ["group by", "count", "date parsing"], 1.5,
   "SELECT TYear AS Year, COUNT(*) AS TotalTrans FROM m GROUP BY TYear ORDER BY TYear DESC;", hint="Year and count.")
pc("t4q9", "Task 4, Q9", "List all cardholders by number of transactions in 2014, most first. Show name and NumTrans.",
   ["group by", "count", "sort"], 1.5,
   "SELECT Name, COUNT(*) AS NumTrans FROM m WHERE TYear = 2014 GROUP BY Name ORDER BY NumTrans DESC, Name;",
   hint="Name and count.")
pc("t4q10", "Task 4, Q10", "For 2014 returns (negative amounts), list each person with ReturnedGoodsValue (sum of the "
                           "returned amounts) and ReturnedGoodsCount, largest returned value first.",
   ["filter", "group by", "sum", "sort"], 2,
   "SELECT Name, ROUND(SUM(Amount), 2) AS ReturnedGoodsValue, COUNT(*) AS ReturnedGoodsCount FROM m "
   "WHERE TYear = 2014 AND Amount < 0 GROUP BY Name ORDER BY ReturnedGoodsValue, Name;",
   hint="Name, value, count. Values are negative; the largest return is the most negative.")
pc("t4q11", "Task 4, Q11", "List cardholders with more than 10 transactions in 2014, most first. Show name and "
                           "NumTrans.", ["group by", "having", "sort"], 1.5,
   "SELECT Name, COUNT(*) AS NumTrans FROM m WHERE TYear = 2014 GROUP BY Name HAVING COUNT(*) > 10 "
   "ORDER BY NumTrans DESC, Name;", hint="Name and count.")
pc("t4q12", "Task 4, Q12", "List people who returned more than $1,000 of goods in 2014, largest returned value first. "
                           "Show name, ReturnedGoodsValue and ReturnedGoodsCount.",
   ["filter", "group by", "having", "sort"], 2,
   "SELECT Name, ROUND(SUM(Amount), 2) AS ReturnedGoodsValue, COUNT(*) AS ReturnedGoodsCount FROM m "
   "WHERE TYear = 2014 AND Amount < 0 GROUP BY Name HAVING SUM(Amount) < -1000 ORDER BY ReturnedGoodsValue, Name;",
   hint="Name, value, count.")
pc("t4q13", "Task 4, Q13 (optional)", "For December 2014, compute the 4.5 % sales tax each transaction would have "
                                      "carried. Show month, year, name, description, vendor, amount and SalesTax, "
                                      "largest tax first.", ["derived column", "filter", "sort"], 2,
   "SELECT TMonth AS Month, TYear AS Year, Name, Description, Vendor, Amount, ROUND(Amount * 0.045, 2) AS SalesTax "
   "FROM m WHERE TYear = 2014 AND TMonth = 12 ORDER BY Amount * 0.045 DESC;", ["pcards.Description"] + V,
   "A table.", optional=True)
pc("t4q13v1", "Task 4, Q13 (optional)", "For December 2013, compute the 4.5 % sales tax each transaction would have "
                                        "carried. Show month, year, name, description, vendor, amount and SalesTax, "
                                        "largest tax first.", ["derived column", "filter", "sort"], 2,
   "SELECT TMonth AS Month, TYear AS Year, Name, Description, Vendor, Amount, ROUND(Amount * 0.045, 2) AS SalesTax "
   "FROM m WHERE TYear = 2013 AND TMonth = 12 ORDER BY Amount * 0.045 DESC;", ["pcards.Description"] + V,
   "A table.", variant_of="t4q13", optional=True)
pc("t4q14", "Task 4, Q14 (optional)", "For each calendar year, show total amount spent and SalesTaxSaved at 4.5 %, "
                                      "rounded to the cent, most recent year first.", ["group by", "sum", "rounding"],
   2, "SELECT TYear AS Year, ROUND(SUM(Amount), 2) AS TotalSpent, ROUND(SUM(Amount) * 0.045, 2) AS SalesTaxSaved "
      "FROM m GROUP BY TYear ORDER BY TYear DESC;", hint="Year, total, tax.", optional=True)
pc("t4q15", "Task 4, Q15 (optional)", "As Q14, but OSU paid tax in other states 30 % of the time: compute SalesTaxSaved "
                                      "on 70 % of the totals, per calendar year, most recent first.",
   ["group by", "sum", "rounding"], 2,
   "SELECT TYear AS Year, ROUND(SUM(Amount), 2) AS TotalSpent, ROUND(SUM(Amount) * 0.7 * 0.045, 2) AS SalesTaxSaved "
   "FROM m GROUP BY TYear ORDER BY TYear DESC;", hint="Year, total, tax.", optional=True)
pc("t4q16", "Task 4, Q16 (optional)", "For November 2014, compute TimeDif = days from transaction date to posted date. "
                                      "Show month, year, name, description, vendor, amount and TimeDif, longest first, "
                                      "then by name.", ["date arithmetic", "date parsing", "sort"], 2.5,
   "SELECT TMonth AS Month, TYear AS Year, Name, Description, Vendor, Amount, "
   "CAST(JULIANDAY(PDate) - JULIANDAY(TDate) AS INTEGER) AS TimeDif FROM m WHERE TYear = 2014 AND TMonth = 11 "
   "ORDER BY TimeDif DESC, Name;", ["pcards.PostedDate", "pcards.Description"] + V, "A table.", optional=True)
pc("t4q16v1", "Task 4, Q16 (optional)", "For October 2014, compute TimeDif = days from transaction date to posted date. "
                                        "Show month, year, name, description, vendor, amount and TimeDif, longest "
                                        "first, then by name.", ["date arithmetic", "date parsing", "sort"], 2.5,
   "SELECT TMonth AS Month, TYear AS Year, Name, Description, Vendor, Amount, "
   "CAST(JULIANDAY(PDate) - JULIANDAY(TDate) AS INTEGER) AS TimeDif FROM m WHERE TYear = 2014 AND TMonth = 10 "
   "ORDER BY TimeDif DESC, Name;", ["pcards.PostedDate", "pcards.Description"] + V, "A table.",
   variant_of="t4q16", optional=True)
pc("t4q17", "Task 4, Q17 (optional)", "Rank 2014 returns: High if the return is $1,000 or more, Medium if $500 to "
                                      "under $1,000, Low if under $500 (returns are negative amounts). Show year, "
                                      "name, description, vendor, amount and RiskRanking, largest returns first.",
   ["case", "filter", "sort"], 2.5,
   "SELECT TYear AS Year, Name, Description, Vendor, Amount, CASE WHEN Amount <= -1000 THEN 'High' "
   "WHEN Amount <= -500 THEN 'Medium' ELSE 'Low' END AS RiskRanking FROM m WHERE TYear = 2014 AND Amount < 0 "
   "ORDER BY Amount;", ["pcards.Description"] + V, "A table.", optional=True)
pc("t4q18", "Task 4, Q18 (optional)", "For 2014 purchases (amount above 0) at the vendor Amazon.com (any letter case), "
                                      "OSU would earn 0.75 % on transactions of $500 or more and 0.50 % below $500. "
                                      "What is the total? Label it AmazonEarnings.", ["case", "sum", "filter"], 2,
   "SELECT ROUND(SUM(CASE WHEN Amount >= 500 THEN Amount * 0.0075 ELSE Amount * 0.005 END), 2) AS AmazonEarnings "
   "FROM m WHERE TYear = 2014 AND UPPER(Vendor) = 'AMAZON.COM' AND Amount > 0;", V, "One amount.", optional=True)
pc("t4q19", "Task 4, Q19 (optional)", "Show 2014 transactions above the 2014 average transaction amount, most "
                                      "expensive first. Show year, month, name, amount and vendor.",
   ["subquery", "filter", "sort"], 2,
   "SELECT TYear AS Year, TMonth AS Month, Name, Amount, Vendor FROM m WHERE TYear = 2014 AND Amount > "
   "(SELECT AVG(Amount) FROM m WHERE TYear = 2014) ORDER BY Amount DESC;", V, "A table.", optional=True)
pc("t4q20", "Task 4, Q20 (optional)", "For vendors with purchases in both 2013 and 2014, show DiffSpending = 2014 total "
                                      "minus 2013 total, largest increase first.", ["subquery", "join", "group by"], 3,
   "SELECT a.Vendor, ROUND(a.s - b.s, 2) AS DiffSpending FROM (SELECT Vendor, SUM(Amount) AS s FROM m "
   "WHERE TYear = 2014 GROUP BY Vendor) a JOIN (SELECT Vendor, SUM(Amount) AS s FROM m WHERE TYear = 2013 "
   "GROUP BY Vendor) b ON a.Vendor = b.Vendor ORDER BY DiffSpending DESC, a.Vendor;", V, "Vendor and difference.",
   optional=True)
pc("t4q21", "Task 4, Q21 (optional)", "Show 2014 vendors whose 2014 total (TotalSpent) is higher than the total spent "
                                      "at the top vendor of 2013, largest first.", ["subquery", "group by", "having"],
   3, "SELECT ROUND(SUM(Amount), 2) AS TotalSpent, Vendor FROM m WHERE TYear = 2014 GROUP BY Vendor "
      "HAVING SUM(Amount) > (SELECT MAX(s) FROM (SELECT SUM(Amount) AS s FROM m WHERE TYear = 2013 GROUP BY Vendor)) "
      "ORDER BY TotalSpent DESC;", V, "Total and vendor.", optional=True)
pc("t4q22", "Task 4, Q22 (optional)", "For 2012, 2013 and 2014, compute the percentage change in the number of "
                                      "transactions relative to 2011, rounded to two decimals. Label it "
                                      "PercDiffFrom2010 (the case's label).", ["subquery", "group by", "ratio"], 3,
   "SELECT TYear AS Year, ROUND((COUNT(*) - (SELECT COUNT(*) FROM m WHERE TYear = 2011)) * 100.0 / "
   "(SELECT COUNT(*) FROM m WHERE TYear = 2011), 2) AS PercDiffFrom2010 FROM m WHERE TYear IN (2012, 2013, 2014) "
   "GROUP BY TYear ORDER BY TYear;", hint="Three rows: year and percentage.", optional=True)

pc("t5q1", "Task 5, control 1", "Control: no user spends more than $50,000 per year. Show name and total spent in 2014 "
                                "for everyone above $50,000, largest first.", ["group by", "having", "sort"], 2,
   "SELECT Name, ROUND(SUM(Amount), 2) AS TotalSpent FROM m WHERE TYear = 2014 GROUP BY Name "
   "HAVING SUM(Amount) > 50000 ORDER BY TotalSpent DESC;", hint="Name and total.")
pc("t5q1v1", "Task 5, control 1", "Control: no user spends more than $50,000 per year. Show name and total spent in "
                                  "2013 for everyone above $50,000, largest first.", ["group by", "having", "sort"], 2,
   "SELECT Name, ROUND(SUM(Amount), 2) AS TotalSpent FROM m WHERE TYear = 2013 GROUP BY Name "
   "HAVING SUM(Amount) > 50000 ORDER BY TotalSpent DESC;", hint="Name and total.", variant_of="t5q1")
pc("t5q2", "Task 5, control 2", "Control: no user spends more than $10,000 per month without approval. For 2014, show "
                                "name, month and total for every person-month above $10,000, by month (January first) "
                                "and then largest total first.", ["group by", "having", "sort"], 2.5,
   "SELECT Name, ROUND(SUM(Amount), 2) AS TotalSpent, TMonth AS Month FROM m WHERE TYear = 2014 "
   "GROUP BY Name, TMonth HAVING SUM(Amount) > 10000 ORDER BY TMonth, TotalSpent DESC;", hint="Name, total, month.")
pc("t5q3", "Task 5, control 3", "Control: no single transaction above $5,000. Show amount, name, description, vendor, "
                                "transaction date, posted date and MCC for every 2014 transaction above $5,000, sorted "
                                "by amount.", ["filter", "sort"], 1.5,
   "SELECT Amount, Name, Description, Vendor, TransactionDate, PostedDate, MCC FROM m WHERE TYear = 2014 "
   "AND Amount > 5000 ORDER BY Amount;", ["pcards.Description", "pcards.PostedDate", "pcards.MCC"] + V, "A table.")
pc("t5q4", "Task 5, control 4", "Split purchases, same person: find 2014 days where one person made more than one "
                                "transaction at the same vendor with a combined total above $5,000. Show all those "
                                "transactions, earliest date first.", ["group by", "having", "join", "date parsing"], 3,
   "SELECT m.Amount, m.Name, m.Description, m.Vendor, m.TransactionDate, m.PostedDate, m.MCC FROM m JOIN "
   "(SELECT Name, Vendor, TDate FROM m WHERE TYear = 2014 GROUP BY Name, Vendor, TDate "
   "HAVING COUNT(*) > 1 AND SUM(Amount) > 5000) g ON g.Name = m.Name AND g.Vendor = m.Vendor AND g.TDate = m.TDate "
   "ORDER BY m.TDate, m.Name, m.Vendor, m.Amount;", ["pcards.Description", "pcards.PostedDate", "pcards.MCC"] + V,
   "A table.")
pc("t5q5", "Task 5, control 5", "Split purchases between two cardholders: find 2014 vendor-days with exactly two "
                                "different cardholders, one transaction each (so no double payments), and a combined "
                                "total above $5,000. Show those transactions, earliest date first.",
   ["group by", "having", "join", "date parsing"], 3,
   "SELECT m.Amount, m.Name, m.Description, m.Vendor, m.TransactionDate, m.PostedDate, m.MCC FROM m JOIN "
   "(SELECT Vendor, TDate FROM m WHERE TYear = 2014 GROUP BY Vendor, TDate "
   "HAVING COUNT(DISTINCT Name) = 2 AND COUNT(*) = 2 AND SUM(Amount) > 5000) g ON g.Vendor = m.Vendor "
   "AND g.TDate = m.TDate ORDER BY m.TDate, m.Vendor, m.Name;",
   ["pcards.Description", "pcards.PostedDate", "pcards.MCC"] + V, "A table.")
pc("t5q6", "Task 5, control 6", "Split purchases between two vendors: find 2014 person-days with purchases at exactly "
                                "two different vendors, one transaction each (so no double payments), and a combined "
                                "total above $5,000. Show those transactions, earliest date first.",
   ["group by", "having", "join", "date parsing"], 3,
   "SELECT m.Amount, m.Name, m.Description, m.Vendor, m.TransactionDate, m.PostedDate, m.MCC FROM m JOIN "
   "(SELECT Name, TDate FROM m WHERE TYear = 2014 GROUP BY Name, TDate "
   "HAVING COUNT(DISTINCT Vendor) = 2 AND COUNT(*) = 2 AND SUM(Amount) > 5000) g ON g.Name = m.Name "
   "AND g.TDate = m.TDate ORDER BY m.TDate, m.Name, m.Vendor;",
   ["pcards.Description", "pcards.PostedDate", "pcards.MCC"] + V, "A table.")
pc("t5q7", "Task 5, control 7", "Food while travelling: on 2014 days when a person has a transaction whose MCC "
                                "contains hotel, motel, resort or inn, list that person's transactions on the same day "
                                "whose MCC contains food or restaurant. Sort by name, then amount.",
   ["subquery", "like", "join", "date parsing"], 3,
   "SELECT m.Amount, m.Name, m.Description, m.Vendor, m.TransactionDate, m.PostedDate, m.MCC FROM m JOIN "
   "(SELECT DISTINCT Name, TDate FROM m WHERE TYear = 2014 AND (MCC LIKE '%hotel%' OR MCC LIKE '%motel%' "
   "OR MCC LIKE '%resort%' OR MCC LIKE '%inn%')) h ON h.Name = m.Name AND h.TDate = m.TDate "
   "WHERE m.MCC LIKE '%food%' OR m.MCC LIKE '%restaurant%' ORDER BY m.Name, m.Amount;",
   ["pcards.Description", "pcards.PostedDate", "pcards.MCC"] + V, "A table.")

pc("t7q1", "Task 7, Q1 (optional)", "Benford's law: for 2014 transactions of at least $1.00, what share of amounts "
                                    "starts with each digit 1 to 9? Percentages rounded to three decimals.",
   ["text functions", "group by", "ratio"], 3,
   "SELECT SUBSTR(CAST(Amount AS TEXT), 1, 1) AS FirstDigit, ROUND(COUNT(*) * 100.0 / "
   "(SELECT COUNT(*) FROM m WHERE TYear = 2014 AND Amount >= 1), 3) AS Pct FROM m WHERE TYear = 2014 "
   "AND Amount >= 1 GROUP BY FirstDigit ORDER BY FirstDigit;", hint="Nine rows: digit and percentage.",
   optional=True)
pc("t7q2", "Task 7, Q2 (optional)", "Possible duplicate payments in 2014: same day, same vendor, same name and same "
                                    "amount, two or more times, returns excluded. Show date, vendor, name and amount, "
                                    "by date then vendor.", ["group by", "having", "join"], 3,
   "SELECT TransactionDate, Vendor, Name, Amount FROM (SELECT m.*, COUNT(*) OVER (PARTITION BY TDate, Vendor, Name, "
   "Amount) AS n FROM m WHERE TYear = 2014 AND Amount > 0) WHERE n >= 2 ORDER BY TDate, Vendor, Name;", V,
   "A table.", optional=True)
pc("t7q3", "Task 7, Q3 (optional)", "From the possible duplicates in 2014 (same day, vendor, name and amount, returns "
                                    "excluded), list each name with how many duplicate groups they have, most first.",
   ["group by", "having", "subquery"], 3,
   "SELECT Name, COUNT(*) AS DuplicateGroups FROM (SELECT TDate, Vendor, Name, Amount FROM m WHERE TYear = 2014 "
   "AND Amount > 0 GROUP BY TDate, Vendor, Name, Amount HAVING COUNT(*) >= 2) GROUP BY Name "
   "ORDER BY DuplicateGroups DESC, Name;", V, "Name and count.", optional=True)
pc("t7q4", "Task 7, Q4 (optional)", "Round numbers: list 2014 transactions with a four-digit whole-dollar amount ending "
                                    "in 000. Show amount, vendor, description and name, by vendor then name.",
   ["filter", "sort"], 2,
   "SELECT Amount, Vendor, Description, Name FROM m WHERE TYear = 2014 AND Amount >= 1000 AND Amount < 10000 "
   "AND Amount = CAST(Amount AS INTEGER) AND CAST(Amount AS INTEGER) % 1000 = 0 ORDER BY Vendor, Name;",
   ["pcards.Description"] + V, "A table.", optional=True)


def main():
    out = ROOT / "bank" / "questions.json"
    out.write_text(json.dumps(QUESTIONS, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(len(QUESTIONS), "questions", dict(Counter((q["subject"], q["case"]) for q in QUESTIONS)))


if __name__ == "__main__":
    main()
