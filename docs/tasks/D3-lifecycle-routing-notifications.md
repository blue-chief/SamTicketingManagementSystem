# D3 · Ticket Lifecycle, Routing and Notifications

**You own:** the ticket state machine and ticket service, the ticket API, routing, scheduler timers (acknowledgement and resolution deadlines), the notification core (events, WebSocket, email, client emails), the staff UI, admin reassignment, the security fast path, staging deployment, and handover documentation.

**Study first (about 2 hours):** `M00`, `M03`, `M02` (section 9 fully), `M07`, `M05` (13.2, 13.5), `M10`. Then `M04` (tickets, messages, ticket_assignments, notifications).

**How to use this file:** one agent session per task. Paste the "Prompt" block, point the agent at the "Read" files, review the diff, run tests, merge.

| Task | Sprint / Days | Depends on | Task |
|---|---|---|---|
| D3-01 | S1 · Day 4-5 | D1-01 | Staging environment and CD |
| D3-02 | S1 · Day 2-3 | D1-02, D1-05 | State machine and ticket service |
| D3-03 | S1 · Day 4 | D3-02, D1-04 | Ticket API |
| D3-04 | S1 · Day 1-5 | D1-01 | Svelte shell, login, ticket list and detail (read-only) |
| D3-05 | S2 · Day 6 | D3-02, D1-03 | Routing engine |
| D3-06 | S2 · Day 7-8 | D3-02 | Notification core, WebSocket, email, client emails |
| D3-07 | S2 · Day 8-9 | D3-05, D3-06 | Scheduler: acknowledgement and resolution timers |
| D3-08 | S2 · Day 9-10 | D3-03, D3-04 | Staff dashboard and ticket work UI |
| D3-09 | S3 · Day 11 | D3-05, D3-06 | Security fast path |
| D3-10 | S3 · Day 11-12 | D3-05 | Admin reassignment (API and UI) |
| D3-11 | S3 · Day 12 | D3-06 | Profile, availability, system alerts |
| D3-12 | S3 · Day 13 | all | Handover documentation |

**Hand-offs you owe others (critical path):** `create_ticket_from_email`, `append_message`, `transition`, `apply_analysis` by end of **Day 3** (D2-04, D2-07 wait on them). `route_ticket` and `emit_event` stubs with the final signatures on Day 2, real versions Day 6-8. Channel registry by Day 7 so D2-08 can register SMS/WhatsApp. Frontend shell, API client and shared components by Day 5 (D1-07, D1-10, D2-10 reuse them).

---

## D3-01 · Staging environment and CD

**Read:** `docs/spec/M03-architecture-and-setup.md`, `docs/spec/M09-testing-and-release.md` (section 24)

```text
Read AGENTS.md, docs/spec/M03-architecture-and-setup.md, docs/spec/M09-testing-and-release.md section 24 and the existing deploy/ folder.

Task: staging deployment (the VM and DNS are provisioned manually by the team; generate everything else and list the manual steps in docs/staging-setup.md).
1. deploy/docker-compose.staging.yml (api, worker, postgres, redis, frontend, caddy), staging env example, no database or Redis ports exposed.
2. deploy/Caddyfile for staging with automatic HTTPS and WebSocket proxying (/ws) to the api.
3. A GitHub Actions workflow: on merge to main, build images, push to the registry, SSH to the VM and run deploy/deploy-staging.sh (pull, `alembic upgrade head`, restart, wait for /health).
4. docs/staging-setup.md: VM sizing (4 vCPU, 16 GB), firewall (80/443 + SSH allow-list), creating the deploy user, secrets handling, first-run seed command.
Done when: a push to main deploys and https://<staging>/health returns ok.
```

**Reqs:** NFR-07, section 24.

---

## D3-02 · State machine and ticket service

**Read:** `docs/spec/M02-domain-rules.md` (9.1, 9.5), `docs/spec/M10-shared-contracts.md`, `docs/spec/M04-data-model.md`

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md section 9.1 (statuses and transition table), docs/spec/M10-shared-contracts.md (D3 section) and docs/spec/M04-data-model.md (tickets, messages, ticket_assignments).

