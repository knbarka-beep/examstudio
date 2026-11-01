import { initImprovement } from "./improvement.js?v=01.11.2026-2856ff5";
import { examMode } from "./examiner.js?v=01.11.2026-2856ff5";

const PAGE_SIZE = 25;
const main = document.getElementById("main");
const S = {};
const bank = { subject: "", case: "", source: "", skill: "", text: "", page: 1 };
let lastExam = null;
let cleanup = null; // stops the timer, speech and recognition of the page being left

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
  cleanup = () => { halt(); watch.disconnect(); };
  draw();
  const out = new DocumentFragment();
  out.append(sentinel, box);
  return out;
}

// ---------- page parts ----------

function heading(text) {
  return el("h1", { tabindex: "-1" }, text);
}

function pageHead(text, { lead, back, action } = {}) {
  return el("header", { class: "page-head" },
    back || null,
    el("div", { class: "head-row" }, heading(text), action || null),
    lead ? el("p", { class: "lead" }, lead) : null);
}

const backLink = (href, text) => el("a", { class: "back", href }, text);

// Label and value pairs as a definition list.
function facts(rows) {
  return el("dl", { class: "facts" }, rows.filter(Boolean).flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
}

// A real <table>. Cells are plain values or { v, th, num, span }.
const spec = (c) => (c && typeof c === "object" && !(c instanceof Node) && !Array.isArray(c) ? c : { v: c });

function tableRow(row, tag = "td") {
  return el("tr", {}, row.map((c) => {
    const s = spec(c);
    const t = s.th ? "th" : tag;
    return el(t, { scope: t === "th" ? (tag === "th" ? "col" : "row") : null, colspan: s.span || null,
      class: [s.num && "num", s.cls].filter(Boolean).join(" ") || null }, s.v);
  }));
}

function table({ head, rows = [], caption }) {
  const t = el("table", { class: "data" },
    caption ? el("caption", {}, caption) : null,
    head ? el("thead", {}, tableRow(head, "th")) : null,
    el("tbody", {}, rows.map((r) => tableRow(r))));
  return { wrap: el("div", { class: "table-wrap" }, t), table: t };
}

// ---------- question panels ----------

function datasetReference(q) {
  const req = q.required_objects || {};
  const has = (list, x) => (list || []).includes(x);
  const list = (names, bold) => el("ul", { class: "cols" }, names.map((h) => el("li", {}, bold(h) ? el("strong", {}, h) : h)));
  const items = q.dataset_ids.map((id) => {
    const d = S.dsById[id];
    const parts = [el("h3", {}, `${d.label} (${d.file})`)];
    if (d.sheets) {
      const sheets = d.sheets.filter((s) => !req.sheets?.length || has(req.sheets, s.name));
      for (const s of sheets) {
        parts.push(el("p", {}, "Sheet ", el("code", {}, s.name), `, headers in row ${s.header_row}, ${num(s.rows, 0)} data rows:`),
          list(s.headers.filter((h) => h !== null), (h) => has(req.headers, h)));
      }
    } else if (d.tables) {
      const tables = d.tables.filter((t) => !req.tables?.length || has(req.tables, t.name));
      for (const t of tables) {
        parts.push(el("p", {}, "Table ", el("code", {}, t.name), `, ${num(t.rows, 0)} rows:`),
          list(t.columns, (c) => has(req.columns, `${t.name}.${c.split(" ")[0]}`)));
      }
    } else {
      parts.push(el("p", {}, `Text file, ${d.delimiter} delimited, ${d.encoding}, ${num(d.rows, 0)} data rows. Headers:`),
        list(d.headers || [], (h) => has(req.headers, h)));
    }
    return el("div", {}, parts);
  });
  return el("details", { class: "reference" }, el("summary", {}, "Dataset reference"),
    el("p", { class: "muted small" }, "Fields the question needs are highlighted."), items);
}

function referenceSolution(r) {
  const solution = typeof r.solution === "object" && r.solution !== null ? JSON.stringify(r.solution, null, 1) : r.solution;
  return el("details", { class: "reference" }, el("summary", {}, "Reference solution"),
    solution !== null && solution !== undefined ? el("pre", {}, String(solution)) : null,
    r.draft ? el("pre", {}, r.draft) : null,
    el("p", { class: "muted" }, r.source === "materials" ? `From the course materials (${r.file}).` : "Written for this site and checked against the data."));
}

function runImprovement(question, exam, slot) {
  // IMPROVEMENT: the answer check; exam mode builds on it (examiner.js)
  if (!S.config.improvementEnabled) return;
  const datasets = (question.dataset_ids || exam?.files || []).map((id) => S.dsById[id]);
  initImprovement({ question, exam, datasets, config: S.config, slot });
}

function questionPanel(q, exam, { files = true } = {}) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const ids = exam ? exam.files : q.dataset_ids;
  const card = el("article", { class: "card question" },
    el("p", { class: "qid" }, `${q.id}, ${q.subject}`),
    el("h2", { class: "sr-only" }, `Question ${q.id}`),
    el("p", { class: "prompt" }, q.prompt),
    slot,
    facts([
      ["Case", q.case],
      ["Time", `about ${num(q.estimated_minutes, 1)} min`],
      files ? ["Files", [downloads(ids),
        exam ? el("p", { class: "muted small" }, `Open ${ids.length > 1 ? "both files" : "the file"} before you start the clock.`) : null]] : null,
      q.expected_answer_hint ? ["Answer format", q.expected_answer_hint] : null,
      ["Data", datasetReference(q)],
      S.config.showReferenceSolutions && q.reference ? ["Solution", referenceSolution(q.reference)] : null,
    ]),
    issueLink(q.id, exam));
  return { card, slot };
}

