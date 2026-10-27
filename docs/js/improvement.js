// Improvement: answer check that recognises trap answers.
// app.js calls initImprovement after each question render when config.improvementEnabled is true.
// context = { question, exam, datasets, config, slot }. Data: docs/data/checks.json, built by
// scripts/build_checks.py. Every trap value there is computed from the raw data with the wrong method.

let checksPromise = null;
const drafts = new Map(); // answer typed so far, per exam and question, kept while the page is open

function loadChecks(version) {
  if (!checksPromise) {
    checksPromise = fetch(`data/checks.json?v=${encodeURIComponent(version || "")}`)
      .then((r) => (r.ok ? r.json() : { checks: {} }))
      .catch(() => ({ checks: {} }));
  }
  return checksPromise;
}

function addStyles(version) {
  if (document.getElementById("improvement-css")) return;
  const link = document.createElement("link");
  link.id = "improvement-css";
  link.rel = "stylesheet";
  link.href = `css/improvement.css?v=${encodeURIComponent(version || "")}`;
  document.head.appendChild(link);
}

function h(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) if (k !== null && k !== undefined) n.append(k);
  return n;
}

// ---------- parsing ----------

// All readings of a typed number: "1.194" may be 1194 or 1,194; "8" for a percentage may be 8 % or 0.08.
function numberCandidates(raw, kind) {
  let s = String(raw).trim();
  if (!s) return [];
  const pct = s.includes("%");
  let neg = /^\(.*\)$/.test(s.replace(/[^\d().,-]/g, ""));
  s = s.replace(/[^\d.,-]/g, "");
  if (s.startsWith("-")) { neg = true; s = s.slice(1); }
  if (!/\d/.test(s) || s.includes("-")) return [];
  const reads = new Set();
  const hasDot = s.includes("."), hasComma = s.includes(",");
  if (hasDot && hasComma) {
    const dec = s.lastIndexOf(".") > s.lastIndexOf(",") ? "." : ",";
    const other = dec === "." ? "," : ".";
    reads.add(s.split(other).join("").replace(dec, "."));
  } else if (hasDot || hasComma) {
    const sep = hasDot ? "." : ",";
    const parts = s.split(sep);
    const grouped = parts.length > 1 && parts.slice(1).every((p) => p.length === 3) && parts[0].length <= 3;
    if (grouped) reads.add(parts.join(""));
    if (parts.length === 2) reads.add(parts.join("."));
  } else reads.add(s);
  const out = [];
  for (const r of reads) {
    const v = Number(r) * (neg ? -1 : 1);
    if (!Number.isFinite(v)) continue;
    if (kind === "percent") {
      if (pct) out.push(v / 100);
      else { out.push(v / 100); if (Math.abs(v) <= 1) out.push(v); }
    } else out.push(v);
  }
  return out;
}