Task: implement backend/app/services/tickets.py. THIS IS THE ONLY PLACE TICKET STATUS CHANGES.
1. transition(session, ticket, to_status, *, actor, reason_code=None, resolution_notes=None): data-driven allowed-transitions table copied from section 9.1 (including Resolved/Closed -> Reopened, Reopened -> Assigned, Assigned -> Assigned for reassignment). Illegal moves raise IllegalTransition. Requires resolution_notes for Resolved. Sets timestamps (ack_at, resolved_at, closed_at, resolve_due_at when work starts using priority_sla). Writes an audit entry (log_audit) and emits an event through emit_event (use a no-op STUB(owner D3) until D3-06). Row-lock the ticket (SELECT ... FOR UPDATE) to avoid races.
2. create_ticket_from_email(session, msg: IncomingMessage) -> Ticket: get-or-create the client by email, generate the ref with next_ticket_ref(), create the first message with attachments, status Submitted, needs_triage = true until analysed, audit entry.
3. append_message(session, ticket, msg) -> Message and add_outbound_message / add_internal_note helpers.
4. apply_analysis(session, ticket, analysis) -> Ticket: writes category, type, department (from the mapping/override), priority, confidence, summary, needs_triage as in M10.
5. set_assignee(session, ticket, user, reason_code): inserts a ticket_assignments row, closes the previous one, sets assignee_id, assigned_at and ack_deadline_at = now + ACK_TIMEOUT_MINUTES (get_setting), increments reassign_count for ACK_TIMEOUT, audits.
Tests: every legal transition passes, every illegal pair is rejected (table-driven over the full matrix), audit rows exist, concurrency test (two simultaneous transitions), resolution notes required.
Done when: D2 can call create_ticket_from_email and apply_analysis. Merge this by end of Day 3.
```

**Reqs:** FR-04, FR-23, section 9.1.

---

## D3-03 · Ticket API

**Read:** `docs/spec/M05-api.md` (13.2), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.2 and docs/spec/M10-shared-contracts.md.

Task: implement these endpoints using D1's get_current_user, require_ticket_access and can_access, and your ticket service:
- GET /tickets (staff: assigned + shared only; admin: all) with filters status, category, department, priority, assignee, age_bucket, needs_triage, q (safe parameterised search over ref, subject, summary), pagination and sort.
- GET /tickets/{ref}: summary, messages as a thread chain, attachments (metadata), links (related/duplicate/followup), assignment history, audit entries (admin only for full audit).
- PATCH /tickets/{ref}/status (assignee, edit-access staff, admin) -> transition() only.
- POST /tickets/{ref}/acknowledge (assignee) -> sets ack_at and moves Assigned to In Progress via transition().
- POST /tickets/{ref}/messages: kind reply (creates an outbound message and enqueues send_client_email; subject carries [TKT-ref]) or internal note.
- GET /tickets/{ref}/links, GET /attachments/{id} (download with Content-Disposition attachment; D1-09 adds the 410 after purge).
Reuse the exact response schemas in backend/app/schemas/ so the frontend can type them. 404 (not 403) for tickets the user cannot access.
Tests: RBAC matrix per endpoint, staff cannot read others' tickets by ref, filters, pagination, acknowledge flow, illegal status change returns code ILLEGAL_TRANSITION.
Done when: all endpoints are documented in OpenAPI and tests pass.
```

**Reqs:** FR-15, FR-17 (partly), FR-21, D-13, AC-11.

---

## D3-04 · Svelte shell, login, ticket list and detail

**Read:** `docs/spec/M10-shared-contracts.md` (section 5), `docs/spec/M05-api.md`

```text
Read AGENTS.md, docs/spec/M10-shared-contracts.md section 5 and docs/spec/M05-api.md (13.1, 13.2).

Task: build the SvelteKit + TypeScript frontend foundation. Other developers will build on it, so keep it clean and documented in frontend/README.md.
1. API client (frontend/src/lib/api.ts): base URL from env, JWT access + refresh handling with automatic refresh and one retry on 401, typed error shape { detail, code }, typed functions for auth and tickets. Generate or hand-write types from the OpenAPI schema.
2. Auth store, route guards, role-aware layout and navigation (staff vs admin menus; menu entries for admin pages D1/D2 will add can already be listed and point to placeholder pages).
3. Pages: /login (including the forced password-change flow), /tickets (list with filters, pagination), /tickets/[ref] (read-only detail: summary, message thread, attachments, links). Show emails as plain text only.
4. Shared components: StatusBadge, PriorityBadge, DataTable, Pagination, ErrorBanner, Modal, ConfirmButton, a Toast host placeholder (D1-10 fills it).
5. Until the real API exists (Day 2-4), develop against mock data behind a feature flag, then switch.
Desktop first (Chrome, Edge, Firefox). svelte-check must pass.
Done when: staff and admin can log in; admin sees all tickets, staff sees only theirs; others can import the shared components.
```