function equation(m) {
  const dep = m.formula.split("~")[0].trim();
  const terms = Object.entries(m.coefficients).map(([term, c]) => {
    if (term === "Intercept") return num(c.coef, 4);
    return `${c.coef < 0 ? "- " : "+ "}${num(Math.abs(c.coef), 4)} x ${term.replace(":", " x ")}`;
  });
  return `${dep} = ${terms.join(" ")}`;
}

// The model as three tables: statistics, variables, coefficients.
function modelTables(m) {
  const mono = (v) => ({ v: el("code", {}, v), th: true });
  const stats = table({ caption: "Regression statistics", rows: [
    [{ v: "Model", th: true }, el("code", {}, m.formula)],
    [{ v: "R squared", th: true }, { v: num(m.r_squared, 4), num: true }],
    [{ v: "Adjusted R squared", th: true }, { v: num(m.adj_r_squared, 4), num: true }],
    [{ v: "Observations", th: true }, { v: num(m.n, 0), num: true }],
  ] });
  const vars = table({ caption: "Variables", head: ["Variable", "Definition", "Unit", { v: "Observed range", num: true }], rows: [
    ...Object.entries(m.variables).map(([name, v]) => [mono(name), v.definition, v.unit || "", { v: `${num(v.min)} to ${num(v.max)}`, num: true }]),
    ...Object.entries(m.dummy_coding || {}).map(([name, codes]) =>
      [mono(name), { v: "Coding: " + Object.entries(codes).map(([k, v]) => `${k} = ${v}`).join("; "), span: 3 }]),
  ] });
  const coefs = table({ caption: "Coefficients",
    head: ["Parameter", "Term", { v: "Coefficient", num: true }, { v: "Standard error", num: true }, { v: "p-value", num: true }],
    rows: Object.entries(m.coefficients).map(([term, c], i) =>
      [`b${i}`, mono(term), { v: num(c.coef, 4), num: true }, { v: num(c.se, 4), num: true }, { v: pval(c.p), num: true }]) });
  return el("div", { class: "tables" }, stats.wrap, vars.wrap, coefs.wrap);
}

