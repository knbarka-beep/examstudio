import { initImprovement } from "./improvement.js";

const PAGE_SIZE = 25;
const main = document.getElementById("main");
const S = {};
const bank = { subject: "", case: "", source: "", skill: "", text: "", page: 1 };
let lastExam = null;
let stopTimer = null;

// ---------- helpers ----------

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "class") e.className = v;
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat()) {
    if (c !== null && c !== undefined && c !== false) e.append(c instanceof Node ? c : String(c));
  }
  return e;
}

const num = (x, d = 2) => Number(x).toLocaleString("en-GB", { maximumFractionDigits: d });
const mb = (b) => (b < 1e5 ? `${Math.ceil(b / 1e3)} KB` : (b / 1e6).toLocaleString("en-GB", { maximumFractionDigits: 1 }) + " MB");
const pval = (p) => (p < 0.0001 ? p.toExponential(2) : p.toFixed(4));
const pick = (list, avoid) => {
  const pool = list.length > 1 ? list.filter((x) => x.id !== avoid) : list;
  return pool[Math.floor(Math.random() * pool.length)];
};

function issueLink(id, exam) {
  const title = `Issue with ${id} (data ${S.version})`;
  const body = `Question: ${id}\nExam: ${exam ? exam.id : "none"}\nData version: ${S.version}\nPage: ${location.href}\n\nWhat is wrong:\n`;
  const url = `${S.config.repoUrl}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
  return el("p", { class: "issue" }, el("a", { href: url, target: "_blank", rel: "noopener" }, "Report an issue"));
}

function datasetLink(d) {
  const size = d.download_size_bytes ? `zip, ${mb(d.download_size_bytes)}` : `${d.file.split(".").pop()}, ${mb(d.size_bytes)}`;
  return el("a", { class: "button secondary", href: d.download, download: d.download.startsWith("files/") ? d.file : null },
    `Download ${d.label}`, el("span", { class: "muted" }, size));
}

function downloads(ids) {
  const ds = ids.map((id) => S.dsById[id]);
  const box = el("div", { class: "downloads" }, ds.map(datasetLink));
  if (ds.length > 1) {
    box.append(el("button", { type: "button", class: "secondary", onclick: () => {
      for (const d of ds) el("a", { href: d.download, download: d.file }).click();
    } }, "Download both"));
  }
  return box;
}

// ---------- timer ----------

function timer(minutes) {
  const total = minutes * 60000;
  let elapsed = 0, startedAt = null, tick = null;
  const remainingOut = el("span", { class: "time" });
  const elapsedOut = el("span", { class: "time" });
  const status = el("p", { class: "timer-status", "aria-live": "polite" });
  const start = el("button", { type: "button" }, "Start");
  const pause = el("button", { type: "button", class: "secondary" }, "Pause");
  const reset = el("button", { type: "button", class: "secondary" }, "Reset");
  const used = el("span");
  const box = el("section", { class: "timer", "aria-label": "Timer" },
    el("p", { class: "remaining" }, remainingOut, el("span", {}, "remaining")),
    el("p", { class: "elapsed" }, "Elapsed ", elapsedOut),
    status,
    el("div", { class: "buttons" }, start, pause, reset),
    el("div", { class: "progress", "aria-hidden": "true" }, used));
  const sentinel = el("div", { "aria-hidden": "true", style: "height: 1px" });
  const watch = new IntersectionObserver(([en]) =>
    box.classList.toggle("stuck", !en.isIntersecting && en.boundingClientRect.top < 0));
  watch.observe(sentinel);

  const fmt = (ms) => {
    const s = Math.round(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };
  const now = () => Math.min(total, elapsed + (startedAt ? Date.now() - startedAt : 0));
  const draw = () => {
    const e = now();
    remainingOut.textContent = fmt(total - e);
    elapsedOut.textContent = fmt(e);
    used.style.width = `${(e / total) * 100}%`;
    if (e >= total && !box.classList.contains("timeup")) {
      halt();
      box.classList.add("timeup");
      status.textContent = "Time is up";
    }
    start.disabled = !!startedAt || e >= total;
    pause.disabled = !startedAt;
  };
  const halt = () => {
    if (startedAt) elapsed = Math.min(total, elapsed + Date.now() - startedAt);
    startedAt = null;
    clearInterval(tick);
  };
  start.addEventListener("click", () => {
    startedAt = Date.now();
    status.textContent = "";
    tick = setInterval(draw, 250);
    draw();
  });
  pause.addEventListener("click", () => { halt(); status.textContent = "Paused"; draw(); });
  reset.addEventListener("click", () => {
    halt();
    elapsed = 0;
    box.classList.remove("timeup");
    status.textContent = "";
    draw();
  });
  stopTimer = () => { halt(); watch.disconnect(); };
  draw();
  const out = new DocumentFragment();
  out.append(sentinel, box);
  return out;
}

// ---------- workbook chrome ----------
// Column letters and row numbers are aria-hidden chrome; the content itself stays real headings, tables and lists.

const LETTERS = "ABCDEFGHIJ";
const spec = (c) => (c && typeof c === "object" && !(c instanceof Node) && !Array.isArray(c) ? c : { v: c });
const rowNo = (n, tag = "td") => el(tag, { class: "rn", "aria-hidden": "true" }, n ?? "");

function heading(text) {
  return el("h1", { tabindex: "-1" }, text);
}

function title(text, extra) {
  return el("div", { class: "page-title" }, heading(text), extra);
}

function formulaBar(name, ...content) {
  return el("div", { class: "fbar" },
    el("div", { class: "namebox" }, name),
    el("span", { class: "fx", "aria-hidden": "true" }, "fx"),
    el("div", { class: "formula" }, content));
}

// The frame of every page: formula bar on top, sheet body, tabs and status bar at the bottom.
// The clock, when there is one, is inserted as a direct child so it can stick inside the frame.
function workbook(sticky) {
  const top = el("div", { class: "wb-top" });
  const body = el("div", { class: "wb-body" });
  const tabs = el("div", { class: "wb-tabs" });
  const status = el("div", { class: "status-left" });
  const frame = el("div", { class: "workbook" }, top, body,
    el("div", { class: sticky ? "wb-foot sticky" : "wb-foot" }, tabs,
      el("div", { class: "status" }, status, el("p", { class: "status-right" }, `Data version ${S.version}`))));
  return { frame, top, body, tabs, status };
}

// Label and value rows laid out as cells with CSS grid. cols are the widths of columns A, B, ...
function cells(rows, { start = 1, cols = ["13rem", "minmax(0, 1fr)"], letters = true } = {}) {
  let n = start;
  const style = `grid-template-columns: var(--rn) ${cols.join(" ")}`;
  const cell = (c, i) => {
    const s = spec(c);
    return el("div", { class: `cell ${s.cls || (i === 0 ? "lc" : "vc")}`, style: s.span ? `grid-column: span ${s.span}` : null }, s.v);
  };
  const grid = el("div", { class: "cells" },
    letters ? el("div", { class: "cr letters", "aria-hidden": "true", style },
      el("span", { class: "rn" }), cols.map((_, i) => el("span", { class: "cell" }, LETTERS[i]))) : null,
    rows.filter(Boolean).map((r) => el("div", { class: "cr", style }, rowNo(n++, "span"), r.map(cell))));
  return { grid, next: n };
}

function xlRow(n, row, tag = "td") {
  return el("tr", {}, rowNo(n), row.map((c) => {
    const s = spec(c);
    const t = s.th ? "th" : tag;
    return el(t, { scope: t === "th" ? (tag === "th" ? "col" : "row") : null, colspan: s.span || null,
      class: [s.num && "num", s.cls].filter(Boolean).join(" ") || null }, s.v);
  }));
}

// A real <table> drawn as part of the sheet. widths: one entry per column (null = take the rest).
function xl({ widths, head, rows = [], start = 1, letters = true, banded = false, heading: label }) {
  let n = start;
  const table = el("table", { class: banded ? "xl banded" : "xl" },
    el("colgroup", {}, el("col", { class: "rn-col" }), widths.map((w) => el("col", { style: w ? `--w: ${w}` : null }))),
    el("thead", {},
      letters ? el("tr", { class: "letters", "aria-hidden": "true" }, el("td", { class: "rn" }), widths.map((_, i) => el("td", {}, LETTERS[i]))) : null,
      label ? el("tr", { class: "block" }, rowNo(n++), el("th", { scope: "colgroup", colspan: widths.length }, label)) : null,
      head ? xlRow(n++, head, "th") : null),
    el("tbody", {}, rows.map((r) => xlRow(n++, r))));
  return { wrap: el("div", { class: "table-wrap" }, table), table, next: n };
}

// ---------- question panels ----------

function datasetReference(q) {
  const req = q.required_objects || {};
  const has = (list, x) => (list || []).includes(x);
  const grid = (names, bold) => el("ul", { class: "mini-grid" }, names.map((h) => el("li", {}, bold(h) ? el("strong", {}, h) : h)));
  const items = q.dataset_ids.map((id) => {
    const d = S.dsById[id];
    const parts = [el("h3", {}, `${d.label} (${d.file})`)];
    if (d.sheets) {
      const sheets = d.sheets.filter((s) => !req.sheets?.length || has(req.sheets, s.name));
      for (const s of sheets) {
        parts.push(el("p", {}, "Sheet ", el("code", {}, s.name), `, headers in row ${s.header_row}, ${num(s.rows, 0)} data rows:`),
          grid(s.headers.filter((h) => h !== null), (h) => has(req.headers, h)));
      }
    } else if (d.tables) {
      const tables = d.tables.filter((t) => !req.tables?.length || has(req.tables, t.name));
      for (const t of tables) {
        parts.push(el("p", {}, "Table ", el("code", {}, t.name), `, ${num(t.rows, 0)} rows:`),
          grid(t.columns, (c) => has(req.columns, `${t.name}.${c.split(" ")[0]}`)));
      }
    } else {
      parts.push(el("p", {}, `Text file, ${d.delimiter} delimited, ${d.encoding}, ${num(d.rows, 0)} data rows. Headers:`),
        grid(d.headers || [], (h) => has(req.headers, h)));
    }
    return el("div", {}, parts);
  });
  return el("details", { class: "reference" }, el("summary", {}, "Dataset reference"),
    el("p", { class: "muted" }, "Fields the question needs are in bold."), items);
}

function referenceSolution(r) {
  const solution = typeof r.solution === "object" && r.solution !== null ? JSON.stringify(r.solution, null, 1) : r.solution;
  return el("details", { class: "reference" }, el("summary", {}, "Reference solution"),
    solution !== null && solution !== undefined ? el("pre", {}, String(solution)) : null,
    r.draft ? el("pre", {}, r.draft) : null,
    el("p", { class: "muted" }, r.source === "materials" ? `From the course materials (${r.file}).` : "Written for this site and checked against the data."));
}

function runImprovement(question, exam, slot) {
  // IMPROVEMENT: Knut adds his feature here
  if (!S.config.improvementEnabled) return;
  const datasets = (question.dataset_ids || exam?.files || []).map((id) => S.dsById[id]);
  initImprovement({ question, exam, datasets, config: S.config, slot });
}

function questionPanel(q, exam) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const files = exam ? exam.files : q.dataset_ids;
  const { grid } = cells([
    ["Case", q.case],
    ["Time", `about ${num(q.estimated_minutes, 1)} min`],
    ["Files", [downloads(files),
      exam ? el("p", { class: "muted" }, `Open ${files.length > 1 ? "both files" : "the file"} before you start the clock.`) : null]],
    q.expected_answer_hint ? ["Answer format", q.expected_answer_hint] : null,
    [{ v: datasetReference(q), span: 2, cls: "wide" }],
    S.config.showReferenceSolutions && q.reference ? [{ v: referenceSolution(q.reference), span: 2, cls: "wide" }] : null,
    [{ v: issueLink(q.id, exam), span: 2, cls: "wide" }],
  ]);
  const top = [formulaBar(q.id, el("h2", { class: "sr-only" }, `Question ${q.id}`), el("p", { class: "prompt" }, q.prompt)), slot];
  return { top, body: grid, slot };
}

function equation(m) {
  const dep = m.formula.split("~")[0].trim();
  const terms = Object.entries(m.coefficients).map(([term, c]) => {
    if (term === "Intercept") return num(c.coef, 4);
    return `${c.coef < 0 ? "- " : "+ "}${num(Math.abs(c.coef), 4)} x ${term.replace(":", " x ")}`;
  });
  return `${dep} = ${terms.join(" ")}`;
}

// The model as a regression summary sheet: statistics, variables, coefficients, in one run of rows.
const MODEL_WIDTHS = ["11rem", null, "9rem", "10rem", "8rem"];

function modelSheet(m, start) {
  const mono = (v) => ({ v, th: true, cls: "mono" });
  const stats = xl({ widths: MODEL_WIDTHS, start, heading: "Regression statistics", rows: [
    [{ v: "Model", th: true }, { v: el("code", {}, m.formula), span: 4 }],
    [{ v: "R squared", th: true }, "", { v: num(m.r_squared, 4), num: true }, "", ""],
    [{ v: "Adjusted R squared", th: true }, "", { v: num(m.adj_r_squared, 4), num: true }, "", ""],
    [{ v: "Observations", th: true }, "", { v: num(m.n, 0), num: true }, "", ""],
  ] });
  const vars = xl({ widths: MODEL_WIDTHS, start: stats.next, letters: false, heading: "Variables",
    head: ["Variable", "Definition", "Unit", { v: "Observed range", num: true }, ""],
    rows: [
      ...Object.entries(m.variables).map(([name, v]) => [mono(name), v.definition, v.unit || "", { v: `${num(v.min)} to ${num(v.max)}`, num: true }, ""]),
      ...Object.entries(m.dummy_coding || {}).map(([name, codes]) =>
        [mono(name), { v: "Coding: " + Object.entries(codes).map(([k, v]) => `${k} = ${v}`).join("; "), span: 4 }]),
    ] });
  const coefs = xl({ widths: MODEL_WIDTHS, start: vars.next, letters: false, heading: "Coefficients",
    head: ["Parameter", "Term", { v: "Coefficient", num: true }, { v: "Standard error", num: true }, { v: "p-value", num: true }],
    rows: Object.entries(m.coefficients).map(([term, c], i) =>
      [`b${i}`, mono(term), { v: num(c.coef, 4), num: true }, { v: num(c.se, 4), num: true }, { v: pval(c.p), num: true }]) });
  return { parts: [stats.wrap, vars.wrap, coefs.wrap], next: coefs.next };
}

function interpretationPanel(q, exam) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const m = S.mById[q.model_id];
  const sheet = modelSheet(m, 1);
  const { grid } = cells([
    [{ v: el("details", { class: "reference" }, el("summary", {}, "Show answer"),
      el("div", { class: "answer" }, el("p", {}, q.worked_answer))), span: 2, cls: "wide" }],
    [{ v: issueLink(q.id, exam), span: 2, cls: "wide" }],
  ], { start: sheet.next, letters: false });
  const top = [formulaBar(q.id, el("h2", { class: "sr-only" }, `Question ${q.id}`),
    el("p", { class: "prompt" }, q.prompt), el("p", { class: "equation" }, equation(m))), slot];
  return { top, body: [...sheet.parts, grid], slot };
}

// ---------- views ----------

function homeBook(manip, avoid) {
  const e = pick(manip, avoid);
  const qs = e.question_ids.map((id) => S.qById[id]);
  const wb = workbook(false);
  const another = el("button", { type: "button", class: "secondary another", onclick: () => {
    const fresh = homeBook(manip, e.id);
    wb.frame.replaceWith(fresh);
    fresh.querySelector(".another").focus();
  } }, "Show another exam");
  const exam = xl({ widths: ["8rem", "8rem", null, "9rem"], head: ["Question", "Subject", "Case", { v: "Time", num: true }], rows: [
    ...qs.map((q) => [q.id, q.subject, q.case, { v: `${num(q.estimated_minutes, 1)} min`, num: true }]),
    [{ v: el("div", { class: "buttons" }, el("a", { class: "button", href: `#/manipulation/exams/${e.id}` }, `Start exam ${e.id}`), another), span: 3 },
      { v: el("span", { class: "big-time" }, `${e.time_limit_minutes}:00`), num: true }],
  ] });
  const part = (type, label, about, extra) => {
    const exams = S.exams.filter((x) => x.type === type);
    const base = `#/${type}/exams/`;
    return [{ v: label, span: 2 }, { v: [el("p", {}, `${exams[0].question_ids.length} questions in ${exams[0].time_limit_minutes} minutes ${about}`),
      el("p", { class: "links" },
        el("button", { type: "button", class: "secondary", onclick: () => { location.hash = base + pick(exams, lastExam).id; } }, "Start a random exam"),
        el("a", { href: base }, `Browse ${exams.length} exams`), extra)], span: 2, cls: "vc" }];
  };
  const { grid } = cells([
    part("manipulation", "Data manipulation", "on Excel and SQL, with files from the course cases.",
      el("a", { href: "#/manipulation/questions" }, `Question bank (${S.questions.length})`)),
    part("interpretation", "Data interpretation", "on regression output from the restaurant case.", null),
  ], { start: exam.next, cols: ["8rem", "8rem", "minmax(0, 1fr)", "9rem"], letters: false });
  wb.top.append(formulaBar("Start", el("h2", { class: "sr-only" }, `Exam ${e.id}, question 1 of ${qs.length}`),
    el("p", { class: "prompt" }, qs[0].prompt)));
  wb.body.append(exam.wrap, grid);
  wb.status.append(`Start page, exam ${e.id} with ${qs.length} questions`);
  return wb.frame;
}