**Reqs:** FR-15, NFR-09.

---

## D3-05 · Routing engine

**Read:** `docs/spec/M02-domain-rules.md` (8, 9.3), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md sections 8 and 9.3, and docs/spec/M10-shared-contracts.md.

Task: implement backend/app/services/routing.py: route_ticket(session, ticket) -> RoutingResult and reassign_next(session, ticket, reason_code, *, actor).
route_ticket (spec 9.3 steps 1-5):
1. Primary department = complaint type override if set, else the category's primary department. Secondary departments become ticket_access rows with permission view and trigger a notification.
2. Eligible staff: active, role staff, in that department, available = true, not on leave (on_leave_until null or past), not the ticket's excluded users.
3. Pick the eligible staff with the fewest open tickets (statuses Assigned, In Progress, Pending Client Response, Escalated, Reopened); break ties by oldest last assignment (ticket_assignments.assigned_at).
4. None eligible -> the department's backup staff (is_backup).
5. Still none -> admin queue (assignee null, status Submitted) and emit system.alert / alert the admin.
Assign through set_assignee, then transition Submitted -> Assigned (or Reopened -> Assigned), reason code ROUTED, then emit ticket.assigned.
reassign_next (step 6): exclude everyone who already has an ACK_TIMEOUT assignment on this ticket (from ticket_assignments), backup first when nobody else is free; after MAX_AUTO_REASSIGN timeouts, transition to Escalated and alert the admin. Reason codes ROUTED, ACK_TIMEOUT, STAFF_UNAVAILABLE, ADMIN.
Use SELECT ... FOR UPDATE SKIP LOCKED style safety so two tickets routed at once do not both pick the same last person incorrectly.
Tests: table-driven for every branch (least loaded, tie-break, backup, admin fallback, type override, secondary view-only rows, on leave, unavailable, exclusion of timed-out staff, escalate after 2).
Done when: AC-01 routing part and AC-07 selection logic pass.
```

**Reqs:** FR-08, FR-10, AC-01, AC-07.

---

## D3-06 · Notification core, WebSocket, email, client emails

**Read:** `docs/spec/M07-notifications.md` (all), `docs/spec/M05-api.md` (13.5), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M07-notifications.md (all of section 15), docs/spec/M05-api.md section 13.5 and docs/spec/M10-shared-contracts.md.

Task: implement backend/app/notifications/.
1. emit_event(session, event, ticket, *, recipients=None, payload=None): resolves default recipients per table 15.1, creates a notifications row per user per enabled channel (users.channels), enqueues send_notification(notification_id).
2. NotificationChannel ABC and registry (section 15.2). Implement InAppChannel (writes the row and pushes over WebSocket) and EmailChannel (aiosmtplib using SMTP_* settings). Leave SMS and WhatsApp as registered stubs returning False with a clear "not configured" log (D2-08 replaces them).
3. WebSocket hub: GET /ws?token= (validate JWT), per-user connections, Redis pub/sub so it works with multiple API processes, event types listed in section 13.5. In-app delivery must be under 2 seconds from assignment (test it).
4. Retry with backoff 10 s, 30 s, 90 s via ARQ; after the final failure mark the notification failed, write an audit/system flag and show the ticket as unacknowledged for the admin dashboard. Store attempts, last_error (no personal data), sent_at.
5. Endpoints GET /notifications (own), POST /notifications/{id}/read.
6. Client emails (section 15.4): job send_client_email(message_id): auto-acknowledgement "[TKT-000124] We received your complaint" with no complaint details, and staff replies sent with the same [ref] in the subject and proper In-Reply-To/References headers so replies thread; store Message-ID on the outgoing message.
7. Message templates for each event in a single templates module (short, no sensitive content in SMS/WhatsApp).
Tests: fan-out per user channel preferences, retry then failure flag, WebSocket delivery latency, client acknowledgement content, reply threading headers. Mock SMTP.
Done when: AC-01 notification part and AC-08 pass; D1-10 and D2-08 can integrate.
```

**Reqs:** FR-09, FR-20, FR-21, NFR-03, NFR-04, AC-08.

---

## D3-07 · Scheduler: acknowledgement and resolution timers

