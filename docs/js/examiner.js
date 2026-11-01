// Exam mode: one task at a time with a rules-based examiner. No AI model, nothing stored.
// Built on the answer check (improvement.js): when the answer box or a number said in the transcript matches a
// computed trap answer in checks.json, the examiner asks the probe for that trap's tag (probes.json) instead of
// marking the answer wrong. Speech uses the browser's Web Speech API when it is there; the text box always works.
// app.js only calls examMode when config.improvementEnabled is true.

import { grade, loadChecks, addStyles, show, answerBlock } from "./improvement.js?v=01.11.2026-2856ff5";

// Strictness presets. Times in milliseconds.
//   probes: [fewest, most] follow-up questions per task (pushbacks are not counted)
//   pauseMs: silence that counts as a pause in the answer
//   talkMs: continuous talking after which the examiner may cut in (null = never)
//   triggerMs: how soon after a trigger term the examiner asks (null = only at a pause)
//   midSentence: may ask while the student is still talking
//   hints: hints allowed per task; thinMax: pushbacks on thin answers per task
//   challenge: asks "Are you sure? Convince me." about once per task; hardStop: ends the task at zero
const PRESETS = {
  supportive: { label: "Supportive", probes: [1, 2], pauseMs: 4000, talkMs: null, triggerMs: null, midSentence: false,
    hints: Infinity, thinMax: 1, gentle: true, challenge: false, hardStop: false },
  standard: { label: "Standard", probes: [3, 4], pauseMs: 4000, talkMs: 75000, triggerMs: 800, midSentence: false,
    hints: 1, thinMax: 1, gentle: false, challenge: false, hardStop: true },
  strict: { label: "Strict", probes: [4, 6], pauseMs: 3000, talkMs: 45000, triggerMs: 1500, midSentence: true,
    hints: 0, thinMax: 2, gentle: false, challenge: true, hardStop: true },
};
const MIN_GAP_MS = 20000; // never two examiner interruptions within 20 seconds, in any mode
const ANSWER_PAUSE_MS = 2500; // a pause this long after an answer to a probe ends that answer
const WARN_MS = 120000;

// Answer quality heuristic: an answer is "thin" when it has fewer than 15 words, or when it contains none of the
// reasoning words below, so it says what was done but not why.
const REASON = /\b(because|so|since|otherwise|which means|the reason)\b/i;
const words = (s) => (s.match(/\S+/g) || []).length;
const isThin = (s) => words(s) < 15 || !REASON.test(s);

const TOPICS = { Excel: "Excel", SQL: "SQL", Regression: "Regression interpretation", Mixed: "Mixed" };
const PRIORITY = { pushback: 0, trap: 1, challenge: 2, trigger: 3, question: 4, generic: 5 };

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const TTS = "speechSynthesis" in window;

// Settings and weak spots live only while the page is open.
const settings = { topic: "Mixed", strictness: "standard", minutes: 8, voice: true };
const session = { tagCounts: new Map(), done: new Set() };
let probesPromise = null;