function textKey(s) {
  return String(s).trim().toLowerCase().replace(/^["'“”]+|["'“”.]+$/g, "").replace(/\s+/g, " ");
}

const pad = (n) => String(n).padStart(2, "0");

// Accepts 2011-12-07 16:38, 07.12.2011 16:38 and 12/7/2011 16:38. Returns { date, time } keys.
function dateKey(raw) {
  const s = String(raw).trim();
  const n = s.match(/\d+/g) || [];
  if (n.length < 3) return null;
  let y, m, d;
  if (n[0].length === 4) [y, m, d] = n;
  else if (s.includes("/")) [m, d, y] = n;
  else [d, m, y] = n;
  if (String(y).length !== 4) return null;
  const date = `${y}-${pad(m)}-${pad(d)}`;
  const time = n.length >= 5 ? `${pad(n[3])}:${pad(n[4])}` : null;
  return { date, time };
}

// ---------- matching ----------

function matches(check, raw, target) {
  if (check.kind === "number" || check.kind === "percent") {
    return numberCandidates(raw, check.kind).some((v) => Math.abs(v - Number(target)) <= check.tol + 1e-9);
  }
  if (check.kind === "datetime") {
    const a = dateKey(raw), b = dateKey(target);
    return !!a && !!b && a.date === b.date && a.time === b.time;
  }
  return textKey(raw) === textKey(target);
}

function parseable(check, raw) {
  if (!String(raw).trim()) return false;
  if (check.kind === "number" || check.kind === "percent") return numberCandidates(raw, check.kind).length > 0;
  if (check.kind === "datetime") return !!dateKey(raw);
  return true;
}

function show(check, v) {
  if (check.kind === "percent") return `${(Number(v) * 100).toLocaleString("en-GB", { maximumFractionDigits: 2 })}%`;
  if (check.kind === "number") return Number(v).toLocaleString("en-GB", { maximumFractionDigits: 4 });
  if (check.kind === "datetime") {
    const k = dateKey(v);
    const [y, m, d] = k.date.split("-");
    return `${d}.${m}.${y}${k.time ? " " + k.time : ""}`;
  }
  return String(v);
}

function grade(check, raw) {
  if (!parseable(check, raw)) return { state: "unreadable" };
  if (matches(check, raw, check.answer)) return { state: "correct" };
  for (const alt of check.also || []) if (matches(check, raw, alt)) return { state: "also" };
  const trap = (check.traps || []).find((t) => matches(check, raw, t.value));
  if (trap) return { state: "trap", trap };
  if (check.kind === "datetime") {
    const a = dateKey(raw), b = dateKey(check.answer);
    if (a && b && a.date === b.date && !a.time) return { state: "notime" };
  }
  return { state: "wrong" };
}

// ---------- view ----------

function trapList(check, intro) {
  if (!check.traps?.length) return null;
  return h("div", { class: "ic-traps" },
    h("p", { class: "ic-small", text: intro }),
    check.traps.map((t) => h("p", {},
      h("strong", { text: `${show(check, t.value)} (${t.category.toLowerCase()}). ` }), t.why)));
}

function answerBlock(check) {
  const tol = check.tol > 0 ? ` Accepted within ${show(check, check.tol).replace(/^0(?=[.,]\d)/, "0")} of this.` : "";
  return h("div", { class: "ic-answer" },
    h("p", {}, h("strong", { text: "Expected answer: " }), show(check, check.answer),
      check.also?.length ? ` (${check.also.map((a) => show(check, a)).join(", ")} also fits the wording)` : "",
      check.kind === "percent" || check.kind === "number" ? h("span", { class: "ic-small", text: tol }) : null),
    check.note ? h("p", { class: "ic-small", text: check.note }) : null,
    trapList(check, "Wrong answers that look right on this question:"));
}

function feedback(check, result, raw) {
  const kids = [];
  let cls = "ic-wrong";
  switch (result.state) {
    case "correct":
      cls = "ic-right";
      kids.push(h("p", {}, h("strong", { text: "Correct." }),
        check.traps?.length ? " Now check you could explain why the trap below is wrong." : ""));
      kids.push(trapList(check, "The trap on this question:"));
      break;
    case "also":
      cls = "ic-right";
      kids.push(h("p", {}, h("strong", { text: "Defensible. " }), check.note || ""));
      break;
    case "trap":
      kids.push(h("p", {}, h("strong", { text: `Not quite. ${show(check, result.trap.value)} is a known trap: ` }),
        result.trap.category.toLowerCase() + "."));
      kids.push(h("p", { text: result.trap.why }));
      kids.push(h("p", { class: "ic-small", text: "Fix the method and try again, or show the answer." }));
      break;
    case "notime":
      kids.push(h("p", {}, h("strong", { text: "Right date, but the question asks for the time as well." })));
      break;
    case "unreadable":
      kids.push(h("p", { text: check.kind === "number" || check.kind === "percent"
        ? "Enter one number, for example 1194, 1.194 or 12.5%." : "Enter one value." }));
      return { cls: "ic-note", kids };
    default:
      kids.push(h("p", {}, h("strong", { text: "Not the expected answer. " }),
        "It does not match a known trap either. Check the filter (which rows are in), what one row is, and the rounding."));
  }
  return { cls, kids };
}

export function initImprovement(context) {
  const { question, exam, config, slot } = context;
  if (!question || !slot) return;
  addStyles(config?.version);
  const key = `${exam?.id || "bank"}:${question.id}`;
  loadChecks(config?.version).then((data) => {
    const check = data.checks?.[question.id];
    if (!check || !slot.isConnected) return;
    const id = `ic-input-${question.id}`;
    const input = h("input", { id, type: "text", autocomplete: "off", spellcheck: "false", inputmode: "text" });
    input.value = drafts.get(key) || "";
    input.addEventListener("input", () => drafts.set(key, input.value));
    const out = h("div", { class: "ic-out", "aria-live": "polite" });
    const reveal = h("button", { type: "button", class: "secondary", hidden: true, text: "Show answer" });
    const go = h("button", { type: "button", text: "Check" });
    const run = () => {
      const r = grade(check, input.value);
      const f = feedback(check, r, input.value);
      out.className = `ic-out ${f.cls}`;
      out.replaceChildren(...f.kids.filter(Boolean));
      reveal.hidden = r.state === "correct" || r.state === "also" || r.state === "unreadable";
    };
    go.addEventListener("click", run);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") run(); });
    reveal.addEventListener("click", () => {
      out.className = "ic-out ic-note";
      out.replaceChildren(answerBlock(check));
      reveal.hidden = true;
    });
    slot.replaceChildren(h("div", { class: "ic" },
      h("label", { for: id, text: "Check your answer" }),
      h("div", { class: "ic-row" }, input, go, reveal),
      h("p", { class: "ic-small", text: check.traps?.length
        ? "This question has a wrong answer that looks right. The check tells you if you hit it, and why."
        : "Compared with the answer computed from the data." }),
      out));
    slot.hidden = false;
  });
}
export { grade, numberCandidates, dateKey }; // used by tests/check_answers.mjs