**Read:** `docs/spec/M02-domain-rules.md` (9.1-9.3), `docs/spec/M01-requirements.md` (FR-10, FR-11), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md sections 9.1 to 9.3, docs/spec/M01-requirements.md FR-10 and FR-11, and docs/spec/M10-shared-contracts.md section 3.

Task: implement the ARQ cron jobs in backend/app/workers/.
1. check_ack_timeouts() every 30 s: tickets in Assigned with ack_deadline_at < now. For each, in its own transaction with SELECT ... FOR UPDATE SKIP LOCKED: write an audit ACK_TIMEOUT entry (reason_code ACK_TIMEOUT, previous assignee in detail), call reassign_next (D3-05), emit ack.timeout to the previous assignee and admin, ticket.reassigned to the new assignee. After MAX_AUTO_REASSIGN, transition to Escalated and alert the admin. Idempotent: running twice never double-reassigns.
2. check_resolve_deadlines() every 60 s: tickets In Progress (or Pending Client Response excluded from the clock, as configured) with resolve_due_at < now -> transition to Escalated, emit ticket.escalated to assignee and admin. resolve_due_at is set when work starts from priority_sla.
3. A user who is acknowledged-by-opening the ticket (status In Progress) is never timed out.
4. All timings from get_setting/priority_sla so tests can set the acknowledge timeout to 1 minute.
5. Publish queue:depth to Redis every minute for the health endpoint.
Tests with a fake clock: timeout moves to the next staff then to backup, second timeout escalates, acknowledged tickets are untouched, audit entries and reason codes correct, resolve escalation, double-run idempotency.
Done when: AC-07 passes: with the timeout set to 1 minute an ignored ticket moves to backup and is logged.
```

**Reqs:** FR-10, FR-11, AC-07.

---

## D3-08 · Staff dashboard and ticket work UI

**Read:** `docs/spec/M05-api.md` (13.3), `docs/spec/M01-requirements.md` (FR-15, FR-21), `docs/spec/M09-testing-and-release.md` (AC-11)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.3, docs/spec/M01-requirements.md FR-15 and FR-21, and AC-11 in docs/spec/M09-testing-and-release.md. Reuse the shared components and API client you built in D3-04.

Task:
1. GET /dashboard/staff: counts by status and priority for the user's own and shared tickets, due soon (next 2 hours or 25 percent of the limit), overdue, shared with me, and the number of pending access requests awaiting their approval.
2. /dashboard page (staff landing): number cards and short lists linking into tickets; the acknowledge button for tickets awaiting acknowledgement with a countdown to ack_deadline_at.
3. Extend /tickets/[ref] into the working screen: summary (with confidence), full thread chain in order, attachments (download links), linked tickets, assignment history; actions: Acknowledge, change status (Pending Client Response, Resolve with required resolution notes, Close for allowed roles), reply to the client (sent by email) and add internal note; hide actions the user's permission or the state machine does not allow (use the allowed-transitions endpoint or response). Show clear Escalated and overdue badges.
4. All email content rendered as plain text.
Tests: staff dashboard counts, component tests for action visibility, svelte-check.
Done when: a staff member can take a ticket from Assigned to Resolved entirely in the UI (S2 exit demo).
```

**Reqs:** FR-15, FR-21, AC-11.

---

## D3-09 · Security fast path

**Read:** `docs/spec/M00-context-and-decisions.md` (D-16, O-06), `docs/spec/M01-requirements.md` (FR-24), `docs/spec/M07-notifications.md` (15.1)

```text
Read AGENTS.md, docs/spec/M00-context-and-decisions.md D-16 and O-06, docs/spec/M01-requirements.md FR-24, docs/spec/M07-notifications.md section 15.1 and the priority rules in docs/spec/M02-domain-rules.md 9.2.

Task: security complaint fast path.
1. For any ticket in CAT-06 (also System downtime and Suspected account compromise are Critical but follow normal routing): priority is Critical (never lowered by other rules), routed immediately without waiting for any batching or queue delay, and the event ticket.security is emitted to every active user flagged is_incident_contact and to all admins on ALL channels at once (in-app, email, SMS, WhatsApp), ignoring per-user channel preferences for this event.
2. The ticket is still routed to its department (DEP-05, DEP-02 secondary) as normal, the Critical acknowledgement (10 min) and resolve (4 h) limits apply.
3. If no incident contact is configured, fall back to admins and raise system.alert so it gets configured.
4. Never include complaint content in SMS/WhatsApp.
Tests: CAT-06 ticket produces ticket.security notifications on all channels within the target, no incident contact fallback, non-security ticket does not trigger it.
Done when: AC-15 passes.
```

