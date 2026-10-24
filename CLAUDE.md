# ExamStudio practice site: standing rules for every Claude Code run

This repo is Knut's individual hand-in for Assignment 2 in AI in Accounting and Business (SDU, autumn 2026): a practice website for the course Data Analytics in Accounting. Read this file before every run. The run prompts live in `prompts/`.

## Paths

- Repo root: `C:\Users\knbar\Documents\examstudio`
- Material source (read only, never modify): `MATERIALS_SRC = C:\Users\knbar\OneDrive\Skrivebord\AI in Accounting and Business\Assignment 2\1. ExamStudio\materials`
  - Path confirmed to exist on 23.10.2026, together with `ASSIGNMENT.md` and `IMPROVEMENTS.md` in its parent folder.
- Local working copy of the materials: `materials/` in the repo root. It is gitignored and must never be committed.
- Assignment text: `MATERIALS_SRC\..\ASSIGNMENT.md` and `MATERIALS_SRC\..\IMPROVEMENTS.md`
- GitHub remote: `https://github.com/knbarka-beep/examstudio.git`, branch `main`
- Published site: `docs/` (GitHub Pages serves `main` /docs)

## Machine

Windows 11. Python is `py` (never `python` or `python3`). Install packages with `py -m pip install --user <pkg>`. Git identity is already set globally. No Node is assumed; do not add a JavaScript build step.

Your shell may be Git Bash or PowerShell depending on the Claude Code version, so do file work (copying, searching, sizes, hashes, timestamps, zipping) in Python scripts with `shutil`, `os`, `pathlib`, `hashlib`, `zipfile` and `datetime`, not with shell-specific commands. Use the shell only for `py` and `git`.

## Stack

Plain HTML, CSS and vanilla JavaScript in `docs/`, reading JSON from `docs/data/`. No framework, no bundler, no backend, no API key. Python scripts in `scripts/` and `tests/` build and validate the content. Local preview: `py -m http.server 8000 --directory docs`.

## Hard rules

1. Questions and exams are based only on the course materials and the skills practised in them. No outside datasets, no invented topics.
2. Never invent a reference solution and attribute it to the materials. Solutions taken from the materials get `solution_source: "materials"` with the file name. Solutions you write get `solution_source: "generated"` and must be verified in Run 2 before they count.
3. Do not publish reference solutions, answer documents or case texts. Nothing from `materials/` goes into git except the dataset files students need, copied into `docs/files/`. `scripts/build_site.py` strips solution fields from the public JSON unless `docs/data/config.json` has `"showReferenceSolutions": true` (default false).
4. No secrets anywhere. Never print, echo or commit a key, token or password. If any secret appears in a file, stop and log it.
5. Do not build "the improvement". Knut chooses it later from his own experience on the course. Leave the slot described in Run 3 and nothing more. Do not add AI tutoring, feedback storage, analytics or accounts.
6. Everything user facing is in English. British spelling. Dates as 31.12.2026.
7. Design: quiet and functional, like a university tool. No purple or other gradients, no pill-shaped buttons, no emoji or decorative icons, no vague hero text, no scroll or cursor animations, no fake metrics, counters or testimonials, no stock or AI images, no em dashes in any copy, no "made with AI" tag.
8. Where Knut's own wording is needed, insert a marker `[[KNUT: what is needed]]` instead of writing it.
9. Never force-push, never rewrite history, never delete files outside the repo.

## Logging and resuming

- `LOG.md` has three sections: "Active time (Knut)", "Unattended runs" and "Cost statement". For each run, append start and end timestamps (Europe/Copenhagen time, from Python `datetime`), duration, what was done, and what failed. Leave "Active time" and the cost figures for Knut, using `[[KNUT: ...]]` markers.
- Each run keeps a checklist in `LOG.md` under its own heading. Tick items as they finish. If a run starts and finds items already ticked, verify them quickly and continue from the first unticked one. Runs may be cut off by usage limits, so commit locally after each major step.
- Commit messages are short and plain English.
