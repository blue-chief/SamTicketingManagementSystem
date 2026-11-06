# D1 · Platform, Access and Governance

**You own:** repo and CI, database schema, seed data, authentication and RBAC, audit log, admin configuration (API and UI), access sharing, auto-close and purge, notification UI, admin dashboard, production deployment.

**Study first (about 2 hours):** `M00`, `M03`, `M04` (including the 12.A addendum), `M08`, `M10`. Then `M02` sections 8, 9.1, 9.5 and `M05` sections 13.1, 13.4.

**How to use this file:** for each task, open a fresh agent session, paste the text in the "Prompt" block, and attach/point to the files in "Read". Review the diff, run the tests, merge. Tick the task off.

| Task | Sprint / Days | Depends on | Task |
|---|---|---|---|
| D1-01 | S1 · Day 1 | P0-05 | Repo scaffold, Compose, CI |
| D1-02 | S1 · Day 1-2 | D1-01 | Schema and migrations |
| D1-03 | S1 · Day 2 | D1-02 | Seed data |
| D1-04 | S1 · Day 3 | D1-02 | Auth and RBAC |
| D1-05 | S1 · Day 4 | D1-02 | Audit service and API |
| D1-06 | S2 · Day 6-7 | D1-03, D1-05 | Admin configuration API |
| D1-07 | S2 · Day 7-8 | D1-06, D3-04 | Admin configuration UI |
| D1-08 | S2 · Day 8-9 | D3-02, D3-06 | Access sharing |
| D1-09 | S2 · Day 9-10 | D3-02 | Auto-close and purge |
| D1-10 | S2 · Day 9-10 | D3-06, D3-04 | Notification UI |
| D1-11 | S3 · Day 11-12 | D3-07, D2-06 | Admin dashboard |
| D1-12 | S3 · Day 12-13 | D3-01 | Production deployment and backups |

**Hand-offs you owe others:** schema models merged by end of Day 1 (D2, D3 wait on them). `can_access`, `get_current_user`, `require_admin` by Day 3 (D3-03). `log_audit` by Day 3 (D3-02). `get_setting` by Day 3.

---

## D1-01 · Repo scaffold, Docker Compose, CI

**Read:** `docs/spec/M03-architecture-and-setup.md`, `docs/spec/M08-security-and-config.md` (Appendix B), `docs/spec/M10-shared-contracts.md`

```text
You are setting up the repository for the SamConsultingFirm Ticket Management Tool. Read AGENTS.md, docs/spec/M03-architecture-and-setup.md (section 18 layout), docs/spec/M08-security-and-config.md (Appendix B variables) and docs/spec/M10-shared-contracts.md first.

Task: create the project skeleton.
1. Create the exact folder layout from section 18 (backend/app/{api,core,db,models,schemas,services,pipeline,ai,notifications,workers}, backend/{alembic,tests,scripts}, frontend, deploy, docs). Add empty __init__.py files and short README placeholders where useful.
2. Backend: FastAPI app factory with CORS config, structured JSON logging (no bodies or personal data), pydantic-settings Settings class covering EVERY variable in Appendix B with the listed defaults, async SQLAlchemy engine/session dependency, and GET /health returning database status, redis status, imap:last_poll (from Redis, null if absent) and queue depth.
3. Worker: an ARQ worker entrypoint (backend/app/workers/worker.py) with a heartbeat cron job that writes status:worker_heartbeat to Redis. Leave a clearly commented place where other modules register jobs.
4. Frontend: minimal SvelteKit + TypeScript project that builds and serves a placeholder page.
5. deploy/docker-compose.yml with services api, worker, postgres (persistent volume), redis, frontend. deploy/.env.example listing every variable name with safe dummy values.
6. Tooling: ruff config, pytest config with an async test fixture, one smoke test for /health, a Makefile or scripts for common commands (up, test, lint, migrate).
7. GitHub Actions workflow: ruff, pytest (with postgres and redis services), svelte-check, docker image build.

Constraints: no secrets in git, Python 3.12, everything async. Do not create database models or business logic; that is another task.
Done when: `docker compose -f deploy/docker-compose.yml up` starts all services, /health returns ok JSON, CI passes on the smoke test. Report the commands to run it.
```

**Done when:** one command starts everything locally, CI green on an empty test. **Reqs:** NFR-11.