function interpretationPanel(q, exam, { answer = true } = {}) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const m = S.mById[q.model_id];
  const card = el("article", { class: "card question" },
    el("p", { class: "qid" }, `${q.id}, model ${m.id}`),
    el("h2", { class: "sr-only" }, `Question ${q.id}`),
    el("p", { class: "prompt" }, q.prompt),
    el("p", { class: "equation" }, equation(m)),
    slot,
    el("div", { style: "margin-top: 24px" }, modelTables(m)),
    answer ? facts([["Answer", el("details", { class: "reference" }, el("summary", {}, "Show answer"),
      el("div", { class: "answer" }, el("p", {}, q.worked_answer)))]]) : null,
    issueLink(q.id, exam));
  return { card, slot };
}

// ---------- views ----------

function home() {
  const manip = S.exams.filter((e) => e.type === "manipulation");
  const interp = S.exams.filter((e) => e.type === "interpretation");
  const random = (list) => () => { location.hash = `#/${list[0].type}/exams/${pick(list, lastExam).id}`; };
  const tile = (title, text, ...actions) => el("section", { class: "card tile" }, el("h2", {}, title), el("p", {}, text),
    el("div", { class: "buttons" }, actions));
  main.append(
    pageHead("Practice", { lead: "Timed exams and a question bank built from the Data Analytics in Accounting cases, with the same data files." }),
    el("div", { class: "grid2" },
      tile("Data manipulation", `${manip[0].question_ids.length} questions on Excel and SQL in ${manip[0].time_limit_minutes} minutes, with two files from the course cases.`,
        el("button", { type: "button", class: "big", onclick: random(manip) }, "Start a random exam"),
        el("a", { class: "button secondary", href: "#/manipulation/exams" }, `Browse ${manip.length} exams`)),
      tile("Data interpretation", `${interp[0].question_ids.length} questions on regression output from the restaurant case in ${interp[0].time_limit_minutes} minutes.`,
        el("button", { type: "button", class: "secondary", onclick: random(interp) }, "Start a random exam"),
        el("a", { class: "button secondary", href: "#/interpretation/exams" }, `Browse ${interp.length} exams`)),
      tile("Question bank", `All ${S.questions.length} validated data manipulation questions, with filters by subject, case and skill.`,
        el("a", { class: "button secondary", href: "#/manipulation/questions" }, "Open the question bank")),
      S.config.improvementEnabled ? tile("Exam mode", "One task at a time with an examiner who asks follow-up questions while you work and explain.",
        el("a", { class: "button secondary", href: "#/exam-mode" }, "Set up exam mode")) : null));
}

function examList(type) {
  const manip = type === "manipulation";
  const exams = S.exams.filter((e) => e.type === type);
  const base = manip ? "#/manipulation/exams/" : "#/interpretation/exams/";
  const t = table({
    head: manip ? ["Exam", "Spreadsheet file", "Database", { v: "Time", num: true }] : ["Exam", "Models", { v: "Time", num: true }],
    rows: exams.map((e) => [{ v: el("a", { href: base + e.id }, e.id), th: true },
      ...(manip ? e.files.map((f) => S.dsById[f].file) : [e.question_ids.map((id) => S.iById[id].model_id).join(", ")]),
      { v: `${e.time_limit_minutes} min`, num: true }]) });
  main.append(
    pageHead(manip ? "Data manipulation exams" : "Data interpretation exams", {
      back: backLink("#/", "Practice"),
      lead: manip ? "Each exam has five questions and two data files, with 8 minutes in total."
        : "Each exam has four questions on regression output, with 5 minutes in total.",
      action: el("button", { type: "button", onclick: () => { location.hash = base + pick(exams, lastExam).id; } }, "Pick an exam for me") }),
    t.wrap);
}

// Exam pages: question tabs, the clock, then the active question.
function examBook(e, qs, panel, label, back) {
  lastExam = e.id;
  let active = 0;
  const strip = el("ol", { class: "qtabs" });
  const holder = el("div");
  const prev = el("button", { type: "button", class: "secondary" }, "Previous");
  const next = el("button", { type: "button", class: "secondary" }, "Next");
  const show = (i) => {
    active = i;
    const { card, slot } = panel(qs[i], e);
    holder.replaceChildren(card);
    strip.querySelectorAll("button").forEach((b, j) => b.setAttribute("aria-current", j === i ? "true" : "false"));
    prev.disabled = i === 0;
    next.disabled = i === qs.length - 1;
    runImprovement(qs[i], e, slot);
  };
  qs.forEach((q, i) => strip.append(el("li", {}, el("button", { type: "button", onclick: () => show(i) }, label(q, i)))));
  prev.addEventListener("click", () => show(active - 1));
  next.addEventListener("click", () => show(active + 1));
  main.append(pageHead(`Exam ${e.id}`, { back }),
    el("nav", { "aria-label": "Questions in this exam" }, strip),
    timer(e.time_limit_minutes), holder,
    el("div", { class: "step-nav" }, prev, next));
  show(0);
}