const fmt = (ms) => {
  const s = Math.max(0, Math.round(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

function pickVoice() {
  const voices = TTS ? speechSynthesis.getVoices() : [];
  return voices.find((v) => v.lang === "en-GB") || voices.find((v) => /^en[-_]/i.test(v.lang)) || null;
}

export function examMode(main, ui, taskId) {
  const { S, el } = ui;
  let stop = () => {};
  const cleanup = () => stop();
  addStyles(S.config.version);
  if (TTS) speechSynthesis.getVoices(); // starts loading the voice list
  if (!probesPromise) probesPromise = fetch(`data/probes.json?v=${encodeURIComponent(S.version)}`).then((r) => r.json());
  Promise.all([probesPromise, loadChecks(S.config.version)]).then(([bank, checks]) => {
    const B = { ...bank, checks: checks.checks || {} };
    const fixed = ui.S.qById[taskId] || ui.S.iById[taskId] || null; // #/exam-mode/Q048 sets the first task
    setup(main, ui, B, (s) => { stop = s; }, null, fixed);
  }).catch((err) => main.append(el("p", {}, `Exam mode could not load its data: ${err.message}`)));
  return cleanup;
}

// ---------- which probes and questions belong together ----------

function subjectOf(q) {
  return q.model_id ? "Regression" : q.subject;
}

function topicFits(p, subject) {
  return p.topic === "any" || p.topic === subject;
}

// Question probes tied to this question by id, skill, interpretation kind or number of tables.
function questionProbes(B, q) {
  const subject = subjectOf(q);
  return B.probes.filter((p) => p.kind === "question" && topicFits(p, subject) && (
    p.questions?.includes(q.id) ||
    (p.kinds && p.kinds.includes(q.kind)) ||
    (p.skills && q.skills && p.skills.some((s) => q.skills.includes(s)) &&
      (!p.min_tables || (q.required_objects?.tables || []).length >= p.min_tables))));
}

function tagsOf(B, q) {
  const tags = new Set((B.checks[q.id]?.traps || []).map((t) => t.tag));
  for (const p of questionProbes(B, q)) if (p.tag) tags.add(p.tag);
  return tags;
}

function pool(S, topic) {
  if (topic === "Regression") return S.interp;
  if (topic === "Mixed") return [...S.questions, ...S.interp];
  return S.questions.filter((q) => q.subject === topic);
}

function pickTask(ui, B, topic, tag) {
  let list = pool(ui.S, topic);
  if (tag) {
    const tagged = list.filter((q) => tagsOf(B, q).has(tag));
    // Prefer questions with a computed trap of this tag, then any question tied to it.
    const trapped = tagged.filter((q) => (B.checks[q.id]?.traps || []).some((t) => t.tag === tag));
    list = trapped.length ? trapped : tagged.length ? tagged : list;
  }
  const fresh = list.filter((q) => !session.done.has(q.id));
  return ui.pick(fresh.length ? fresh : list);
}

// ---------- setup screen ----------

function choice(el, name, legend, options, value, help) {
  return el("fieldset", {}, el("legend", {}, legend),
    el("div", { class: "segmented" }, Object.entries(options).map(([v, text]) =>
      el("label", {}, el("input", { type: "radio", name, value: v, checked: String(value) === v }), el("span", {}, text)))),
    help ? el("p", { class: "field-help" }, help) : null);
}

async function micCheck() {
  if (!SR) return { ok: false, why: "This browser has no speech recognition (Firefox and some Safari versions do not). You can answer in the text box instead." };
  if (!navigator.mediaDevices?.getUserMedia) return { ok: false, why: "This page cannot reach a microphone here. You can answer in the text box instead." };
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    return { ok: true };
  } catch (err) {
    return { ok: false, why: `The microphone is not available (${err.name}). You can answer in the text box instead.` };
  }
}

function setup(main, ui, B, setStop, notice, fixed) {
  const { el } = ui;
  setStop(() => {});
  const status = el("p", { class: "field-help", "aria-live": "polite" }, notice || "");
  const form = el("form", { class: "card stack setup" },
    fixed ? el("p", {}, `First task: ${fixed.id}. `, el("a", { href: "#/exam-mode" }, "Pick at random instead")) : null,
    choice(el, "topic", "Topic", TOPICS, settings.topic),
    choice(el, "strictness", "Examiner", { supportive: "Supportive", standard: "Standard", strict: "Strict" }, settings.strictness,
      "Supportive waits for you to pause and gives hints. Standard may cut in after a key term or a long stretch of talking, and allows one hint. Strict cuts in within seconds, even mid-sentence, gives no hints and may challenge a right answer."),
    choice(el, "minutes", "Time per task", { 8: "8 minutes", 10: "10 minutes" }, settings.minutes),
    choice(el, "voice", "Voice", { on: "On", off: "Off, text only" }, settings.voice ? "on" : "off",
      "With voice on, the examiner reads aloud and you answer by microphone. In Chrome and Edge, the browser sends microphone audio to its vendor's speech service (Google or Microsoft), so do not say anything confidential."),
    el("div", { class: "buttons" }, el("button", { type: "submit", class: "big" }, "Start exam")),
    status);
  let checked = false;
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = new FormData(form);
    Object.assign(settings, { topic: f.get("topic"), strictness: f.get("strictness"), minutes: Number(f.get("minutes")), voice: f.get("voice") === "on" });
    let listen = false;
    if (settings.voice) {
      status.textContent = "Checking the microphone...";
      const mic = await micCheck();
      listen = mic.ok;
      if (!mic.ok && !checked) {
        checked = true;
        status.textContent = mic.why;
        form.querySelector("button[type=submit]").textContent = "Start with the text box";
        return;
      }
    }
    runTask(main, ui, B, setStop, fixed || pickTask(ui, B, settings.topic), { listen, speak: settings.voice && TTS });
  });
  main.replaceChildren(
    ui.pageHead("Exam mode", { lead: "One task at a time against the clock, with an examiner who asks follow-up questions while you work and explain." }),
    form);
  main.querySelector("h1")?.focus();
}