---

## D1-02 · Database schema and migrations

**Read:** `docs/spec/M04-data-model.md` (section 12 and 12.A), `docs/spec/M02-domain-rules.md` (9.1 statuses)

```text
Read AGENTS.md, docs/spec/M04-data-model.md (section 12 AND the 12.A addendum), and docs/spec/M02-domain-rules.md section 9.1.

Task: implement the full database layer.
1. SQLAlchemy 2 async declarative models in backend/app/models/ for EVERY table in section 12, plus the additions in 12.A (settings, ticket_assignments, tickets.assigned_at, notifications.read_at, users.must_change_password, complaint_types.keywords). UUID primary keys (except tickets.ref which is a unique human reference), created_at on all tables, proper enums, foreign keys, indexes on the columns used for filtering (tickets.status, assignee_id, category_id, department_id, priority, needs_triage; messages.ticket_id; ingest_log unique(mailbox, uidvalidity, imap_uid)).
2. A Postgres sequence and helper next_ticket_ref() that returns TKT-000001 style references, safe under concurrency.
3. Constraint or service-level validation that complaint_types.category_id matches tickets.category_id.
4. First Alembic migration (async env). It must also create a restricted application role/grant statement set so the app role has INSERT and SELECT only on audit_log (no UPDATE or DELETE). Document how the app connects with that role in docs/runbook-notes.md.
5. Tests: migration upgrade and downgrade on a clean database, unique index rejects duplicate ingest_log rows, ticket ref generator produces unique sequential refs across 50 concurrent calls, audit_log UPDATE/DELETE fails for the app role.

IMPORTANT: other developers depend on the models. Put the models in a first commit and push it early, then continue with the migration and tests.
Done when: `alembic upgrade head` and `downgrade base` both run cleanly and all tests pass.
```

**Reqs:** FR-04, FR-23, NFR-06, all data.

---

## D1-03 · Seed data

**Read:** `docs/spec/M02-domain-rules.md` (section 8, 9.2), `docs/spec/M08-security-and-config.md` (Appendix B)

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md sections 8 and 9.2, docs/spec/M04-data-model.md.

Task: write backend/scripts/seed_taxonomy.py (also callable as a function from tests).
Seed, idempotently (running twice creates no duplicates; use upserts keyed by code/name):
- 6 departments DEP-01..DEP-06 exactly as in section 8.1 (DEP-06 gets no category).
- 6 categories CAT-01..CAT-06 with their primary and secondary department mapping (category_departments).
- All complaint types for each category from section 8.2, each with default_priority from the section 9.2 rules and keywords (a short list of plausible words per type, for example "charged twice", "double charge" for Duplicate charges).
- The type-level override: "Paid account access issues" has DEP-02 as primary override (DEP-04 secondary).
- priority_sla rows: Critical 10 min ack / 4 h resolve, High 10/24 h, Medium 10/72 h, Low 10/5 days (store minutes).
- settings rows for every threshold in Appendix B (CONFIDENCE_THRESHOLD, DUPLICATE_SIMILARITY, SIMILAR_LINK_SIMILARITY, ACK_TIMEOUT_MINUTES, MAX_AUTO_REASSIGN, AUTO_CLOSE_DAYS, REOPEN_WINDOW_DAYS, IMAP poll seconds) plus purge_summary_categories = ["CAT-03","CAT-06"].
- One admin user whose email and initial password come from env vars SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD, must_change_password = true. Add those vars to deploy/.env.example.
- A dev-only flag --demo that also creates 2 staff per department (one flagged backup) and one incident contact.
Tests: counts match section 8, idempotency, override resolves to DEP-02.
Done when: running the script twice on an empty DB gives the same row counts.
```

**Reqs:** FR-19.

---

## D1-04 · Authentication and RBAC

**Read:** `docs/spec/M05-api.md` (13.1), `docs/spec/M08-security-and-config.md` (section 16), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.1, docs/spec/M08-security-and-config.md section 16 and docs/spec/M10-shared-contracts.md.

Task: implement authentication and authorisation.
1. POST /api/v1/auth/login (email+password -> short-lived JWT access token + refresh token), POST /auth/refresh, GET /me, PATCH /me (phone, whatsapp_number, channels, available, on_leave_until). Argon2 hashing. Rate-limit login (Redis, 5 attempts/minute per email+IP). Reject inactive users. If must_change_password is true, the login response flags it and every route except POST /auth/change-password returns code PASSWORD_CHANGE_REQUIRED.
2. backend/app/core/deps.py: get_current_user, require_admin, require_ticket_access(need="view"|"edit").
3. backend/app/services/access.py: can_access(session, user, ticket, need) -> bool. Rules: admin = always; assignee = view+edit; users with a ticket_access row = per its permission; everyone else = False. Return 404 (not 403) for inaccessible tickets.
4. backend/app/services/settings.py: get_setting(session, key) returns the DB value if present, else the env default; cache for 30 seconds.
5. Tests: full RBAC matrix (admin vs staff vs unauthenticated) on a temporary test router, a staff member cannot read another staff member's ticket by ID, shared (view/edit) access works, expired token rejected.
Done when: all tests pass and the three deps are importable by other modules with the exact signatures in M10.
```