function home() {
  main.append(
    title("Practice for Data Analytics in Accounting"),
    el("p", { class: "comment" }, "The exams here are built from the course cases, with the same files and a fixed time limit. Practise both kinds: data manipulation and data interpretation."),
    homeBook(S.exams.filter((e) => e.type === "manipulation")));
}

function examList(type) {
  const manip = type === "manipulation";
  const exams = S.exams.filter((e) => e.type === type);
  const base = manip ? "#/manipulation/exams/" : "#/interpretation/exams/";
  const name = manip ? "Data manipulation exams" : "Data interpretation exams";
  const wb = workbook(false);
  const table = xl({ banded: true, widths: manip ? ["7rem", null, null, "7rem"] : ["7rem", null, "7rem"],
    head: manip ? ["Exam", "Spreadsheet file", "Database", { v: "Time", num: true }] : ["Exam", "Models", { v: "Time", num: true }],
    rows: exams.map((e) => [{ v: el("a", { href: base + e.id }, e.id), th: true },
      ...(manip ? e.files.map((f) => S.dsById[f].file) : [e.question_ids.map((id) => S.iById[id].model_id).join(", ")]),
      { v: `${e.time_limit_minutes} min`, num: true }]) });
  wb.top.append(formulaBar("Exams", el("p", {}, manip
    ? "Each exam has five questions and two data files, with 8 minutes in total."
    : "Each exam has four questions on regression output, with 5 minutes in total.")));
  wb.body.append(table.wrap);
  wb.status.append(`${name}, ${exams.length} exams`);
  main.append(
    title(name, el("button", { type: "button", onclick: () => { location.hash = base + pick(exams, lastExam).id; } }, "Pick an exam for me")),
    wb.frame);
}

