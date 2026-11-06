# M09 · Testing, acceptance, deployment, UAT, handover, risks, backlog

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** Everyone; D1/D3 for deployment

---

## 23. Testing and acceptance

### 23.1 Test layers

| Layer | What | Tooling |
|---|---|---|
| Unit | State machine, routing rules, priority rules, filters, thresholds | pytest |
| API | Auth and RBAC matrix (every role against every endpoint), validation, error shapes | pytest and httpx AsyncClient |
| Pipeline | Email in, ticket out, using fixture emails (replies, duplicates, spam, empty, screenshot-only, oversized, corrupted, multi-language characters) | pytest and `scripts/send_test_emails.py` |
| AI evaluation | Accuracy and time per email on the labelled set | `scripts/eval_analyzer.py` |
| Load and resilience | 500 emails an hour, IMAP, Redis and gateway failures | `scripts/load_test.py` |
| Frontend | Type check and a few end-to-end smoke flows (login, open ticket, acknowledge, reply) | svelte-check, Playwright (optional) |
| Security | RBAC bypass attempts, file upload abuse, login brute force | Manual checklist plus tests |

### 23.2 Acceptance criteria (Given-When-Then)

| ID | Criterion | Reqs |
|---|---|---|
| AC-01 | **Given** a client emails a duplicate-charge complaint, **when** it arrives, **then** a ticket is created within about a minute, categorised CAT-03 / Duplicate charges, with a summary, routed to Finance & Billing, and the assignee is notified in-app in under 2 seconds. | FR-01, FR-04, FR-06, FR-08, FR-09 |
| AC-02 | **Given** an email with a screenshot and little text, **when** it is processed, **then** the OCR text is used for classification and the screenshot is attached to the ticket. | FR-05 |
| AC-03 | **Given** an email with no text and no attachments, **when** it arrives, **then** no ticket is created and the ingest log records it as empty. | FR-02 |
| AC-04 | **Given** an auto-reply or a blocklisted sender, **when** it arrives, **then** it is filtered and logged. | FR-02 |
| AC-05 | **Given** an attachment over 10 MB, a disallowed type, or a corrupted file, **when** it arrives, **then** the file is rejected and flagged, and the ticket is still created from the text. | FR-03 |
| AC-06 | **Given** the analyser is not confident, **when** the ticket is processed, **then** it appears in the Uncategorised queue and the admin is alerted. | FR-07 |
| AC-07 | **Given** an assigned ticket is not acknowledged within 10 minutes, **when** the timer fires, **then** it is reassigned to the next available or backup staff and the audit log records the reason. | FR-10 |
| AC-08 | **Given** a notification channel fails, **when** retries are exhausted, **then** the ticket is flagged unacknowledged on the admin dashboard. | FR-09 |
| AC-09 | **Given** a client replies to an existing thread, **when** it arrives, **then** it is appended to the old ticket (not a new ticket) and the assignee is notified. | FR-12 |
| AC-10 | **Given** the same client resends an identical message, **when** it arrives, **then** it is discarded and logged. **Given** different wording or new context, **then** it is linked to the earlier ticket. | FR-13 |
| AC-11 | **Given** a staff member, **when** they request the ticket list, **then** they see only tickets assigned to or shared with them. | FR-15, D-13 |
| AC-12 | **Given** pending tickets exist, **when** the admin opens the dashboard, **then** they see pending tickets by category, department, assignee, and age, with unacknowledged and overdue lists. | FR-16 |
| AC-13 | **Given** staff B requests access to staff A's ticket, **when** A approves, **then** B can view and edit it. | FR-18 |
| AC-14 | **Given** a ticket moves to Closed, **when** the purge job runs, **then** message bodies and attachment files are removed while metadata and the audit log remain. | FR-22 |
| AC-15 | **Given** a security-category complaint, **when** it is processed, **then** it is Critical and the incident contact and admin are notified on all channels immediately. | FR-24 |
| AC-16 | **Given** the mailbox or the network is down, **when** service returns, **then** all queued emails are processed once, in order, and the admin dashboard shows the state throughout. | FR-25 |
| AC-17 | **Given** the admin adds a category and complaint type, **when** the next matching email arrives, **then** it can be classified and routed without any code change. | FR-19 |
| AC-18 | **Given** 500 emails arrive within an hour, **when** processing completes, **then** there are no lost or duplicated tickets. | NFR-05, NFR-06 |


## 24. Deployment