**Reqs:** NFR-07, D-13.

---

## D1-05 · Audit service and audit API

**Read:** `docs/spec/M04-data-model.md` (audit_log + 12.A), `docs/spec/M05-api.md` (13.4), `docs/spec/M02-domain-rules.md` (9.3 point 7)

```text
Read AGENTS.md, docs/spec/M04-data-model.md (audit_log and the 12.A addendum about excusing timeouts), docs/spec/M05-api.md section 13.4 and docs/spec/M02-domain-rules.md section 9.3 point 7.

Task:
1. backend/app/services/audit.py with log_audit(session, *, ticket_id, actor_user_id, actor_type, action, reason_code=None, detail=None) exactly as in M10. Append only: no update or delete function anywhere in the codebase.
2. GET /api/v1/admin/audit (admin only): filters ticket_ref, action, reason_code, actor, date range, and unexcused_timeouts=true. Paginated, newest first.
3. POST /api/v1/admin/audit/{id}/excuse (admin only, body: reason). Because the log is append only, this inserts a NEW row with action ACK_TIMEOUT_EXCUSED and detail.audit_id referencing the original timeout row. "Unexcused timeouts" means ACK_TIMEOUT rows that have no matching excuse row. Reject excusing a row that is not ACK_TIMEOUT or is already excused.
4. Define an Actions constants module (assignment, reassignment, status change, ACK_TIMEOUT, ACK_TIMEOUT_EXCUSED, access granted/denied/requested, purge, config change, login failures optional) so other modules use the same strings.
Tests: log_audit writes rows, no UPDATE/DELETE path exists, excuse flow, unexcused filter.
Done when: other modules can call log_audit and the admin can query and excuse timeouts.
```

**Reqs:** FR-23, D-14.

---

## D1-06 · Admin configuration API

**Read:** `docs/spec/M05-api.md` (13.4), `docs/spec/M02-domain-rules.md` (section 8, 9.2), `docs/spec/M04-data-model.md`

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.4, docs/spec/M02-domain-rules.md sections 8 and 9.2 and docs/spec/M04-data-model.md.

Task: build the admin-only configuration endpoints under /api/v1/admin/ with Pydantic v2 schemas:
- departments, categories (including category->department mapping with primary/secondary), complaint-types (category, primary department override, default priority, keywords), users (create with a generated temporary password and must_change_password, role, department, backup flag, incident contact flag, active, channels), priority-sla (GET, PUT), blocked-senders (pattern supports exact address or @domain), settings (GET, PUT with validation of ranges, for example thresholds 0-1).
Rules: deactivate, never hard-delete, anything referenced by tickets; a complaint type must belong to exactly one category; every category needs a primary department; at most one primary department per category; user email unique; blocklist patterns validated. Every write calls log_audit with the before/after in detail. All endpoints require admin (use require_admin).
Tests: admin-only (staff gets 403), validation rules, audit rows written, creating a category + type + mapping makes it visible to the routing lookup query.
Done when: the admin can fully manage the taxonomy, users, limits, blocklist and settings through the API without code changes.
```

**Reqs:** FR-19, NFR-10, AC-17.

---

## D1-07 · Admin configuration UI

**Read:** `docs/spec/M10-shared-contracts.md` (section 5), `docs/spec/M05-api.md` (13.4), D3-04's `frontend/src/lib` (API client, components)

```text
Read AGENTS.md, docs/spec/M10-shared-contracts.md section 5 and docs/spec/M05-api.md section 13.4. Reuse the API client, stores, layout and shared components that D3 built in frontend/src/lib; do not create a second client.