// ---------- the task ----------

function runTask(main, ui, B, setStop, q, media) {
  const { S, el } = ui;
  const P = PRESETS[settings.strictness];
  const subject = subjectOf(q);
  const check = B.checks[q.id] || null;
  const total = settings.minutes * 60000;
  const t0 = Date.now();
  const T = {
    q, lines: [], asked: [], askedIds: new Set(), queue: [], thin: [], trapHits: [], answers: [], hints: [],
    pushbacks: 0, challenged: false, lastExaminer: -Infinity, lastUser: null, talkStart: null, said: 0, awaiting: null,
    ended: false, speaking: false, media, minutes: settings.minutes, strictness: settings.strictness, topic: settings.topic,
  };
  session.done.add(q.id);
  const at = () => Date.now() - t0;

  // --- transcript panel ---
  const list = el("ol", { class: "transcript", "aria-live": "polite" });
  const interim = el("p", { class: "interim", "aria-hidden": "true" });
  const mic = el("p", { class: "mic small" });
  const typed = el("textarea", { rows: 3, placeholder: "Type what you would say", "aria-label": "Type your answer to the examiner" });
  const send = el("button", { type: "button", class: "secondary" }, "Send");
  const hint = el("button", { type: "button", class: "secondary", hidden: P.hints === 0 }, "Hint");
  const done = el("button", { type: "button" }, "Done, I'm finished");

  const addLine = (who, text, extra = {}) => {
    const line = { t: at(), who, text, ...extra };
    T.lines.push(line);
    list.append(el("li", { class: who }, el("span", { class: "ts" }, fmt(line.t)),
      el("span", { class: "who" }, who === "examiner" ? "Examiner" : who === "hint" ? "Hint" : who === "system" ? "Note" : "You"),
      el("span", { class: "text" }, text)));
    list.scrollTop = list.scrollHeight;
    return line;
  };

  // --- speech out ---
  let rec = null;
  const voice = pickVoice();
  const speak = (text) => new Promise((resolve) => {
    if (!media.speak) return resolve();
    T.speaking = true;
    try { rec?.abort(); } catch { /* not running */ }
    const u = new SpeechSynthesisUtterance(text);
    if (voice) u.voice = voice;
    u.lang = voice?.lang || "en-GB";
    u.rate = 1;
    const end = () => {
      T.speaking = false;
      T.lastExaminer = Date.now();
      if (!T.ended) startRec();
      resolve();
    };
    u.onend = end;
    u.onerror = end;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  });

  // --- speech in ---
  const startRec = () => {
    if (!rec || T.ended || T.speaking) return;
    try { rec.start(); } catch { /* already running; onend restarts it */ }
  };
  if (media.listen) {
    rec = new SR();
    rec.lang = "en-GB";
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e) => {
      let part = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) userSaid(r[0].transcript.trim());
        else part += r[0].transcript;
      }
      interim.textContent = part;
      if (part.trim()) heard(part, false);
    };
    rec.onstart = () => { mic.textContent = "Listening. Talk while you work."; };
    rec.onend = () => { if (!T.ended && !T.speaking) setTimeout(startRec, 250); }; // the browser ends recognition now and then
    rec.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed" || e.error === "audio-capture") {
        rec = null;
        mic.textContent = "The microphone stopped working. Use the text box.";
        addLine("system", `Speech recognition stopped (${e.error}). Carry on in the text box.`);
      }
    };
  } else {
    mic.textContent = media.speak ? "The examiner speaks; you answer in the text box." : "Text only. Answer in the text box.";
  }

  // --- what the student says or types ---
  const heard = (text, final) => {
    const now = Date.now();
    if (!T.lastUser || now - T.lastUser > 3000) T.talkStart = now;
    T.lastUser = now;
    if (!final && P.midSentence) scanTriggers(text); // Strict reacts to terms before the sentence is finished
  };
  function userSaid(text) {
    if (!text) return;
    heard(text, true);
    interim.textContent = "";
    addLine("you", text);
    T.said += words(text);
    scanTriggers(text);
    scanNumbers(text, "transcript");
  }
  send.addEventListener("click", () => {
    const text = typed.value.trim();
    if (!text) return;
    typed.value = "";
    userSaid(text);
  });
  typed.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send.click(); } });

  // --- the queue of things the examiner wants to say ---
  const enqueue = (item) => {
    if (item.probe && (T.askedIds.has(item.probe.id) || T.queue.some((x) => x.probe?.id === item.probe.id))) return;
    T.queue.push({ at: Date.now(), ...item });
    T.queue.sort((a, b) => PRIORITY[a.kind] - PRIORITY[b.kind] || a.at - b.at);
  };
  const unasked = (filter) => B.probes.find((p) => filter(p) && topicFits(p, subject) && !T.askedIds.has(p.id) &&
    (!p.questions || p.questions.includes(q.id)));

  function scanTriggers(text) {
    for (const p of B.probes) {
      if (p.kind !== "trigger" || !topicFits(p, subject) || T.askedIds.has(p.id)) continue;
      if (p.triggers.some((rx) => new RegExp(rx, "i").test(text))) enqueue({ kind: "trigger", probe: p });
    }
  }

  const trapHit = (trap, value, source) => {
    T.trapHits.push({ tag: trap.tag, category: trap.category, value, source, t: at() });
    const p = unasked((x) => x.kind === "trap" && x.tag === trap.tag);
    if (p) enqueue({ kind: "trap", probe: p });
  };

  // Numbers said or typed in the transcript are checked against the computed traps too.
  function scanNumbers(text, source) {
    if (!check?.traps?.length || !["number", "percent"].includes(check.kind)) return;
    for (const token of text.match(/\(?-?\d[\d.,]*%?\)?/g) || []) {
      const r = grade(check, token);
      if (r.state === "trap" && !T.trapHits.some((h) => h.value === r.trap.value)) trapHit(r.trap, r.trap.value, source);
    }
  }

  // --- the answer box ---
  const answerInput = el("input", { type: "text", autocomplete: "off", spellcheck: "false", id: "exam-answer" });
  const answerBtn = el("button", { type: "button" }, "Submit answer");
  const answerNote = el("p", { class: "ic-small", "aria-live": "polite" },
    check ? "The examiner reacts to your answer; whether it is right is shown in the debrief."
      : "There is no single-value check for this task. Your answer is shown next to the worked answer in the debrief.");
  answerBtn.addEventListener("click", () => {
    const raw = answerInput.value.trim();
    if (!raw) return;
    const r = check ? grade(check, raw) : { state: "unchecked" };
    T.answers.push({ raw, state: r.state, trap: r.trap || null, t: at() });
    answerNote.textContent = `Answer noted at ${fmt(at())}: ${raw}`;
    T.lastUser = Date.now();
    T.said += 1;
    scanTriggers(raw);
    if (r.state === "trap") trapHit(r.trap, r.trap.value, "answer box");
    else if ((r.state === "correct" || r.state === "also") && P.challenge && !T.challenged) {
      T.challenged = true;
      enqueue({ kind: "challenge", text: B.lines.challenge });
    } else if (r.state === "wrong") {
      const p = unasked((x) => x.id === "W-check");
      if (p) enqueue({ kind: "generic", probe: p });
    }
  });
  answerInput.addEventListener("keydown", (e) => { if (e.key === "Enter") answerBtn.click(); });

  // --- hints ---
  const hintText = () => {
    const tag = [...tagsOf(B, q)][0];
    if (tag) return B.tags[tag].hint;
    if (q.expected_answer_hint) return `Answer format: ${q.expected_answer_hint}`;
    return subject === "Regression" ? "Write the equation out with the numbers in before you compute or interpret."
      : "Say what one row of your result represents, then check your filter against the question.";
  };
  hint.addEventListener("click", () => {
    T.hints.push(at());
    addLine("hint", hintText());
    if (T.hints.length >= P.hints) hint.disabled = true;
  });

  // --- asking ---
  async function ask(item) {
    T.queue = T.queue.filter((x) => x !== item);
    const text = item.text || item.probe.text;
    if (item.probe) { T.asked.push({ probe: item.probe, why: item.kind, t: at() }); T.askedIds.add(item.probe.id); }
    T.lastExaminer = Date.now();
    T.awaiting = { item, from: T.lines.length + 1, assessed: false };
    T.said = 0;
    T.talkStart = null;
    addLine("examiner", text, { kind: item.kind, probe: item.probe?.id || null });
    await speak(text);
  }

  function assess() {
    const a = T.awaiting;
    a.assessed = true;
    const answer = T.lines.slice(a.from).filter((l) => l.who === "you").map((l) => l.text).join(" ");
    if (!answer) return;
    const thin = isThin(answer);
    const asked = a.item.probe || null;
    if (thin) {
      T.thin.push({ question: a.item.text || asked?.text, answer, tag: asked?.tag || null });
      if (asked?.tag) session.tagCounts.set(asked.tag, (session.tagCounts.get(asked.tag) || 0) + 1);
      if (T.pushbacks < P.thinMax) {
        T.pushbacks++;
        enqueue({ kind: "pushback", text: P.gentle ? B.lines.thin_gentle : asked?.pushback || B.lines.thin_default, of: a });
      }
    } else if (P.challenge && !T.challenged && !check) {
      // Without an answer box check, Strict challenges the first well-argued answer instead.
      T.challenged = true;
      enqueue({ kind: "challenge", text: B.lines.challenge });
    }
  }

  // The examiner's clock: decides every half second whether to say something.
  function tick() {
    if (T.ended) return;
    const now = Date.now();
    const elapsed = at();
    drawClock(elapsed);
    if (P.hardStop && elapsed >= total) return finish("time");
    if (T.speaking) return;
    const silent = T.lastUser ? now - T.lastUser : Infinity;
    if (T.awaiting && !T.awaiting.assessed && T.said > 0 && silent >= ANSWER_PAUSE_MS) assess();
    if (now - T.lastExaminer < MIN_GAP_MS) return;

    // A pushback is dropped if the student has since said enough to make the answer full.
    T.queue = T.queue.filter((x) => x.kind !== "pushback" || isThin(T.lines.slice(x.of.from).filter((l) => l.who === "you").map((l) => l.text).join(" ")));
    const full = T.asked.length >= P.probes[1];
    const paused = T.said > 0 && silent >= P.pauseMs;
    const talking = P.talkMs && T.talkStart && silent < 3000 && now - T.talkStart >= P.talkMs;
    const item = T.queue.find((x) => !full || x.kind === "pushback" || x.kind === "challenge");
    if (item) {
      const urgent = ["trap", "trigger", "challenge"].includes(item.kind) && P.triggerMs !== null && now - item.at >= P.triggerMs;
      if (paused || talking || (urgent && (P.midSentence || silent >= P.triggerMs))) return void ask(item);
      return;
    }
    if (full) return;
    // Nothing queued: at a pause, or when the student has been quiet for a long time, ask a question or generic probe.
    const quiet = silent >= 20000 && elapsed > 60000 && T.asked.length < P.probes[0];
    if (paused || talking || quiet) {
      const p = unasked((x) => x.kind === "question" && questionProbes(B, q).includes(x)) || unasked((x) => x.kind === "generic");
      if (p) ask({ kind: p.kind, probe: p });
    }
  }

  // --- clock ---
  const remaining = el("span", { class: "time" });
  const clockStatus = el("p", { class: "timer-status", "aria-live": "polite" });
  const used = el("span");
  const clock = el("section", { class: "timer", "aria-label": "Time left" },
    el("p", { class: "remaining" }, remaining, el("span", {}, "remaining")),
    clockStatus,
    el("div", { class: "progress", "aria-hidden": "true" }, used));
  let warned = false;
  function drawClock(elapsed) {
    const left = total - elapsed;
    remaining.textContent = left >= 0 ? fmt(left) : `+${fmt(-left)}`;
    used.style.width = `${Math.min(100, (elapsed / total) * 100)}%`;
    if (left <= WARN_MS && !warned) {
      warned = true;
      clock.classList.add("warn");
      clockStatus.textContent = B.lines.warning;
    }
    if (left <= 0 && !clock.classList.contains("timeup")) {
      clock.classList.add("timeup");
      clockStatus.textContent = P.hardStop ? "Time is up" : "Over time. Finish when you are ready.";
    }
  }

  // --- ending ---
  let timer = null;
  const stopAll = () => {
    T.ended = true;
    clearInterval(timer);
    try { rec?.abort(); } catch { /* not running */ }
    if (TTS) speechSynthesis.cancel();
  };
  async function finish(reason) {
    if (T.ended) return;
    if (reason === "done" && !P.hardStop && T.asked.length < P.probes[0] && Date.now() - T.lastExaminer >= MIN_GAP_MS && !T.closing) {
      // Supportive asks its follow-up when the student presses Done, if it has not asked one yet.
      T.closing = true;
      done.textContent = "End task";
      const p = unasked((x) => x.kind === "question" && questionProbes(B, q).includes(x)) || unasked((x) => x.kind === "generic");
      if (p) return void ask({ kind: p.kind, probe: p });
    }
    stopAll();
    if (reason === "time") {
      addLine("examiner", B.lines.time_up, { kind: "end" });
      if (media.speak) { const u = new SpeechSynthesisUtterance(B.lines.time_up); if (voice) u.voice = voice; speechSynthesis.speak(u); }
    }
    T.duration = at();
    T.reason = reason;
    debrief(main, ui, B, setStop, T, check);
  }
  done.addEventListener("click", () => finish("done"));
  setStop(stopAll);

  // --- layout ---
  const task = subject === "Regression"
    ? el("article", { class: "card question" },
      el("p", { class: "qid" }, `${q.id}, model ${q.model_id}`),
      el("p", { class: "prompt" }, q.prompt),
      el("p", { class: "equation" }, ui.equation(S.mById[q.model_id])),
      el("div", { style: "margin-top: 24px" }, ui.modelTables(S.mById[q.model_id])))
    : el("article", { class: "card question" },
      el("p", { class: "qid" }, `${q.id}, ${q.subject}, ${q.case}`),
      el("p", { class: "prompt" }, q.prompt),
      ui.facts([
        ["Files", ui.downloads(q.dataset_ids)],
        q.expected_answer_hint ? ["Answer format", q.expected_answer_hint] : null,
        ["Data", ui.datasetReference(q)],
      ]));
  const answerBox = el("div", { class: "ic" },
    el("label", { for: "exam-answer" }, "Your answer"),
    el("div", { class: "ic-row" }, answerInput, answerBtn), answerNote);
  main.replaceChildren(
    ui.pageHead("Exam mode", { lead: `${TOPICS[T.topic]}, ${P.label.toLowerCase()} examiner, ${T.minutes} minutes.` }),
    el("div", { class: "exam-layout" },
      el("div", { class: "exam-main" }, clock, task, answerBox),
      el("aside", { class: "exam-side card", "aria-label": "Transcript" },
        el("h2", {}, "Transcript"), mic, list, interim,
        el("div", { class: "say" }, typed, el("div", { class: "buttons" }, send, hint)),
        done)));
  main.querySelector("h1")?.focus();

  drawClock(0);
  timer = setInterval(tick, 500);
  const intro = subject === "Regression" ? `Here is your task. ${q.prompt}` : `Here is your task. ${q.prompt} Explain what you do and why as you go.`;
  ask({ kind: "intro", text: intro }).then(() => { T.lastExaminer = -Infinity; T.awaiting = null; });
  startRec();
}