| Item | Setting |
|---|---|
| Environments | Local (Docker Compose), Staging (deployed on every merge to `main`), Production (deployed by a tagged release) |
| Server | One Linux VM, 4 vCPU and 16 GB RAM recommended (8 GB if no LLM), with a firewall allowing only 80 and 443 (and SSH from known addresses) |
| Proxy | Caddy with automatic HTTPS |
| Database | PostgreSQL in Compose with a persistent volume. Daily encrypted `pg_dump` to separate storage, 30-day retention. Test a restore before go-live |
| Secrets | `.env` on the server, readable only by the deploy user. Rotate the seeded admin password at first login |
| Migrations | `alembic upgrade head` as a step in the deploy script. Backup first |
| Monitoring | External uptime check on `/health`. Worker heartbeat. Admin dashboard shows last IMAP poll time and queue depth. Email alert on failure |
| Logging | Structured JSON logs with rotation. No message bodies or personal data in logs |
| Rollback | Keep the previous image tag. Roll back the image, and restore the database only if a migration was destructive |


## 25. UAT and go-live checklist

**UAT (Day 14, with the firm on staging)**

- [ ] The firm's staff accounts and departments are created, with backups and the incident contact set
- [ ] The firm sends real-format complaints (anonymised) covering all six categories
- [ ] Every acceptance criterion in section 23.2 is demonstrated
- [ ] The firm reviews and accepts the limitations in section 14.5
- [ ] Open items O-01 to O-12 are confirmed or the defaults are accepted in writing
- [ ] The retention and purge behaviour is confirmed with legal

**Go-live (Day 15)**

- [ ] Production environment deployed and `/health` is green
- [ ] Real mailbox settings entered, test email processed end to end
- [ ] SMS and WhatsApp production API keys and approved templates configured, one live message sent to each
- [ ] Seeded passwords changed, admin accounts verified
- [ ] Backup ran once and a restore was tested
- [ ] Uptime check and alert recipients configured
- [ ] Cut-over plan agreed: choose a moment, point the shared inbox at the system, tell the two IT desk staff their new role (they become ordinary staff with their own queues), and keep the old inbox readable for one week as a fallback
- [ ] First 24 hours: a developer watches the dashboard, queue depth, and notification failures


## 26. Handover

Deliver to the firm and keep in the repository:

- `README.md`: how to run locally, how to deploy
- Runbook: restart services, check the queue, rotate secrets, restore a backup, what to do when IMAP or a gateway is down
- Admin guide (one page): add a department, category and type, add users and backups, change limits, handle the Uncategorised queue, read the audit log
- Configuration reference: Appendix B, with defaults
- Test report: AI evaluation results and load test results
- Known limitations (section 14.5) and the post-release backlog (section 28)


## 27. Risks and cut-line

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Classifier accuracy too low on real emails | Medium | High | Early evaluation, gate at D2-09, low-confidence emails go to the admin queue, add labelled examples quickly |
| Sprint 2 overloaded (D1 and D2) | High | High | Daily rebalance, contract-first API, cut-line below |
| WhatsApp approval or provider delays | Medium | Medium | Adapter plus sandbox. Ship with live keys if ready, otherwise in-app, email and SMS go live first |
| Real mailbox details arrive late | Medium | Medium | Build and test on a test mailbox from Day 1 |
| Purge conflicts with reporting or legal needs | Medium | Medium | Purge content only, keep metadata and audit, confirm with legal (O-03, O-10) |
| Burst of emails overwhelms analysis | Low | Medium | Queue, backpressure, load test at 500 an hour |
| Staff receive too many notifications | Medium | Low | Per-user channel settings, short messages |

**Cut-line.** The core path is: email to ticket, classify, route, notify, dashboard. If time runs short, drop in this order and tell the firm:

1. Voice transcription (D2-13)
2. LLM summaries and suggested solutions (D2-13)
3. Embedding-based similar-ticket links (keep thread-header linking and exact-duplicate discard)
4. Live WhatsApp (keep the adapter and sandbox)
5. Polish on the access-sharing UI


## 28. Post-release backlog

1. AI auto-reply for light issues (section 14.7), with strict category exclusions
2. Local small LLM summaries and suggested solutions, then vision models for screenshots
3. Voice-recording transcription
4. Additional channels (web form, WhatsApp inbound, phone)
5. Client portal for ticket status
6. SLA analytics and reports, export to CSV
7. Mobile-friendly UI or app
8. Multi-language support
9. Two-factor authentication for staff and admin

---