**Reqs:** FR-24, D-16, AC-15.

---

## D3-10 · Admin reassignment (API and UI)

**Read:** `docs/spec/M05-api.md` (13.2), `docs/spec/M02-domain-rules.md` (9.3 point 7), `docs/spec/M01-requirements.md` (FR-17)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.2 (reassign), docs/spec/M02-domain-rules.md section 9.3 and docs/spec/M01-requirements.md FR-17.

Task:
1. POST /tickets/{ref}/reassign (admin only): body user_id and reason (required). Validate the target is active staff (any department allowed, but warn in the response if outside the ticket's department). Use set_assignee and transition (Assigned -> Assigned) with reason_code ADMIN; audit with the reason; emit ticket.reassigned to previous and new assignee.
2. When a staff member is set unavailable or put on leave (PATCH /me or admin edit), automatically reassign their open, unacknowledged tickets with reason_code STAFF_UNAVAILABLE (a small service hook D1's user update and your PATCH /me both call).
3. UI: a "Reassign" action on /tickets/[ref] for admins (modal with staff dropdown showing department and current open-ticket count, reason textarea) and a "reassign" shortcut from the admin dashboard lists.
Tests: admin-only, reason required, audit row, notifications, auto-reassignment on unavailability.
Done when: the admin can reassign any ticket with a reason and the history shows it.
```

**Reqs:** FR-17, UC-12.

---

## D3-11 · Profile, availability, system alerts

**Read:** `docs/spec/M05-api.md` (13.1), `docs/spec/M07-notifications.md` (15.1), `docs/spec/M01-requirements.md` (FR-25)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.1, docs/spec/M07-notifications.md section 15.1 and docs/spec/M01-requirements.md FR-25.

Task:
1. /profile page: edit phone, WhatsApp number, notification channels (in-app, email, SMS, WhatsApp), availability toggle and on-leave-until date, using PATCH /me. Validate numbers; warn that WhatsApp requires opt-in.
2. system.alert generation (backend/app/services/system_alerts.py): a cron every minute checks Redis health flags and DB state (IMAP last poll older than 3x poll interval, queue depth above a threshold, dead-letter count, failed notifications spike, worker heartbeat stale) and emits system.alert to admins (in-app + email) once per incident, with a recovery message when it clears (avoid alert storms; store alert state in Redis).
3. Expose the degraded flags in /health and ensure the D1-11 dashboard can read them.
Tests: alert fires once, recovery message, preference changes change fan-out channels.
Done when: stopping IMAP produces one alert and the dashboard shows the degraded state; restoring clears it.
```

**Reqs:** FR-25, NFR-11, D-12.

---

## D3-12 · Handover documentation

**Read:** `docs/spec/M09-testing-and-release.md` (26), `docs/spec/M08-security-and-config.md` (Appendix B)

```text
Read AGENTS.md, docs/spec/M09-testing-and-release.md section 26 (handover), docs/spec/M08-security-and-config.md Appendix B, docs/spec/M06-ingestion-and-ai.md 14.5 and everything in docs/ so far.

Task: write the handover package by inspecting the actual code and configs (do not invent commands: run them or read the scripts).
- README.md: what it is, architecture summary, run locally, run tests, deploy.
- docs/runbook.md: restart services, check queue depth and dead letters, rotate secrets, restore a backup, what to do when IMAP, Redis or an SMS/WhatsApp gateway is down, read logs.
- docs/admin-guide.md (one page, plain language): add a department, category and complaint type, add users and backup staff, set the incident contact, change limits, handle the Uncategorised queue, read the audit log and excuse a timeout.
- docs/config-reference.md from Appendix B plus the settings table.
- docs/privacy-note.md draft: lawful basis, retention and purge, backup retention (30 days), access control, flagged for legal review against NDPA and GDPR.
- docs/known-limitations.md from section 14.5 and the final cut-line status.
Done when: someone who has never seen the project can run, deploy and administer it using only these documents.
```

**Reqs:** section 26.

---

## ALL-01 · Acceptance run (all three developers, Day 14)

Run every criterion AC-01..AC-18 from `docs/spec/M09-testing-and-release.md` with the firm on staging. Tick the UAT checklist in section 25. Record each result in `docs/acceptance-report.md`: pass, or a written and agreed exception. Fix findings on Day 15, then go live using D1-12's checklist.
