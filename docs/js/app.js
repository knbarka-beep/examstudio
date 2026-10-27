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

function heading(text) {
  return el("h1", { tabindex: "-1" }, text);
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
  const box = el("section", { class: "timer", "aria-label": "Timer" },
    el("p", { class: "remaining" }, remainingOut, " remaining"),
    el("p", { class: "muted" }, "Elapsed ", elapsedOut),
    status,
    el("div", { class: "buttons" }, start, pause, reset));

  const fmt = (ms) => {
    const s = Math.round(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };
  const now = () => Math.min(total, elapsed + (startedAt ? Date.now() - startedAt : 0));
  const draw = () => {
    const e = now();
    remainingOut.textContent = fmt(total - e);
    elapsedOut.textContent = fmt(e);
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
  stopTimer = halt;
  draw();
  return box;
}

// ---------- question panels ----------

function datasetReference(q) {
  const req = q.required_objects || {};
  const has = (list, x) => (list || []).includes(x);
  const items = q.dataset_ids.map((id) => {
    const d = S.dsById[id];
    const parts = [el("h4", {}, `${d.label} (${d.file})`)];
    if (d.sheets) {
      const sheets = d.sheets.filter((s) => !req.sheets?.length || has(req.sheets, s.name));
      for (const s of sheets) {
        parts.push(el("p", {}, "Sheet ", el("code", {}, s.name), `, headers in row ${s.header_row}, ${num(s.rows, 0)} data rows:`),
          el("ul", { class: "fields" }, s.headers.filter((h) => h !== null).map((h) =>
            el("li", {}, has(req.headers, h) ? el("strong", {}, h) : h))));
      }
    } else if (d.tables) {
      const tables = d.tables.filter((t) => !req.tables?.length || has(req.tables, t.name));
      for (const t of tables) {
        parts.push(el("p", {}, "Table ", el("code", {}, t.name), `, ${num(t.rows, 0)} rows:`),
          el("ul", { class: "fields" }, t.columns.map((c) =>
            el("li", {}, has(req.columns, `${t.name}.${c.split(" ")[0]}`) ? el("strong", {}, c) : c))));
      }
    } else {
      parts.push(el("p", {}, `Text file, ${d.delimiter} delimited, ${d.encoding}, ${num(d.rows, 0)} data rows. Headers:`),
        el("ul", { class: "fields" }, (d.headers || []).map((h) =>
          el("li", {}, has(req.headers, h) ? el("strong", {}, h) : h))));
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

function questionPanel(q, exam, nav) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const panel = el("article", { class: exam ? "sheet tabbed" : "sheet" },
    el("h2", { class: "meta" }, `${q.id}, ${q.case}, about ${num(q.estimated_minutes, 1)} min`),
    el("p", { class: "prompt" }, q.prompt),
    slot,
    q.expected_answer_hint ? el("p", {}, `Answer format: ${q.expected_answer_hint}`) : null,
    datasetReference(q),
    S.config.showReferenceSolutions && q.reference ? referenceSolution(q.reference) : null,
    el("div", { class: "sheet-foot" }, issueLink(q.id, exam), nav));
  return { panel, slot };
}

function equation(m) {
  const dep = m.formula.split("~")[0].trim();
  const terms = Object.entries(m.coefficients).map(([term, c]) => {
    if (term === "Intercept") return num(c.coef, 4);
    return `${c.coef < 0 ? "- " : "+ "}${num(Math.abs(c.coef), 4)} x ${term.replace(":", " x ")}`;
  });
  return `${dep} = ${terms.join(" ")}`;
}

function modelBlock(m) {
  const vars = Object.entries(m.variables);
  const dummies = Object.entries(m.dummy_coding || {});
  const cols = (names, numeric) => el("thead", {}, el("tr", {}, names.map((h, i) =>
    el("th", { scope: "col", class: i >= numeric ? "num" : null }, h))));
  return el("div", { class: "model" },
    el("h2", {}, `Model ${m.id}: `, el("code", {}, m.formula)),
    el("p", {}, `OLS, n = ${m.n}, R squared = ${m.r_squared}, adjusted R squared = ${m.adj_r_squared}.`),
    el("h3", {}, "Variables"),
    el("div", { class: "table-wrap" }, el("table", { class: "stats" },
      cols(["Variable", "Definition", "Unit", "Observed range"], 3),
      el("tbody", {}, vars.map(([name, v]) => el("tr", {},
        el("th", { scope: "row" }, name), el("td", {}, v.definition), el("td", {}, v.unit || ""),
        el("td", { class: "num" }, `${num(v.min)} to ${num(v.max)}`)))))),
    dummies.length ? el("ul", {}, dummies.map(([name, codes]) =>
      el("li", {}, el("code", {}, name), ": " + Object.entries(codes).map(([k, v]) => `${k} = ${v}`).join("; ")))) : null,
    el("h3", {}, "Regression output"),
    el("div", { class: "table-wrap" }, el("table", { class: "stats" },
      cols(["Parameter", "Term", "Estimate", "Std. error", "p-value"], 2),
      el("tbody", {}, Object.entries(m.coefficients).map(([term, c], i) => el("tr", {},
        el("td", {}, `b${i}`), el("th", { scope: "row" }, term), el("td", { class: "num" }, num(c.coef, 4)),
        el("td", { class: "num" }, num(c.se, 4)), el("td", { class: "num" }, pval(c.p))))))),
    el("p", { class: "equation" }, equation(m)));
}

function interpretationPanel(q, exam) {
  const slot = el("section", { id: "improvement-slot", hidden: true });
  const panel = el("article", { class: "sheet tabbed" },
    modelBlock(S.mById[q.model_id]),
    el("div", { class: "question-part" },
      el("h2", { class: "meta" }, `${q.id}, ${q.kind} question`),
      el("p", { class: "prompt" }, q.prompt),
      slot,
      el("details", { class: "reference" }, el("summary", {}, "Show answer"),
        el("div", { class: "answer" }, el("p", {}, q.worked_answer)))),
    el("div", { class: "sheet-foot" }, issueLink(q.id, exam)));
  return { panel, slot };
}

// ---------- views ----------

function homePart(type, title, about, samples, links) {
  const exams = S.exams.filter((e) => e.type === type);
  const base = `#/${type}/exams/`;
  return el("section", { class: "home-part" },
    el("h2", {}, title),
    el("p", {}, `${exams[0].question_ids.length} questions, `, el("span", { class: "mono" }, `${exams[0].time_limit_minutes}:00`)),
    el("p", {}, about),
    el("p", { class: "muted" }, "One question from the bank:"),
    el("blockquote", {}, el("p", {}, pick(samples).prompt)),
    el("div", { class: "buttons" },
      el("button", { type: "button", onclick: () => { location.hash = base + pick(exams, lastExam).id; } }, "Start a random exam")),
    el("ul", { class: "links" }, el("li", {}, el("a", { href: base }, `Browse ${exams.length} exams`)), links));
}

function home() {
  main.append(
    heading("Practice for Data Analytics in Accounting"),
    el("p", { class: "knut" }, "[[KNUT: one or two sentences on what the oral exam asks for, in my words]]"),
    el("div", { class: "home-parts" },
      homePart("manipulation", "Data manipulation", "Excel and SQL on two files from the course cases.", S.questions,
        el("li", {}, el("a", { href: "#/manipulation/questions" }, `Question bank (${S.questions.length})`))),
      homePart("interpretation", "Data interpretation", "Regression output from the restaurant case.", S.interp, null)));
}

function examList(type) {
  const manip = type === "manipulation";
  const exams = S.exams.filter((e) => e.type === type);
  const base = manip ? "#/manipulation/exams/" : "#/interpretation/exams/";
  main.append(
    heading(manip ? "Data manipulation exams" : "Data interpretation exams"),
    el("p", {}, manip
      ? `${exams.length} exams. Each has five questions and two data files, with 8 minutes in total.`
      : `${exams.length} exams. Each has four questions on regression output, with 5 minutes in total.`),
    el("p", {}, el("button", { type: "button", onclick: () => { location.hash = base + pick(exams, lastExam).id; } }, "Pick an exam for me")),
    el("div", { class: "table-wrap" }, el("table", { class: "banded" },
      el("thead", {}, el("tr", {}, (manip ? ["Exam", "Spreadsheet file", "Database", "Time"] : ["Exam", "Models", "Time"])
        .map((h) => el("th", { scope: "col" }, h)))),
      el("tbody", {}, exams.map((e) => el("tr", {},
        el("th", { scope: "row" }, el("a", { href: base + e.id }, e.id)),
        manip ? e.files.map((f) => el("td", {}, S.dsById[f].file))
          : el("td", {}, e.question_ids.map((id) => S.iById[id].model_id).join(", ")),
        el("td", {}, `${e.time_limit_minutes} min`)))))));
}

function examView(e) {
  lastExam = e.id;
  const qs = e.question_ids.map((id) => S.qById[id]);
  let active = 0;
  const host = el("div");
  const nav = el("ol", { class: "sheet-tabs" });
  const prev = el("button", { type: "button", class: "secondary" }, "Previous");
  const next = el("button", { type: "button", class: "secondary" }, "Next");
  const show = (i) => {
    active = i;
    const { panel, slot } = questionPanel(qs[i], e, el("div", { class: "buttons" }, prev, next));
    host.replaceChildren(panel);
    nav.querySelectorAll("button").forEach((b, j) => b.setAttribute("aria-current", j === i ? "true" : "false"));
    prev.disabled = i === 0;
    next.disabled = i === qs.length - 1;
    runImprovement(qs[i], e, slot);
  };
  qs.forEach((q, i) => nav.append(el("li", {}, el("button", { type: "button", onclick: () => show(i) },
    `${i + 1} ${q.subject}`))));
  prev.addEventListener("click", () => show(active - 1));
  next.addEventListener("click", () => show(active + 1));
  main.append(
    el("p", { class: "crumb" }, el("a", { href: "#/manipulation/exams" }, "All manipulation exams")),
    ...examHeading(e, qs.length, ""),
    downloads(e.files),
    timer(e.time_limit_minutes),
    el("nav", { "aria-label": "Questions in this exam" }, nav),
    host);
  show(0);
}

function examHeading(e, n, about) {
  const h = heading(`Exam ${e.id}`);
  h.classList.add("compact");
  return [h, el("p", {}, `${n} questions, ${e.time_limit_minutes} minutes${about}. `,
    `Open ${e.files.length > 1 ? "both files" : "the file"} before you start the clock.`)];
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
  const results = el("div", { "aria-live": "polite" });
  const select = (key, label, values) => {
    const id = `f-${key}`;
    return el("div", { class: "field" }, el("label", { for: id }, label),
      el("select", { id, onchange: (ev) => { bank[key] = ev.target.value; bank.page = 1; draw(); } },
        el("option", { value: "" }, "All"),
        values.map((v) => el("option", { value: v, selected: bank[key] === v }, v))));
  };
  const draw = () => {
    const list = filtered();
    const pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    bank.page = Math.min(bank.page, pages);
    const shown = list.slice((bank.page - 1) * PAGE_SIZE, bank.page * PAGE_SIZE);
    const go = (p) => { bank.page = p; draw(); results.querySelector("h2").focus(); };
    results.replaceChildren(
      el("h2", { tabindex: "-1" }, `${list.length} questions`),
      el("ul", { class: "qlist" }, shown.map((q) => el("li", {},
        el("a", { href: `#/manipulation/questions/${q.id}` }, q.id),
        el("p", {}, q.prompt),
        el("p", { class: "muted" }, `${q.case}, ${q.skills.join(", ")}, about ${num(q.estimated_minutes, 1)} min`)))),
      el("div", { class: "pager" },
        el("button", { type: "button", class: "secondary", disabled: bank.page === 1, onclick: () => go(bank.page - 1) }, "Previous"),
        el("p", {}, `Page ${bank.page} of ${pages}`),
        el("button", { type: "button", class: "secondary", disabled: bank.page === pages, onclick: () => go(bank.page + 1) }, "Next")));
  };
  main.append(
    heading("Question bank"),
    el("p", {}, "All validated data manipulation questions. Exams draw from the required ones; questions marked optional in the cases are only here."),
    el("form", { class: "filters", onsubmit: (ev) => ev.preventDefault() },
      select("subject", "Subject", uniq((q) => [q.subject])),
      select("case", "Case", uniq((q) => [q.case])),
      select("source", "Source file", uniq((q) => [q.source_file])),
      select("skill", "Skill", uniq((q) => q.skills)),
      el("div", { class: "field" }, el("label", { for: "f-text" }, "Search"),
        el("input", { id: "f-text", type: "search", value: bank.text,
          oninput: (ev) => { bank.text = ev.target.value; bank.page = 1; draw(); } }))),
    results);
  draw();
}

function bankQuestion(q) {
  const list = filtered();
  const i = list.indexOf(q);
  const { panel, slot } = questionPanel(q, null, i >= 0 ? el("div", { class: "buttons" },
    i > 0 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i - 1].id}` }, "Previous") : null,
    i < list.length - 1 ? el("a", { class: "button secondary", href: `#/manipulation/questions/${list[i + 1].id}` }, "Next") : null) : null);
  const h = heading(`${q.id}${q.optional ? " (optional)" : ""}`);
  h.classList.add("compact");
  main.append(
    el("p", { class: "crumb" }, el("a", { href: "#/manipulation/questions" }, "Question bank")),
    h,
    downloads(q.dataset_ids),
    panel);
  runImprovement(q, null, slot);
}

function interpretationExam(e) {
  lastExam = e.id;
  const qs = e.question_ids.map((id) => S.iById[id]);
  const tabs = qs.map((q, i) => el("button", { type: "button", role: "tab", id: `tab-${i}`, "aria-controls": "tabpanel" }, `Question ${i + 1}`));
  const tabpanel = el("div", { role: "tabpanel", id: "tabpanel", tabindex: "0", class: "sheet-host" });
  const show = (i, focus) => {
    tabs.forEach((t, j) => { t.setAttribute("aria-selected", j === i ? "true" : "false"); t.tabIndex = j === i ? 0 : -1; });
    tabpanel.setAttribute("aria-labelledby", `tab-${i}`);
    const { panel, slot } = interpretationPanel(qs[i], e);
    tabpanel.replaceChildren(panel);
    if (focus) tabs[i].focus();
    runImprovement(qs[i], e, slot);
  };
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => show(i));
    t.addEventListener("keydown", (ev) => {
      const n = tabs.length;
      const to = { ArrowRight: (i + 1) % n, ArrowLeft: (i - 1 + n) % n, Home: 0, End: n - 1 }[ev.key];
      if (to !== undefined) { ev.preventDefault(); show(to, true); }
    });
  });
  main.append(
    el("p", { class: "crumb" }, el("a", { href: "#/interpretation/exams" }, "All interpretation exams")),
    ...examHeading(e, qs.length, " on the restaurant data"),
    downloads(e.files),
    timer(e.time_limit_minutes),
    el("div", { role: "tablist", "aria-label": "Questions", class: "sheet-tabs" }, tabs),
    tabpanel);
  show(0);
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
    document.getElementById("version").textContent = `Data version ${S.version}.`;
  } catch (err) {
    main.replaceChildren(heading("The data could not be loaded"),
      el("p", {}, `${err.message}. If you opened the file directly, run a local server: py -m http.server 8000 --directory docs`));
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}

load();
