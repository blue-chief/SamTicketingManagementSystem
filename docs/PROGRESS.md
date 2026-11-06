# Build progress

Working order is the dependency order, not the dev split. Tick a task only when its "Done when" line in docs/tasks/ is true and the tests pass.
Task details: docs/tasks/D1-..., D2-..., D3-... (task IDs below match those files).

## Phase 1: Foundation
- [x] D1-01 Repo scaffold, Compose, CI
- [ ] D1-02 Schema and migrations
- [ ] D1-03 Seed data
- [ ] D1-04 Auth and RBAC
- [ ] D1-05 Audit service and API

## Phase 2: Core ticket logic and app shell
- [ ] D3-02 State machine and ticket service
- [ ] D3-03 Ticket API
- [ ] D3-04 Svelte shell, login, ticket list and detail

## Phase 3: Ingestion
- [ ] D2-01 IMAP poller
- [ ] D2-02 Filters, attachment validation, queue
- [ ] D2-03 Labelled data, baseline analyser, eval script
- [ ] D2-04 Pipeline runner (P1-P6) + scripts/send_test_emails.py

**MILESTONE 1:** email sent to the test mailbox appears as a ticket in the browser. Restarting the worker mid-batch loses and duplicates nothing. Staff cannot open another staff member's ticket.
- [ ] Milestone 1 passed

## Phase 4: Intelligence, routing, notifications
- [ ] D2-05 OCR
- [ ] D3-05 Routing engine
- [ ] D3-06 Notification core, WebSocket, email
- [ ] D2-06 Analyser integration (P8) and triage fallback
- [ ] D3-07 Scheduler timers
- [ ] D1-09 Auto-close and purge
- [ ] D2-07 Thread matching, duplicates, similar links
- [ ] D3-08 Staff dashboard and ticket work UI
- [ ] D1-10 Notification UI
- [ ] D2-08 SMS and WhatsApp adapters
- [ ] D2-09 AI evaluation gate (category accuracy at or above 80%)

**MILESTONE 2 (demo):**
1. Billing complaint with a screenshot: ticket created, CAT-03, High, summary, routed to Finance staff, notification arrives in-app and by email.
2. Ignore it: after the timeout it moves to backup staff, audit shows ACK_TIMEOUT.
3. Reply to the ticket email: joins the same ticket.
4. Vague email: lands in Uncategorised, admin alerted.
- [ ] Milestone 2 passed

## Phase 5: Admin and governance
- [ ] D1-06 Admin configuration API
- [ ] D1-07 Admin configuration UI
- [ ] D1-08 Access sharing
- [ ] D2-10 Uncategorised queue (API and UI)
- [ ] D3-10 Admin reassignment
- [ ] D3-09 Security fast path
- [ ] D3-11 Profile, availability, system alerts
- [ ] D1-11 Admin dashboard

## Phase 6: Hardening and docs
- [ ] D2-11 Hardening and security checklist
- [ ] D2-12 Resilience and load tests
- [ ] D3-12 Handover documentation

## Deferred (need the firm, a server and a domain)
- [ ] D3-01 Staging environment
- [ ] D1-12 Production deployment and backups
- [ ] ALL-01 Acceptance run with the firm
- [ ] D2-13 Stretch: local LLM and voice (only if everything else is done)

---

## Session notes
Newest first. The agent appends one entry at the end of every task session.

Template:
### <task ID> · <date>
- Built:
- Files/areas touched:
- Stubbed (marked STUB in code):
- Assumptions made:
- Spec questions or ambiguities:
- How to run/test it:

### D1-01 · 2026-11-06
- Built: Project skeleton including Section 18 folder structure, FastAPI app factory with CORS, structured JSON logging without message bodies/PII, pydantic-settings Settings class covering all Appendix B variables, async SQLAlchemy session factory, GET /health endpoint (checking DB, Redis, IMAP poll timestamp, queue depth), ARQ worker entrypoint with 30s cron heartbeat (status:worker_heartbeat), minimal SvelteKit + TypeScript frontend with adapter-node, Docker Compose with 5 services (postgres, redis, api, worker, frontend), dev compose, prod compose override, Caddyfile placeholder, safe .env.example, tooling configs (ruff, pytest with async client fixture), and GitHub Actions CI workflow (ruff, pytest, svelte-check, docker-compose build).
- Files/areas touched: backend/app/{api,core,db,models,schemas,services,pipeline,ai,notifications,workers}, backend/{alembic,tests,scripts}, frontend, deploy, .github/workflows/ci.yml, Makefile, pyproject.toml, .gitignore.
- Stubbed (marked STUB in code): None.
- Assumptions made: Node 22 used for SvelteKit 3 (`Promise.withResolvers`); `JWT_SECRET` has safe dev default in Settings with `CHANGE_ME_IN_PRODUCTION` in `.env.example`; dev Compose does not run Caddy (staging/prod per spec).
- Spec questions or ambiguities: None.
- How to run/test it:
  - Compose: `docker compose -f deploy/docker-compose.yml up --build -d`
  - Health check: `curl http://localhost:8000/health` or `Invoke-RestMethod http://localhost:8000/health`
  - Pytest: `python -m pytest -v`
  - Ruff: `ruff check backend/ && ruff format --check backend/`
  - Svelte check: `cd frontend && npx svelte-check --threshold warning`