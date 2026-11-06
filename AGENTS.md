# Project rules for the coding agent (Antigravity)

Put this file at the repo root (and, if Antigravity supports workspace rules, copy it there too) so every task prompt starts with this context.

## Project
SamConsultingFirm Ticket Management Tool. Client complaint emails (IMAP) become tickets that are filtered, classified, summarised, routed to a department and staff member, notified (in-app, email, SMS, WhatsApp), escalated on timeout, and shown on staff/admin dashboards. 3-week build, 3 backend developers.

## Stack
Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, PostgreSQL, Redis + ARQ, imap-tools, aiosmtplib, pytesseract, sentence-transformers, scikit-learn, SvelteKit + TypeScript, Docker Compose, Caddy, GitHub Actions (ruff, pytest, svelte-check).

## Where the truth lives
Read `docs/spec/` before coding. Always read the files named in the task. `docs/spec/M10-shared-contracts.md` defines the function signatures between modules: use them exactly, do not invent alternatives. Section numbers (e.g. "9.3") refer to the master spec and are preserved in the module files.

## Rules
1. Plan first: before writing code, list the files you will create or change and the tests you will write. Then implement.
2. Work only inside the task's scope. If you need something from another module that does not exist yet, code against the contract in M10 and create a minimal stub that is clearly marked `# STUB(owner D#)`. Do not implement other people's modules.
3. Status changes only through `transition()`. Thresholds and limits through `get_setting()`. Taxonomy from the database. No hard-coded categories or departments.
4. Audit every state change, assignment, access change, config change, purge.
5. Never log message bodies or personal data. Never commit secrets. New env vars go in `deploy/.env.example` and the config reference.
6. Write tests for business logic (pytest, httpx AsyncClient). Run `ruff`, `pytest` (and `svelte-check` for frontend work) and fix failures before you finish.
7. Keep commits small, message style `feat(scope): summary`. Open one PR per task.
8. When done, reply with: what you built, files changed, how to run/test it, anything you stubbed, any assumption you made, any spec ambiguity you found.

## North star and progress
- `docs/spec/MASTER-SPEC.md` is the original full specification and the north star of this project. The files in `docs/spec/M00..M10` are the same content split into modules (plus M10 shared contracts). If a module file and MASTER-SPEC.md disagree, or if anything is unclear or missing, STOP and ask me instead of guessing.
- At the start of every task, read `docs/PROGRESS.md` (especially the session notes) so you know what already exists and what is stubbed.
- At the end of every task, append a session note to `docs/PROGRESS.md` using the template there, and tick the task's checkbox only if its "Done when" condition is met and tests pass.
- Before finishing, search the code for `STUB` and tell me about every stub that belongs to the task you are working on or that your task has now made unnecessary, then replace it with the real implementation if the real module exists.