// Exam pages: questions as sheet tabs at the bottom, the clock frozen under the formula bar.
function examBook(e, qs, panel, label, back) {
  lastExam = e.id;
  let active = 0;
  const wb = workbook(true);
  const strip = el("ol", { class: "sheet-tabs" });
  const prev = el("button", { type: "button", class: "secondary" }, "Previous");
  const next = el("button", { type: "button", class: "secondary" }, "Next");
  const show = (i) => {
    active = i;
    const { top, body, slot } = panel(qs[i], e);
    wb.top.replaceChildren(...top);
    wb.body.replaceChildren(...[body].flat());
    wb.status.textContent = `Exam ${e.id}, question ${i + 1} of ${qs.length}`;
    strip.querySelectorAll("button").forEach((b, j) => b.setAttribute("aria-current", j === i ? "true" : "false"));
    prev.disabled = i === 0;
    next.disabled = i === qs.length - 1;
    runImprovement(qs[i], e, slot);
  };
  qs.forEach((q, i) => strip.append(el("li", {}, el("button", { type: "button", onclick: () => show(i) }, label(q, i)))));
  prev.addEventListener("click", () => show(active - 1));
  next.addEventListener("click", () => show(active + 1));
  wb.tabs.append(el("nav", { "aria-label": "Questions in this exam" }, strip), el("div", { class: "buttons" }, prev, next));
  wb.frame.insertBefore(timer(e.time_limit_minutes), wb.body);
  main.append(title(`Exam ${e.id}`, back), wb.frame);
  show(0);
}

