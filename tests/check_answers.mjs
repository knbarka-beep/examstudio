// Tests the answer check: every expected answer grades as correct, every trap grades as that trap,
// and common formats are read. Run: node tests/check_answers.mjs
import { readFileSync } from "node:fs";
import { grade } from "../docs/js/improvement.js";

const { checks } = JSON.parse(readFileSync(new URL("../docs/data/checks.json", import.meta.url)));
let fail = 0;
const expect = (cond, msg) => { if (!cond) { fail++; console.log("FAIL", msg); } };
const asTyped = (c, v) => (c.kind === "percent" ? `${(v * 100).toFixed(2)}%` : String(v));

for (const [id, c] of Object.entries(checks)) {
  expect(grade(c, asTyped(c, c.answer)).state === "correct", `${id} answer ${c.answer}`);
  for (const t of c.traps) {
    const r = grade(c, asTyped(c, t.value));
    expect(r.state === "trap" && r.trap === t, `${id} trap ${t.value} gave ${r.state}`);
  }
  for (const a of c.also || []) expect(grade(c, String(a)).state === "also", `${id} also ${a}`);
}
const c = (id) => checks[id];
const cases = [
  ["Q055", "1194", "correct"], ["Q055", "1.194", "correct"], ["Q055", "1,194", "correct"], ["Q055", "1 194", "correct"],
  ["Q057", "397.979,46", "correct"], ["Q057", "397,979.46", "correct"], ["Q057", "$397,979.46", "correct"],
  ["Q057", "395080.30", "trap"], ["Q052", "(398,321.61)", "correct"], ["Q052", "398321,61", "trap"],
  ["Q016", "20%", "correct"], ["Q016", "20", "correct"], ["Q016", "0.2", "correct"], ["Q016", "8%", "trap"],
  ["Q024", "23,65 %", "correct"], ["Q024", "18%", "trap"], ["Q006", "07.12.2011 16:38", "correct"],
  ["Q006", "2011-12-07 16:38:00", "correct"], ["Q006", "12/7/2011 4:38", "wrong"], ["Q006", "07.12.2011", "notime"],
  ["Q048", " brian gibson ", "correct"], ["Q048", "Elizabeth Rees", "trap"], ["Q061", "9,66", "correct"], ["Q061", "16,24", "trap"], ["Q001", "abc", "unreadable"], ["Q001", "33501", "wrong"],
];
for (const [id, v, want] of cases) {
  const got = grade(c(id), v).state;
  expect(got === want, `${id} "${v}" expected ${want}, got ${got}`);
}
console.log(fail ? `${fail} failed` : `all passed (${Object.keys(checks).length} checks)`);
process.exit(fail ? 1 : 0);
