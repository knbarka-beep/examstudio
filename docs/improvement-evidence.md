# Improvement evidence: answer check and exam mode

All counts below are taken from the published data files on 01.11.2026 (`docs/data/checks.json`, `docs/data/probes.json`, `docs/data/questions.json`, `docs/data/interpretation.json`), not estimated. The question-to-probe matching follows the rules in `docs/js/examiner.js` (`questionProbes` and `tagsOf`).

## Questions on the site

| Topic | Questions | With an answer check | With a computed trap | With a tied question probe | With at least one trap tag |
|---|---:|---:|---:|---:|---:|
| Excel | 81 | 68 | 26 | 72 | 75 |
| SQL | 96 | 35 | 10 | 80 | 81 |
| Regression interpretation | 49 | 0 | 0 | 49 | 16 |
| All | 226 | 103 | 36 | 201 | 172 |

Regression questions have no answer check; their probes come from the interpretation kind (predict 17, significance 16, coefficient 10, dummy 6).

## Computed traps (checks.json)

38 traps on 36 questions. Each one is computed from the raw data with the wrong method by `scripts/build_checks.py` and kept only when it differs from the right answer.

| Trap tag | Traps | Questions with a trap of this tag |
|---|---:|---:|
| Wrong definition | 11 | 11 |
| Boundary or parsing | 9 | 9 |
| Wrong population | 7 | 6 |
| Wrong grain | 6 | 6 |
| Non-unique key | 3 | 3 |
| Average of ratios | 2 | 2 |
| Rows duplicated by a join | 0 | 0 |
| Confounding | 0 | 0 |

Join and confounding have no computed trap. They are covered only by probes.

## The examiner's probe bank (probes.json)

35 probes, all hand-written, every one with a pushback line for a thin answer.

| Kind | Probes | When it is asked |
|---|---:|---|
| Trap | 7 | The answer box or a number in the transcript matches a computed trap |
| Question | 11 | Tied to the question by skill, interpretation kind or number of tables |
| Trigger | 13 | The transcript or answer box contains a trigger term (for example JOIN, VLOOKUP, GROUP BY, "causes") |
| Generic | 4 | Nothing else applies |

| Trap tag | Probes with this tag | Questions tied to this tag ("Practise my weak spots" pool) |
|---|---:|---:|
| Non-unique key | 6 | 24 |
| Wrong grain | 4 | 44 |
| Confounding | 4 | 16 |
| Average of ratios | 3 | 16 |
| Wrong population | 3 | 80 |
| Boundary or parsing | 3 | 62 |
| Wrong definition | 2 | 11 |
| Rows duplicated by a join | 2 | 14 |
| No tag (generic, significance, R squared, prediction) | 8 | |

"Practise my weak spots" picks first from the questions with a computed trap of the tag, then from any question tied to it.

## Strictness presets (examiner.js)

| Preset | Probes per task | Cuts in | Hints | Pushbacks on thin answers | Hard stop |
|---|---|---|---|---:|---|
| Supportive | 1 to 2 | Only at a 4 s pause | Unlimited | 1 (gentle) | No |
| Standard | 3 to 4 | 0.8 s after a trigger term, or after 75 s of talking | 1 | 1 | Yes |
| Strict | 4 to 6 | 1.5 s after a trigger term, even mid-sentence, or after 45 s | 0 | 2 | Yes |

In every preset there are at least 20 seconds between two interruptions. An answer is "thin" when it has fewer than 15 words or none of the words because, so, since, otherwise, which means, the reason.

## Tests

- `node tests/check_answers.mjs`: every expected answer grades as correct, every trap as its trap, plus 27 format cases.
- `py tests/smoke.py`: checks the published site, including that every probe tag exists and every trap tag has a probe.