function examView(e) {
  examBook(e, e.question_ids.map((id) => S.qById[id]), questionPanel, (q, i) => `${i + 1} ${q.subject}`,
    el("a", { href: "#/manipulation/exams" }, "All manipulation exams"));
}

function interpretationExam(e) {
  examBook(e, e.question_ids.map((id) => S.iById[id]), interpretationPanel, (q, i) => `Question ${i + 1}`,
    el("a", { href: "#/interpretation/exams" }, "All interpretation exams"));
}

function filtered() {
  const t = bank.text.toLowerCase();
  return S.questions.filter((q) =>
    (!bank.subject || q.subject === bank.subject) && (!bank.case || q.case === bank.case) &&
    (!bank.source || q.source_file === bank.source) && (!bank.skill || q.skills.includes(bank.skill)) &&
    (!t || `${q.id} ${q.prompt}`.toLowerCase().includes(t)));
}

function bankView() {
  const uniq = (f) => [...new Set(S.questions.flatMap(f))].sort();
  const wb = workbook(false);
  const select = (key, name, values) => el("td", {}, el("label", { class: "flabel", for: `f-${key}` }, "Filter"),
    el("select", { id: `f-${key}`, "aria-label": `Filter by ${name}`, onchange: (ev) => { bank[key] = ev.target.value; bank.page = 1; draw(); } },
      el("option", { value: "" }, "All"),
      values.map((v) => el("option", { value: v, selected: bank[key] === v }, v))));
  const table = xl({ banded: true, widths: ["5rem", null, "6rem", "9rem", "10rem", "13rem"],
    head: ["Id", "Prompt", "Subject", "Case", "Skills", "Source file"] });
  table.table.tHead.append(el("tr", { class: "autofilter" }, rowNo(2), el("td", {}),
    el("td", {}, el("label", { class: "flabel", for: "f-text" }, "Search"),
      el("input", { id: "f-text", type: "search", value: bank.text, "aria-label": "Search ids and prompts",
        oninput: (ev) => { bank.text = ev.target.value; bank.page = 1; draw(); } })),
    select("subject", "subject", uniq((q) => [q.subject])),
    select("case", "case", uniq((q) => [q.case])),
    select("skill", "skill", uniq((q) => q.skills)),
    select("source", "source file", uniq((q) => [q.source_file]))));
  const count = el("span", { "aria-live": "polite" });
  const page = el("span");
  const go = (p) => { bank.page = p; draw(); wb.frame.scrollIntoView(); };
  const prev = el("button", { type: "button", class: "secondary", onclick: () => go(bank.page - 1) }, "Previous");
  const next = el("button", { type: "button", class: "secondary", onclick: () => go(bank.page + 1) }, "Next");
  const draw = () => {
    const list = filtered();
    const pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    bank.page = Math.min(bank.page, pages);
    const from = (bank.page - 1) * PAGE_SIZE;
    const shown = list.slice(from, from + PAGE_SIZE);
    table.table.tBodies[0].replaceChildren(...shown.map((q, i) => xlRow(from + i + 3, [
      { v: el("a", { href: `#/manipulation/questions/${q.id}` }, q.id), th: true },
      q.prompt, q.subject, q.case, q.skills.join(", "), q.source_file])));
    count.textContent = `Question bank, ${list.length} questions, ${shown.length} shown`;
    page.textContent = `Page ${bank.page} of ${pages}`;
    prev.disabled = bank.page === 1;
    next.disabled = bank.page === pages;
  };
  wb.top.append(formulaBar("Bank", el("p", {},
    "All validated data manipulation questions. Exams draw from the required ones; questions marked optional in the cases are only here.")));
  wb.body.append(table.wrap);
  wb.status.append(count, el("span", { class: "pager" }, prev, page, next));
  main.append(title("Question bank"), wb.frame);
  draw();
}