Task: build the admin configuration screens in SvelteKit + TypeScript (desktop first, admin-only route guard):
- /admin/taxonomy: departments, categories (with department mapping), complaint types (override department, default priority, keywords). Inline add/edit/deactivate.
- /admin/users: list, create (shows the temporary password once), edit role/department/backup/incident contact/active.
- /admin/limits: acknowledge and resolve limits per priority.
- /admin/blocklist: add/remove sender patterns.
- /admin/settings: thresholds and intervals with validation hints.
- /admin/audit: searchable audit table with an "Unexcused timeouts" filter and an Excuse action (reason required).
Show API validation errors inline. Plain, clean layout; no decorative charts.
Done when: an admin can add a category and a complaint type from the UI and then see it used by the routing lookup, and svelte-check passes.
```

**Reqs:** FR-19, NFR-10, AC-17.

---

## D1-08 · Access sharing

**Read:** `docs/spec/M05-api.md` (13.2 access endpoints), `docs/spec/M04-data-model.md` (ticket_access, access_requests), `docs/spec/M07-notifications.md` (15.1)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.2 (access-requests), docs/spec/M04-data-model.md (ticket_access, access_requests), docs/spec/M07-notifications.md section 15.1 and docs/spec/M10-shared-contracts.md.

Task: implement ticket access sharing (decision D-13).
Backend:
- POST /tickets/{ref}/access-requests (staff): creates a pending request. A staff member does not have access yet, so the endpoint must work from the ref alone and must NOT leak any ticket details; return the same generic success response whether or not the ref exists, and block duplicate pending requests. Emit access.requested to the ticket owner via emit_event.
- GET /access-requests: staff see requests awaiting THEIR approval, admin sees all.
- POST /access-requests/{id}/decide (owner or admin): approve creates a ticket_access row with permission edit, deny records it. Emit access.decided to the requester. Audit both.
- Extend can_access so approved helpers can view and edit. Secondary departments (view-only) are created by the routing engine as ticket_access view rows; make sure can_access honours them.
UI: /access page with "Request access by ticket ref" and the pending approvals list (approve/deny buttons). Show shared tickets in the staff ticket list (D3 owns the list; just make sure the API includes them).
Tests: B requests, A approves, B can edit; C still gets 404; deny path; duplicates; audit rows.
Done when: AC-13 passes end to end.
```

**Reqs:** FR-18, AC-13. *(If D3-06 is late, stub `emit_event` per M10.)*

---

## D1-09 · Auto-close and purge

**Read:** `docs/spec/M02-domain-rules.md` (9.1, 9.5), `docs/spec/M08-security-and-config.md`, `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md sections 9.1 and 9.5, docs/spec/M10-shared-contracts.md and docs/spec/M04-data-model.md.

Task: implement retention.
1. ARQ cron auto_close_resolved() hourly: tickets Resolved for AUTO_CLOSE_DAYS (get_setting) with no client reply -> call transition(ticket, "Closed", actor=system). Never set status directly.
2. ARQ cron purge_closed() hourly: for Closed tickets with purged_at IS NULL: replace message bodies with a placeholder text, delete attachment files from storage and mark attachments rows, null ocr_text and embedding, and clear the summary when the ticket's category is in setting purge_summary_categories. KEEP ref, category, type, priority, department, assignment history, timestamps, status history, summary (otherwise) and the audit log. Set purged_at, write an audit entry. Idempotent and safe to re-run; each ticket in its own transaction.
3. A helper can_reopen(ticket) -> ReopenDecision: Resolved or Closed within REOPEN_WINDOW_DAYS may reopen; beyond it a new linked ticket (link_type followup) is required. D2 calls this from thread matching. Document that a purged ticket reopens without its old content.
4. GET /attachments/{id} must return 410 Gone after purge.
Tests: close then purge leaves no bodies/files but keeps metadata+audit; CAT-03 summary cleared, CAT-01 summary kept; re-running changes nothing; reopen within and outside the window.
Done when: AC-14 passes.
```