// ---------- debrief ----------

function debrief(main, ui, B, setStop, T, check) {
  const { S, el } = ui;
  const q = T.q;
  setStop(() => {});
  const tagLabel = (tag) => B.tags[tag]?.label || tag;
  for (const h of T.trapHits) session.tagCounts.set(h.tag, (session.tagCounts.get(h.tag) || 0) + 1);

  // The answer and the explanation from the question bank.
  const last = T.answers[T.answers.length - 1];
  const verdict = { correct: "Correct.", also: "Defensible, see the note.", wrong: "Not the expected answer.",
    notime: "Right date, but the time is missing.", unreadable: "Could not be read as a value.", unchecked: "Not checked." };
  const answerPart = el("section", { class: "card" }, el("h2", {}, "The answer"),
    last ? el("p", {}, "Your last answer: ", el("strong", {}, last.raw), ". ",
      last.state === "trap" ? `This is a known trap: ${last.trap.category.toLowerCase()}.` : verdict[last.state] || "")
      : el("p", { class: "muted" }, "You did not submit an answer in the answer box."),
    last?.state === "trap" ? el("p", {}, last.trap.why) : null,
    check ? el("div", { class: "answer" }, answerBlock(check))
      : q.worked_answer ? el("div", { class: "answer" }, el("p", {}, q.worked_answer))
        : el("p", { class: "muted" }, `This question has no single-value check. Answer format: ${q.expected_answer_hint || "see the question"}.`));

  const transcript = ui.table({ head: ["Time", "Who", "What was said"], rows: T.lines.map((l) => {
    const thin = l.who === "you" && T.thin.some((x) => x.answer.includes(l.text));
    return [{ v: fmt(l.t), num: true },
      l.who === "examiner" ? el("strong", {}, "Examiner") : l.who === "hint" ? "Hint" : l.who === "system" ? "Note" : "You",
      el("span", { class: l.who === "examiner" ? "said-examiner" : null }, l.text, thin ? el("span", { class: "flag" }, " Thin") : null)];
  }) });
  transcript.table.classList.add("debrief-transcript");

  const tags = new Map();
  for (const h of T.trapHits) tags.set(h.tag, (tags.get(h.tag) || 0) + 1);
  for (const t of T.thin) if (t.tag) tags.set(t.tag, (tags.get(t.tag) || 0) + 1);
  const why = { trap: "your answer matched a trap", trigger: "a term you used", question: "this task", generic: "general", challenge: "a check of conviction", pushback: "thin answer" };
  const facts = ui.facts([
    ["Time used", `${fmt(T.duration)} of ${T.minutes}:00${T.reason === "time" ? ", stopped at the time limit" : ""}`],
    ["Probes asked", T.asked.length ? el("ul", { class: "plain" }, T.asked.map((a) =>
      el("li", {}, `${fmt(a.t)} ${a.probe.text} `, el("span", { class: "muted" }, `(${why[a.why] || a.why}${a.probe.tag ? `, ${tagLabel(a.probe.tag)}` : ""})`)))) : "None"],
    ["Thin answers", T.thin.length ? el("ul", { class: "plain" }, T.thin.map((t) =>
      el("li", {}, el("span", { class: "muted" }, `${t.question} `), `"${t.answer}"`))) : "None flagged"],
    ["Trap answers", T.trapHits.length ? el("ul", { class: "plain" }, T.trapHits.map((h) =>
      el("li", {}, `${fmt(h.t)} ${show(check, h.value)} in the ${h.source}: ${h.category.toLowerCase()}`))) : "None"],
    ["Trap tags", tags.size ? [...tags].map(([t, n]) => `${tagLabel(t)} (${n})`).join(", ") : "None came up"],
    ["Hints", T.hints.length ? `${T.hints.length} used, at ${T.hints.map(fmt).join(", ")}` : "None used"],
  ]);

  const self = el("form", { class: "card self" }, el("h2", {}, "Your own assessment"),
    el("p", { class: "muted small" }, "This is practice, not a grade on the 7-point scale. Nothing you tick here is saved."),
    ["Did I get the number right?", "Did I explain why, not only what?", "Did I handle the interruptions?"].map((text, i) =>
      el("fieldset", {}, el("legend", {}, text), el("div", { class: "segmented" },
        ["Yes", "Partly", "No"].map((v) => el("label", {}, el("input", { type: "radio", name: `s${i}`, value: v }), el("span", {}, v)))))));

  const weakest = [...session.tagCounts].sort((a, b) => b[1] - a[1])[0];
  const again = (tag) => () => runTask(main, ui, B, setStop, pickTask(ui, B, settings.topic, tag), T.media);
  main.replaceChildren(
    ui.pageHead("Debrief", { lead: `${q.id}. ${q.prompt}` }),
    el("div", { class: "stack" },
      answerPart,
      el("section", { class: "card" }, el("h2", {}, "What happened"), facts),
      el("section", {}, el("h2", { class: "section-title" }, "Transcript"), transcript.wrap),
      self,
      el("div", { class: "buttons" },
        weakest ? el("button", { type: "button", class: "big", onclick: again(weakest[0]) }, `Practise my weak spots: ${tagLabel(weakest[0]).toLowerCase()}`) : null,
        el("button", { type: "button", class: weakest ? "secondary" : "big", onclick: again(null) }, "Next task"),
        el("button", { type: "button", class: "secondary", onclick: () => setup(main, ui, B, setStop) }, "Change settings")),
      weakest ? null : el("p", { class: "muted small" }, "Practise my weak spots appears once a trap answer or a thin answer to a tagged probe has come up in this visit.")));
  main.querySelector("h1")?.focus();
  window.scrollTo(0, 0);
}