function examView(e) {
  examBook(e, e.question_ids.map((id) => S.qById[id]), questionPanel, (q, i) => `${i + 1} ${q.subject}`,
    backLink("#/manipulation/exams", "All manipulation exams"));
}

function interpretationExam(e) {
  examBook(e, e.question_ids.map((id) => S.iById[id]), interpretationPanel, (q, i) => `Question ${i + 1}`,
    backLink("#/interpretation/exams", "All interpretation exams"));
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
  const select = (key, name, values) => el("label", {}, name,
    el("select", { onchange: (ev) => { bank[key] = ev.target.value; bank.page = 1; draw(); } },
      el("option", { value: "" }, "All"),
      values.map((v) => el("option", { value: v, selected: bank[key] === v }, v))));
  const t = table({ head: ["Id", "Prompt", "Subject", "Case", "Skills"] });
  const count = el("p", { class: "muted small", "aria-live": "polite" });
  const page = el("span", { class: "muted small" });
  const go = (p) => { bank.page = p; draw(); t.wrap.scrollIntoView({ block: "start" }); };
  const prev = el("button", { type: "button", class: "secondary", onclick: () => go(bank.page - 1) }, "Previous");
  const next = el("button", { type: "button", class: "secondary", onclick: () => go(bank.page + 1) }, "Next");
  const draw = () => {
    const list = filtered();
    const pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    bank.page = Math.min(bank.page, pages);
    const from = (bank.page - 1) * PAGE_SIZE;
    const shown = list.slice(from, from + PAGE_SIZE);
    t.table.tBodies[0].replaceChildren(...shown.map((q) => tableRow([
      { v: el("a", { href: `#/manipulation/questions/${q.id}` }, q.id), th: true },
      q.prompt, q.subject, q.case, q.skills.join(", ")])));
    count.textContent = `${list.length} questions, ${shown.length} shown`;
    page.textContent = `Page ${bank.page} of ${pages}`;
    prev.disabled = bank.page === 1;
    next.disabled = bank.page === pages;
  };
  main.append(
    pageHead("Question bank", { back: backLink("#/", "Practice"),
      lead: "All validated data manipulation questions. Exams draw from the required ones; questions marked optional in the cases are only here." }),
    el("div", { class: "filters" },
      el("label", { class: "search" }, "Search ids and prompts",
        el("input", { type: "search", value: bank.text, oninput: (ev) => { bank.text = ev.target.value; bank.page = 1; draw(); } })),
      select("subject", "Subject", uniq((q) => [q.subject])),
      select("case", "Case", uniq((q) => [q.case])),
      select("skill", "Skill", uniq((q) => q.skills)),
      select("source", "Source file", uniq((q) => [q.source_file]))),
    count, t.wrap,
    el("div", { class: "pager" }, prev, page, next));
  draw();
}

function bankQuestion(q) {
  const list = filtered();
  const i = list.indexOf(q);
  const { card, slot } = questionPanel(q, null);
  main.append(pageHead(`${q.id}${q.optional ? " (optional)" : ""}`, { back: backLink("#/manipulation/questions", "Question bank") }), card,
    i >= 0 ? el("div", { class: "step-nav" },
      i > 0 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i - 1].id}` }, "Previous") : el("span"),
      i < list.length - 1 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i + 1].id}` }, "Next") : null) : null);
  runImprovement(q, null, slot);
}