**Reqs:** FR-22, D-18, AC-14.

---

## D1-10 · Notification UI

**Read:** `docs/spec/M07-notifications.md`, `docs/spec/M05-api.md` (13.5), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M07-notifications.md section 15 and docs/spec/M05-api.md section 13.5. Reuse the API client and layout in frontend/src/lib.

Task: build the live notification experience in SvelteKit.
- A WebSocket client (frontend/src/lib/ws.ts) connecting to /ws?token= with automatic reconnect (exponential backoff) and token refresh on reconnect. Events: ticket.assigned, ticket.updated, ticket.escalated, ticket.reopened, access.requested, ack.timeout, system.alert.
- A Svelte store for notifications: loads GET /notifications on start (so missed events appear), merges live events, tracks unread count.
- Components: bell icon with unread badge in the layout, dropdown list with mark-as-read (POST /notifications/{id}/read), toast on new events with a link to /tickets/[ref], and for ticket.assigned an "Acknowledge" button on the toast that calls POST /tickets/{ref}/acknowledge.
- A connection-status indicator.
Tests: component/store tests for merge and unread logic; svelte-check passes.
Done when: assigning a ticket in the backend pops a toast without a page refresh (demo it).
```

**Reqs:** FR-09, NFR-03.

---

## D1-11 · Admin dashboard (API and UI)

**Read:** `docs/spec/M05-api.md` (13.3), `docs/spec/M01-requirements.md` (FR-16), `docs/spec/M09-testing-and-release.md` (AC-12)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.3, docs/spec/M01-requirements.md FR-16, and AC-12 in docs/spec/M09-testing-and-release.md.

Task: GET /api/v1/dashboard/admin (admin only) and the /admin/dashboard page.
Return: ticket counts by status, category, department and age bucket (<1h, 1-4h, 4-24h, 1-3d, >3d); lists of unacknowledged tickets, uncategorised (needs_triage) tickets and overdue tickets (resolve_due_at passed); workload per staff (open tickets, unacknowledged count, recent ACK_TIMEOUT count); ingestion health: last IMAP poll time (Redis imap:last_poll), queue depth (Redis queue:depth), worker heartbeat, count of failed notifications, any degraded flags under status:* keys.
UI: simple tables and number cards, a degraded-state banner when ingestion health is bad, links into tickets. No decorative charts.
Efficient SQL (grouped counts, no N+1). Tests: fixture with known tickets, API counts equal database counts exactly.
Done when: AC-12 passes and counts match the fixture.
```

**Reqs:** FR-16, AC-12.

---

## D1-12 · Production deployment, backups, monitoring

**Read:** `docs/spec/M09-testing-and-release.md` (24, 25), `docs/spec/M08-security-and-config.md`, D3-01 staging files

```text
Read AGENTS.md, docs/spec/M09-testing-and-release.md sections 24 and 25, docs/spec/M08-security-and-config.md and the existing deploy/ folder (staging files from D3-01).

Task: produce everything needed for the production release (you cannot provision the VM; generate files and scripts and list the manual steps).
1. deploy/docker-compose.prod.yml: pinned image tags, restart policies, resource limits, persistent volumes, no exposed DB/Redis ports, log rotation (json-file max-size/max-file).
2. deploy/Caddyfile for production with automatic HTTPS and WSS proxying.
3. deploy/deploy.sh: take a database backup, run `alembic upgrade head`, pull the tagged images, restart, wait for /health green, and roll back to the previous image tag on failure.
4. deploy/backup.sh + cron: daily pg_dump, encrypted (age or gpg, key from env), copied to separate storage location, 30-day retention (BACKUP_RETENTION_DAYS). deploy/restore.sh and a documented restore test.
5. Monitoring: an external uptime check configuration for /health, instructions for alert email, and an email alert when the worker heartbeat or IMAP poll is stale (small script or health endpoint extension).
6. docs/production-checklist.md: the manual steps (VM, firewall 80/443 + SSH allow-list, DNS, .env with secrets, rotate seeded admin password) and the go-live checklist from section 25.
Done when: a dry run on the staging VM completes deploy, backup, restore and rollback, with output pasted in docs/production-checklist.md.
```

**Reqs:** NFR-08, NFR-11, section 24.
