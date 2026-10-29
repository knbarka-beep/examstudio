# RUN 7: Examiner mode + polished, white redesign

You are working in the ExamStudio repo (static site on GitHub Pages, repo knbarka-beep/examstudio). It is a practice site for the SDU course Data Analytics in Accounting. The real oral exam includes solving case-style Excel/SQL tasks in about 8 to 10 minutes each while explaining out loud what you do and why. This run adds a mode that simulates exactly that, and cleans up the look.

## 0. Before you change anything

1. Read ASSIGNMENT.md, README.md, LOG.md and everything in prompts/ so you know what earlier runs did.
2. Run `git log --oneline -15` and check whether RUN6_spreadsheet.md was actually carried out. Report this in one line before you start.
3. List the current pages, the question bank format and where datasets are loaded from (GitHub release datasets-v1). Do not break any of it.
4. Keep the stack as it is: plain HTML, CSS and JavaScript, no framework, no build step. If you think a library is needed, use one from cdnjs and say why in LOG.md.

## 1. Redesign: white, polished, Apple-like

The owner finds the current site messy. Goal: a clean, modern, polished site in the spirit of apple.com. Light, airy and premium, not plain or analogue. Simplicity comes from less on each screen, not from removing all styling.

- White and very light grey (#f5f5f7) backgrounds, near-black text, one confident accent colour (for example a clear blue). Large, bold headings with tight letter spacing, calm body text.
- System font stack (-apple-system, SF Pro on Apple devices, Segoe UI on Windows) or Inter.
- Rounded cards and controls, soft subtle shadows, smooth hover states and short, gentle transitions are welcome. Use them with restraint so the page stays calm.
- Max content width about 980px, centred, lots of white space. One clear primary action per screen.
- Top navigation with at most four items: Practice, Exam mode, Progress, About. Move anything else into those pages or remove it. A light translucent sticky nav bar is fine.
- Clean line icons are fine where they help; no emoji as icons.
- Content rules: no hero text that says nothing, no counters or fake metrics, no "made with AI" tag, no em dashes in any copy.
- If a spreadsheet-style workspace from Run 6 exists, keep it only inside the task area, styled to match (thin light gridlines, rounded container).
- Must work at phone width (16px side gutter, no horizontal scroll), although exam mode is meant for desktop.
- Remove dead code and unused CSS you find while doing this. List what you removed in LOG.md.

## 2. New feature: Exam mode (the examiner)

### 2.1 Setup screen
The user picks:
- Topic: Excel, SQL, Power BI theory, or Mixed.
- Examiner strictness: Supportive, Standard, Strict (see 2.4).
- Duration per task: 8 or 10 minutes.
- Voice: on (examiner speaks, user answers by microphone) or off (text only).
- A short line explaining that microphone audio in Chrome and Edge is processed by the browser vendor's speech service, so nothing confidential should be said. Keep this factual, one sentence.

A "Start exam" button. Before starting, run a mic check and show plainly if speech recognition is not supported (Firefox, some Safari versions) and fall back to a text box.

### 2.2 During the exam
- The examiner reads the task out loud with `speechSynthesis` (pick an English voice, en-GB preferred, normal rate). The task text is also shown on screen.
- The user works in the existing task workspace (SQL editor, spreadsheet or whatever the question type uses) and talks while working.
- Speech recognition via the Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`), continuous with interim results, shown as a live transcript in a narrow side panel. Restart recognition automatically when the browser ends it.
- A visible countdown timer. A soft warning at 2 minutes left.
- The examiner interrupts with follow-up questions (see 2.3 and 2.4). When the examiner speaks, pause recognition so it does not transcribe itself, then resume. Show the examiner's question as a highlighted line in the transcript.
- The user can always type instead of speaking (a text field under the transcript).
- A "Done, I'm finished" button ends the task early.

### 2.3 How the examiner decides what to ask (no LLM needed)
Build a probe bank as a JSON file (e.g. data/probes.json). Each probe has: id, text, topic, trigger keywords or regex, trap tag, and an optional "pushback" text for weak answers.

Three kinds of probes:
1. Trigger probes: fired when the transcript or the user's formula/query contains certain terms. Examples: VLOOKUP → "Why VLOOKUP and not XLOOKUP or INDEX/MATCH?"; JOIN → "What is the grain of the result after that join? Can it duplicate rows?"; AVERAGE on a ratio → "Is an average of percentages the same as the overall percentage here?"; GROUP BY → "What does one row represent now?"; a pivot → "Which field is your key, and is it unique?"; regression wording → "Could a third variable explain that relationship?"
2. Question-specific probes: tie probes to individual question ids where it makes sense. Add an optional `probes` array to the question format without breaking existing questions.
3. Generic "why" probes for when nothing triggers: "Why did you do it that way?", "What would you check to be sure the number is right?", "How would you explain this result to a partner who doesn't use Excel?"

Weight the probes towards the owner's known weak spots: answers that look right but are wrong because of the wrong level or grain, mix effects (Simpson-type aggregation), non-unique keys in lookups and joins, confounding in regression, and explaining why rather than what. Tag these probes so the debrief can report on them.

Answer quality check (simple heuristics, documented in the code): an answer is "thin" if it is under about 15 words, or contains no reasoning words (because, so, since, otherwise, which means, the reason). In Standard and Strict mode a thin answer triggers the pushback text, for example "That tells me what you did. Why?"

### 2.4 Strictness presets
Put the parameters in one config object so they are easy to tune.

- Supportive: never interrupts mid-answer, asks follow-ups only when the user pauses for about 4 seconds or presses Done. One or two probes per task. Hints available. Timer shown but no hard stop. No pushback on thin answers, just a gentle "Can you say a bit more?"
- Standard (internal examiner): may interrupt after about 60 to 90 seconds of continuous talking or right after a trigger term. Three or four probes per task. One hint, which is noted in the debrief. Pushback on thin answers once. Hard stop at the time limit.
- Strict (external examiner): interrupts within a couple of seconds of a trigger term, even mid-sentence. Four to six probes. No hints. Pushes back on thin answers up to twice. Sometimes challenges a correct answer ("Are you sure? Convince me.") to test conviction, about once per task. Hard stop at the time limit.

Never let two interruptions happen within 20 seconds of each other in any mode.

### 2.5 Optional LLM examiner (off by default)
Add a setting "Use an AI examiner (needs your own API key)". The key is typed by the user, kept only in that browser's localStorage, never written to the repo, never logged. If on, send the task text, the current transcript and the user's formula/query to the model to generate the next follow-up and the final feedback, with the rules-based examiner as fallback if the call fails. Use the Anthropic Messages API directly from the browser; check the current docs for the required browser-access header and current model names before writing the call, and use a small cheap model by default. Show an estimated token count per session. If this turns out to be more than a small, clean addition, skip it, note why in LOG.md, and say so in your final report.

### 2.6 Debrief after each task
- Full transcript with the examiner's questions marked, time stamps.
- Which probes were asked, which answers were flagged thin, which trap tags came up.
- The correct answer and the explanation from the question bank, shown after the attempt.
- A simple self-assessment the user fills in (did I get the number right, did I explain why, did I handle the interruptions), not an automatic grade. Label clearly that this is practice, not a grade on the 7-point scale.
- "Practise my weak spots": starts a new task chosen from questions whose trap tags were flagged most often.
- Save sessions in localStorage (wrap every read/write in try/catch) and show them on the Progress page: sessions per topic, thin answers per trap tag over time.

## 3. Wording the owner writes himself
Wherever the site needs text that explains why the owner built examiner mode or how it relates to his own exam preparation (About page, README section on the improvement), leave a clearly visible marker `<!-- KNUT: write this yourself -->` plus a placeholder line on the page reading `[KNUT: your text here]`. Do not write that text.

## 4. Testing and hand-off
1. Run locally with `py -m http.server 8000` and test in Chrome and Edge: setup, voice on, voice off, each strictness, at least one Excel and one SQL task, the debrief and the Progress page.
2. Check the page at 390px width.
3. Check that no API key, token or secret exists anywhere in the repo or git history (`git grep -i "sk-ant"` and similar).
4. Update README.md (what exam mode is, which browsers support voice, the privacy line) and append to LOG.md: date, what was done, time spent, cost (Claude Pro subscription, no API cost unless the optional LLM was tested).
5. Commit in sensible steps (redesign, probe bank, exam mode, debrief, docs) and push to main.
6. Finish with a short report: whether Run 6 had been run, what changed, what was skipped and why, any browser limits found, and the KNUT markers left for the owner.