function about() {
  main.append(
    pageHead("About", { lead: "A practice site for the course Data Analytics in Accounting at SDU." }),
    el("div", { class: "stack" },
      el("section", { class: "soft" }, el("h2", {}, "What is here"),
        el("p", {}, `Every question is built from the course cases and their data files, and checked against the data before it is published. There are ${S.questions.length} data manipulation questions in Excel and SQL, and ${S.interp.length} data interpretation questions on regression output.`),
        el("p", {}, "The answer check compares a typed result with the answer computed from the data. Where a common wrong method gives a different number, that number is computed too, so the site can name the mistake.")),
      S.config.improvementEnabled ? el("section", { class: "soft" }, el("h2", {}, "Exam mode"),
        el("p", {}, "Exam mode gives one task at a time with a countdown. An examiner reads the task aloud and asks follow-up questions while you work. The questions are chosen by fixed rules from what you say or type and from the answer you enter; when your answer matches a known wrong method, the examiner asks about that mistake. No AI model is used and nothing is stored.")) : null,
      el("section", { class: "soft" }, el("h2", {}, "Why I built it"),
        el("p", {}, "My improvement is an exam mode. The original site lets you open an exam and start a timer, but nobody asks you why you did what you did. When I practise, I usually know a formula exists. The problem is remembering which one to use under time pressure, for example to pull a value out of the middle of a cell, and then explaining it while someone listens. Exam mode reads the task aloud and listens while you work. Then it interrupts with follow-up questions. Those questions come from typical mistakes in accounting data work, like the wrong grain after a join, counting the same album twice, averaging percentages, or keeping a dummy term that should be zero. In total, 105 questions have an answer check, and 39 known trap answers each trigger a question aimed at that mistake. If you answer 49 on Q108, the examiner asks what one row in your result represents. Everything is rules-based, so there is no AI and nothing is stored. I would not use it every day. It feels a bit impractical for normal practice, and I think that is fine, because it is meant as a dress rehearsal for the last week before the exam. That fits what the site is for in the first place: showing students what to expect so the exam feels less scary.")),
      el("section", { class: "soft" }, el("h2", {}, "Source and issues"),
        el("p", {}, el("a", { href: S.config.repoUrl }, "Source code on GitHub"), `. Data version ${S.version}.`))));
}

function notFound() {
  main.append(pageHead("Page not found"), el("p", {}, el("a", { href: "#/" }, "Back to Practice")));
}

// What exam mode reuses from the practice pages.
const ui = { S, el, num, pick, heading, pageHead, facts, table, downloads, datasetReference, modelTables, equation, issueLink };

// ---------- routing ----------

function route() {
  if (cleanup) cleanup();
  cleanup = null;
  main.replaceChildren();
  const p = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const key = p.slice(0, 2).join("/");
  const id = p[2];
  const improvement = S.config.improvementEnabled;
  if (!p.length) home();
  else if (p[0] === "about") about();
  else if (p[0] === "exam-mode" && improvement) cleanup = examMode(main, ui, p[1]);
  else if (key === "manipulation/exams" && !id) examList("manipulation");
  else if (key === "manipulation/exams" && S.eById[id]?.type === "manipulation") examView(S.eById[id]);
  else if (key === "manipulation/questions" && !id) bankView();
  else if (key === "manipulation/questions" && S.qById[id]) bankQuestion(S.qById[id]);
  else if (key === "interpretation/exams" && !id) examList("interpretation");
  else if (key === "interpretation/exams" && S.eById[id]?.type === "interpretation") interpretationExam(S.eById[id]);
  else notFound();
  const section = ["about", "exam-mode"].includes(p[0]) ? p[0] : "";
  document.querySelectorAll(".site-header nav a").forEach((a) =>
    a.setAttribute("aria-current", a.getAttribute("href") === `#/${section}` ? "page" : "false"));
  window.scrollTo(0, 0);
  main.querySelector("h1")?.focus();
}

async function load() {
  const get = async (name) => {
    const r = await fetch(`data/${name}.json`, { cache: "no-cache" }); // revalidate, so the version is never stale
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
  document.getElementById("nav-exam-mode").hidden = !S.config.improvementEnabled;
  window.addEventListener("hashchange", route);
  route();
}

load();