function bankQuestion(q) {
  const list = filtered();
  const i = list.indexOf(q);
  const wb = workbook(false);
  const { top, body, slot } = questionPanel(q, null);
  wb.top.append(...top);
  wb.body.append(body);
  if (i >= 0) {
    wb.tabs.append(el("span"), el("div", { class: "buttons" },
      i > 0 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i - 1].id}` }, "Previous") : null,
      i < list.length - 1 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i + 1].id}` }, "Next") : null));
  }
  wb.status.append(i >= 0 ? `Question bank, question ${i + 1} of ${list.length}` : `Question bank, ${q.id}`);
  main.append(title(`${q.id}${q.optional ? " (optional)" : ""}`, el("a", { href: "#/manipulation/questions" }, "Question bank")), wb.frame);
  runImprovement(q, null, slot);
}

function notFound() {
  main.append(heading("Page not found"), el("p", {}, el("a", { href: "#/" }, "Back to the start page")));
}

// ---------- routing ----------

function route() {
  if (stopTimer) stopTimer();
  stopTimer = null;
  main.replaceChildren();
  const p = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const key = p.slice(0, 2).join("/");
  const id = p[2];
  if (!p.length) home();
  else if (key === "manipulation/exams" && !id) examList("manipulation");
  else if (key === "manipulation/exams" && S.eById[id]?.type === "manipulation") examView(S.eById[id]);
  else if (key === "manipulation/questions" && !id) bankView();
  else if (key === "manipulation/questions" && S.qById[id]) bankQuestion(S.qById[id]);
  else if (key === "interpretation/exams" && !id) examList("interpretation");
  else if (key === "interpretation/exams" && S.eById[id]?.type === "interpretation") interpretationExam(S.eById[id]);
  else notFound();
  document.querySelectorAll(".site-header nav a").forEach((a) =>
    a.setAttribute("aria-current", location.hash.startsWith(a.getAttribute("href")) ? "page" : "false"));
  window.scrollTo(0, 0);
  main.querySelector("h1")?.focus();
}

async function load() {
  const get = async (name) => {
    const r = await fetch(`data/${name}.json`);
    if (!r.ok) throw new Error(`${name}.json: ${r.status}`);
    return r.json();
  };
  try {
    const [config, questions, exams, interp, datasets] = await Promise.all(
      ["config", "questions", "exams", "interpretation", "datasets"].map(get));
    Object.assign(S, {
      config, version: questions.version, questions: questions.questions, exams: exams.exams,
      datasets: datasets.datasets, models: interp.models, interp: interp.questions,
    });
    const index = (list) => Object.fromEntries(list.map((x) => [x.id, x]));
    S.qById = index(S.questions);
    S.eById = index(S.exams);
    S.iById = index(S.interp);
    S.mById = index(S.models);
    S.dsById = index(S.datasets);
  } catch (err) {
    main.replaceChildren(heading("The data could not be loaded"),
      el("p", {}, `${err.message}. If you opened the file directly, run a local server: py -m http.server 8000 --directory docs`));
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}

load();
