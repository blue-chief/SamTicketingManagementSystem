# SamConsultingFirm Ticket Management Tool
## Developer Specification and Build Plan

| | |
|---|---|
| **Version** | 1.0 (2026-10-20) |
| **Team** | 3 developers (D1, D2, D3) |
| **Delivery window** | 3 weeks (15 working days), three 1-week sprints |
| **Stack** | Python / FastAPI, Svelte, PostgreSQL, Redis |
| **Source** | Requirement gathering using the S.C.O.P.E. guide (Sift, Categorize, Outline, Plan for failure, Echo & confirm), stakeholder answers, use case and system analysis |

### How to read this document

Read it in order. It follows the life of the project from start to finish.

| Part | Contents | Use it to |
|---|---|---|
| **A. Context and decisions** (sections 1-5) | What we are building, scope, confirmed decisions, assumptions | Know what is agreed and what is still open |
| **B. Specification** (sections 6-16) | Requirements, rules, architecture, data model, API, AI, notifications, security | Know exactly what to build |
| **C. Build plan** (sections 17-22) | Team roles, repo setup, kickoff, Sprint 1, 2, 3 task lists | Know what to do each day, in order |
| **D. Release** (sections 23-28) | Testing, deployment, UAT, go-live, handover, risks | Ship it |

Every requirement has an ID (`FR-xx`, `NFR-xx`). Every task has an ID (`S1-01`...). Tasks reference requirement IDs so nothing gets built without a reason and nothing is forgotten.

---

# PART A. CONTEXT AND DECISIONS

## 1. Problem and goal

**Problem.** SamConsultingFirm's clients send complaints by email to a shared inbox (about 15-30 a day normally, up to about 50 at peak). Two IT desk staff read every email, decide which department it belongs to, and forward it. Feedback is slow and unpredictable. Clients sometimes resend requests to remind the firm. Similar problems are not recognised as related, and the admin has no visibility.

**Root cause.** There is no structured triage and ownership layer between the inbox and the staff who solve problems.

**Goal.** Replace the manual inbox workflow with a system that turns each complaint email into a ticket, classifies it, summarises it, routes it to the right department and staff member, notifies them immediately, escalates if nobody acts, and gives the admin full visibility.

**Success (minimum).** All "Must" items in section 2 work end to end on the firm's real mailbox.

## 2. Scope

### 2.1 In scope for release 1 (Must)

- Email to ticket (IMAP, any provider)
- Filtering (spam, auto-replies, empty emails, bad attachments)
- Classification (one category, one complaint type, priority), confidence score, and a summary for the assigned staff
- Screenshot reading (OCR) combined with the email text
- Routing: category to department(s) to staff, with backup staff
- Notifications on in-app, email, SMS and WhatsApp
- Acknowledgement tracking and automatic reassignment after 10 minutes
- Resolution time limits by priority, with escalation
- Linking: client replies, duplicates, similar tickets
- Staff dashboard and admin dashboard
- Admin reassignment, admin-managed configuration (departments, categories, types, users)
- Ticket access sharing (request and approve)
- Resolve, close, and purge of sensitive data (keep metadata and audit log)
- Audit log
- Outbound email to clients (auto-acknowledgement and staff replies)

### 2.2 Out of scope for release 1

| Item | Status |
|---|---|
| AI auto-reply to clients for "light" issues | Deferred (design leaves a hook, see section 14.7) |
| Channels other than email (web form, WhatsApp inbound, phone) | Later |
| Mobile app or mobile-optimised UI | Later (build responsive where it is free) |
| Client portal for tracking tickets | Later |
| Voice-recording transcription | Stretch (Could) |
| Automated resolution of payment or transaction problems | Never auto-answered |
| Multi-language support | Later |
| SLA analytics and reports beyond the dashboards | Later |

## 3. Actors and roles

| Actor | Login | Can do |
|---|---|---|
| **Client** | No | Sends emails, receives acknowledgements and replies |
| **Staff** | Yes | See only tickets assigned to them or shared with them. Acknowledge, work, update status, message the client, resolve, share access, request access |
| **Admin** | Yes | See all tickets. Reassign. Triage uncategorised tickets. Manage departments, categories, types, users, backups, priority limits, sender blocklist. View the admin dashboard |
| **System / AI** | Service | Ingest, filter, classify, route, notify, escalate, purge |

## 4. Confirmed decisions

| # | Decision | Source |
|---|---|---|
| D-01 | Email is the only channel for now. Other channels may be added later. | Stakeholder |
| D-02 | Must work with any email provider or domain, using IMAP. | Stakeholder |
| D-03 | The tool replaces the existing inbox workflow. The admin supervises and can reassign. | Stakeholder |
| D-04 | Each ticket has exactly one category. The admin owns and edits categories. | Stakeholder |
| D-05 | Department and category are separate. The category decides the responsible department. | Stakeholder |
| D-06 | Similar tickets are linked, not merged. | Stakeholder |
| D-07 | A client reply on an existing thread is attached to the old ticket as a chain, not as a new ticket and not overwriting the old one. | Stakeholder |
| D-08 | The system reads screenshots, compares them with the written text, and uses both to classify. | Stakeholder |
| D-09 | Empty emails create no ticket. Screenshot-only emails are analysed and become tickets only if an issue is found. | Stakeholder |
| D-10 | Spam, auto-replies and unknown junk are filtered. | Stakeholder |
| D-11 | Attachments: max 10 MB, other and corrupted file types rejected. Voice recordings arrive as attachments (stretch). | Stakeholder |
| D-12 | Staff notified on in-app, email, SMS and WhatsApp. In-app under 2 seconds, external channels within about a minute (best effort). | Stakeholder |
| D-13 | Staff see only their own tickets or those shared with them. Sharing: the helper requests access, the owner approves, and approved helpers can edit. | Stakeholder |
| D-14 | Staff must acknowledge a ticket (or it moves to In Progress when they open and start it) within 10 minutes. Otherwise it goes to the next available or backup staff, and the event is recorded. | Stakeholder |
| D-15 | After work starts, a resolution time limit applies depending on difficulty (priority). | Stakeholder |
| D-16 | Security complaints are escalated immediately. | Taxonomy document |
| D-17 | Payment issues and anything that risks loss are never auto-answered. | Stakeholder |
| D-18 | Compliance: NDPA and GDPR. On resolution, purge content and attachments, keep metadata and audit log. A legal check against NDPA is still recommended. | Stakeholder |
| D-19 | Volume: 15-30 per day normally (5,475-10,950 a year), 50 per day at peak. Must tolerate a burst of 500 emails in an hour without losing any. | Stakeholder |
| D-20 | Desktop first. Cloud hosting approved. | Stakeholder |
| D-21 | AI must run on infrastructure we control (no third-party AI API). The team has no GPU, so the AI is lightweight and runs on the cloud VM. | Stakeholder, team |
| D-22 | SMS and WhatsApp gateways are approved. API keys will be added at the end through configuration. | Stakeholder |
| D-23 | Stack: Python / FastAPI and Svelte. 3 weeks, 3 developers. | Team |

## 5. Proposed defaults and open items

These are the values the plan uses until the firm answers. Every one of them is a configuration value, not hard-coded, so changing them is cheap.

| # | Item | Default used in this plan | Who confirms |
|---|---|---|---|
| O-01 | Resolution limits by priority | Critical 4 h, High 24 h, Medium 72 h, Low 5 days | Firm |
| O-02 | Acknowledgement limit | 10 minutes for all priorities, max 2 automatic reassignments, then Escalated to admin | Firm |
| O-03 | When purge happens | At Closed. Resolved tickets auto-close after 3 days with no client reply, so a late reply can still reopen the ticket with content. | Firm and legal |
| O-04 | Department DEP-06 (HR and Talent Acquisition) has no complaint category in the supplied taxonomy | Seeded but receives no tickets. Needs a decision: add an HR category, or HR is only for staff accounts. | Firm |
| O-05 | Secondary departments (for example Product & Technology on a billing/access complaint) | Added to the ticket as view-only and notified. The primary department owns the ticket. | Firm |
| O-06 | Incident-response contact for security complaints | A named user flagged `incident_contact` | Firm |
| O-07 | PDF attachments (invoices as evidence) | Allowed | Firm |
| O-08 | Meaning of "must run locally" | Privacy: no client data to third-party AI providers. If it is only about cost, a free-tier API could improve summaries later. | Firm |
| O-09 | Cloud VM size | 4 vCPU, 16 GB RAM (8 GB if the small LLM is dropped) | Team and firm |
| O-10 | Backup retention vs. purge | Backups kept at most 30 days, stated in the privacy notice | Firm and legal |
| O-11 | Sample complaint emails for AI evaluation | 30-50 anonymised real ones. If unavailable, the team writes synthetic ones from the taxonomy. | Firm |
| O-12 | Classification accuracy target | At least 80% category accuracy on the test set | Team |

---

# PART B. SPECIFICATION

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Poll the configured IMAP mailbox and ingest each new email exactly once. Processing must be idempotent. |
| FR-02 | Filter automated mail (auto-replies, bounces, bulk), blocklisted senders, and empty emails. Every filtered or discarded email is written to the ingest log with a reason. Nothing is silently dropped. |
| FR-03 | Validate attachments: max 10 MB, allowed types only (png, jpg, jpeg, webp, pdf, and audio mp3/m4a/wav/ogg for the stretch feature), checked by file signature and not just the extension. Corrupted or disallowed files are rejected and flagged on the ticket. The ticket is still created from the text. |
| FR-04 | Create a ticket with reference `TKT-000001` style, status Submitted, linked to the client (created if new). |
| FR-05 | Run OCR on image attachments and combine the extracted text with the email body for analysis. |
| FR-06 | Analyse each ticket and produce category, complaint type, priority, confidence score and a summary. |
| FR-07 | If confidence is below the threshold, set `needs_triage`, place the ticket in the Uncategorised queue and alert the admin. |
| FR-08 | Route to the responsible department(s) and select a staff member (see section 9.3). Use backup staff when needed. |
| FR-09 | Notify the assigned staff on in-app, email, SMS and WhatsApp as the user has enabled. Retry failures. Record delivery status. |
| FR-10 | Track acknowledgement. If a ticket stays unacknowledged for 10 minutes, reassign it, write an audit entry, and notify the new assignee. |
| FR-11 | Track resolution due time by priority. When overdue, set Escalated and notify the assignee and the admin. |
| FR-12 | Match client replies to existing tickets and append them as messages. Reopen if the ticket was Resolved. Move Pending Client Response back to In Progress. |
| FR-13 | Detect duplicates (same sender, same meaning, no new information) and discard them with a log entry. Link when wording or context differs. |
| FR-14 | Link similar tickets from different clients so that one fix can resolve the group. |
| FR-15 | Staff dashboard: own and shared tickets by status, priority, due time, plus access requests awaiting approval. |
| FR-16 | Admin dashboard: all tickets by status, category, department, age, plus unacknowledged, uncategorised, overdue, workload per staff, and ingestion health. |
| FR-17 | Admin can reassign any ticket with a reason. |
| FR-18 | Access sharing: a staff member can request access to a ticket, the owner approves or denies, and approved helpers can edit. |
| FR-19 | Admin can create, edit and deactivate departments, categories, complaint types, category-to-department mapping, users, backup staff, priority limits and the sender blocklist. No code change needed. |
| FR-20 | Send an automatic acknowledgement email to the client with the ticket reference. |
| FR-21 | Staff can reply to the client from the ticket. The reply is sent by email with the reference in the subject and stored in the ticket thread. |
| FR-22 | On resolution flow completion (Closed), purge message bodies and attachment files. Keep ticket metadata and the audit log. |
| FR-23 | Write an audit log entry for assignment, reassignment, status changes, timeouts, access changes, purges, and configuration changes. |
| FR-24 | Security-category tickets are Critical, skip normal queueing, and notify the incident contact and the admin immediately on all channels. |
| FR-25 | If the mailbox, network, AI or a notification channel is down, work is queued and processed when service returns. The admin dashboard shows the state. |
| FR-26 | (Stretch) Transcribe voice recordings locally and include the text in analysis. |

## 7. Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Ingestion latency | Email becomes a ticket within poll interval (default 30 s) plus processing |
| NFR-02 | Analysis time | p95 at or under 10 seconds per email (baseline analyser) |
| NFR-03 | In-app notification | Under 2 seconds from assignment |
| NFR-04 | External notification | Within about 1 minute, best effort, with retries |
| NFR-05 | Capacity | 50 emails/day comfortably. Burst of 500 per hour queued with zero loss |
| NFR-06 | Reliability | No email lost or processed twice across restarts |
| NFR-07 | Security | Role-based access enforced on the server for every ticket endpoint. Hashed passwords. HTTPS only. Secrets in environment. |
| NFR-08 | Compliance | NDPA and GDPR: purge on closure, access control, audit trail, documented backup retention |
| NFR-09 | Devices | Desktop browsers (current Chrome, Edge, Firefox) |
| NFR-10 | Configurability | Taxonomy, limits and thresholds changeable without code changes |
| NFR-11 | Observability | Health endpoint, structured logs, dashboard shows last poll time and queue depth |

## 8. Taxonomy (seed data)

Departments and categories are separate. The department decides who handles the ticket. The category decides what it is about.

### 8.1 Departments

| ID | Department | Teams / functions |
|---|---|---|
| DEP-01 | Delivery & Consulting | Strategy & Management Consulting, Implementation & Advisory, PMO |
| DEP-02 | Product & Technology | Product Management, Engineering & Software Development, Data Science & Research |
| DEP-03 | Growth & Client Success | Sales & Business Development, Account Management, Customer Success & Support, Marketing |
| DEP-04 | Finance & Billing | Billing, Invoicing, Subscription Payments, Financial Reconciliation |
| DEP-05 | Legal, Risk & Compliance | Contractual Disputes, Legal Affairs, Data Privacy, Risk & Compliance |
| DEP-06 | Human Resources & Talent Acquisition | Recruitment, Employee Relations, Talent Acquisition (see open item O-04) |

### 8.2 Categories, complaint types, and routing

| Category | Primary dept | Secondary dept | Complaint types |
|---|---|---|---|
| **CAT-01** Product & Technical Issues | DEP-02 | none | Software bugs; System downtime; Performance issues; Feature malfunction; Integration issues; Product feature requests |
| **CAT-02** Service Delivery & Quality | DEP-01 | none | Poor consulting advice; Missed deadlines; Poor deliverable quality; Scope or implementation issues; Lack of expertise; Project management failures |
| **CAT-03** Billing, Invoicing & Access | DEP-04 | DEP-02 | Duplicate charges; Incorrect invoice; Subscription pricing disputes; Payment failures; Paid account access issues; Refund requests |
| **CAT-04** Communication & Professionalism | DEP-03 | DEP-01 | Unresponsive staff; Unprofessional conduct; Poor communication; Poor team handover; Incorrect information; Poor customer support |
| **CAT-05** Account & Contractual Disputes | DEP-05 | DEP-03 | Scope-of-work disputes; Contract interpretation; Subscription cancellation; SLA violations; Renewal disputes; Service commitments |
| **CAT-06** Data Privacy & Security | DEP-05 | DEP-02 | Unauthorized data access; Confidentiality breaches; Data exposure; Suspected account compromise; Data handling concerns; Data deletion requests |

**Type-level override (proposed).** A complaint type may override the primary department. Seed one: *Paid account access issues* has DEP-02 as primary and DEP-04 as secondary, because the fix is usually technical.

**Rules**

- The complaint type must belong to the selected category.
- The taxonomy is data in the database, editable by the admin, never hard-coded.

## 9. Business rules

### 9.1 Ticket lifecycle

Statuses: `Submitted`, `Assigned`, `In Progress`, `Pending Client Response`, `Escalated`, `Resolved`, `Closed`, `Reopened`.

| From | To | Trigger |
|---|---|---|
| (new) | Submitted | Ticket created |
| Submitted | Assigned | Routing selects staff, or the admin assigns an uncategorised ticket |
| Assigned | In Progress | Staff acknowledges or starts work |
| Assigned | Assigned | Acknowledgement timeout and reassignment, or admin reassignment |
| In Progress | Pending Client Response | Staff waits for the client |
| Pending Client Response | In Progress | Client replies |
| In Progress | Escalated | Resolution due time passed, or a manual escalation |
| Escalated | In Progress | Assignee or admin takes action |
| In Progress | Resolved | Staff records resolution notes |
| Resolved | Closed | 3 days with no client reply (O-03), or staff or admin closes |
| Resolved / Closed | Reopened | Client replies on the thread (Closed only within the reopen window, default 14 days; after that a new linked ticket is created) |
| Reopened | Assigned | Routing selects staff |

Every transition goes through one state-machine function that validates it, writes the audit entry, and emits events. No endpoint changes status directly.

### 9.2 Priority and limits

Priority is independent of category.

| Priority | Default rule | Acknowledge | Resolve |
|---|---|---|---|
| Critical | All of CAT-06, System downtime, Suspected account compromise | 10 min | 4 h |
| High | Duplicate charges, Payment failures, Paid account access issues, Software bugs, Integration issues, SLA violations | 10 min | 24 h |
| Medium | Everything else | 10 min | 72 h |
| Low | Product feature requests | 10 min | 5 days |

Urgency words in the email ("urgent", "again", "third time", "still not fixed") raise the priority by one level, up to High. Only Critical rules produce Critical. Limits live in `priority_sla` and are admin-editable.

### 9.3 Routing

1. Look up the ticket's complaint type (override) or category, then the primary department. Add secondary departments as view-only, with a notification.
2. Eligible staff: active, role staff, in that department, `available = true`, and not on leave.
3. Pick the eligible staff with the fewest open tickets. Break ties by oldest last assignment.
4. If none is eligible, use that department's backup staff (`is_backup = true`).
5. If there is still none, assign to the admin queue and alert the admin.
6. Acknowledgement timeout: reassign to the next eligible staff (backup first when nobody else is free), excluding anyone who already timed out on this ticket. After 2 automatic reassignments, set Escalated and alert the admin.
7. Every reassignment records the reason code (`ROUTED`, `ACK_TIMEOUT`, `STAFF_UNAVAILABLE`, `ADMIN`) in the audit log. The admin can mark a timeout as excused with a reason, because the firm wants unexcused absences tracked.

### 9.4 Reply matching, duplicates, similar tickets

Order of checks for every incoming email:

1. **Thread headers.** `In-Reply-To` or `References` matches a stored Message-ID, which gives the ticket.
2. **Reference in subject.** `[TKT-000124]`.
3. **Same sender, recent open ticket, high similarity** (embedding cosine at or above 0.80 against that sender's open tickets from the last 30 days) means treat it as a reply.
4. Otherwise it is a new ticket.

For an email matched to a ticket:

- Near-identical to a message already on the ticket (cosine at or above 0.92, no new attachment) means **discard** it as a duplicate and log it.
- Otherwise append it as a new message in the chain and notify the assignee.

For a new ticket, compare against open tickets from other clients. A cosine at or above 0.80 in the same category creates a `related` link. These thresholds are configuration and must be tuned on the test set.

### 9.5 Retention and purge

- At Closed, a scheduled job deletes message bodies (replaced by a placeholder), deletes attachment files, and clears OCR text and embeddings.
- It keeps: ticket ref, category, type, priority, department, assignee history, timestamps, status history, the summary, and the audit log.
- **Open point:** the summary may itself contain sensitive details (amounts, account numbers). The analyser must not copy account or card numbers into the summary, and the purge job also clears the summary if the category is CAT-03 or CAT-06 (configurable). Review with legal.

## 10. Architecture

```
                       +-------------------+
 Client email  ------> |  Mailbox (IMAP)   |
                       +---------+---------+
                                 |  poll every 30 s
                       +---------v---------+          +------------------+
                       |  Ingestion worker |--------->|  Redis queue     |
                       +-------------------+          +---------+--------+
                                                                |
                       +----------------------------------------v--------------+
                       |  Pipeline worker                                      |
                       |  filter > attachments > thread match > create ticket |
                       |  > OCR > analyse > dup/similar > route > notify       |
                       +----+---------------------+----------------------+-----+
                            |                     |                      |
                  +---------v------+    +---------v---------+   +--------v---------+
                  |  PostgreSQL    |    | Notification svc  |   |  Analyser        |
                  |  (tickets,     |    | in-app / email /  |   |  embeddings,     |
                  |   audit, cfg)  |    | SMS / WhatsApp    |   |  classifier, OCR |
                  +---------^------+    +---------+---------+   +------------------+
                            |                     |
                  +---------+------+    WebSocket |      +------------------+
                  |  FastAPI REST  |<-------------+----->|  Svelte frontend |
                  +----------------+                     +------------------+
                  +----------------+
                  |  Scheduler     |  ack timer, resolve timer, auto-close, purge, poll
                  +----------------+
```

| Component | Responsibility |
|---|---|
| **Ingestion worker** | Poll IMAP, parse MIME, store the raw email with UID and Message-ID, enqueue a job. |
| **Pipeline worker** | Run the ordered steps in section 14.1, each step logged. Retries with backoff, dead-letter queue for repeated failure. |
| **Analyser** | Interface with a baseline implementation (section 14). |
| **Notification service** | Event to channel fan-out through adapters. Retries, delivery log, WebSocket hub. |
| **Scheduler** | Cron-like jobs: IMAP poll, acknowledgement checks, resolve-by checks, auto-close, purge, health heartbeat. |
| **API** | REST for the frontend, JWT auth, role enforcement. |
| **Frontend** | Svelte single-page app (SvelteKit), role-aware. |

## 11. Technology stack

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic | Async end to end |
| Database | PostgreSQL | Embeddings stored as `real[]` and compared in Python against recent open tickets (volume is under 11k tickets a year, so no vector extension is needed) |
| Queue and scheduler | Redis with ARQ | Simpler than Celery for a 3-week build |
| Email in / out | `imap-tools` (IMAP), `aiosmtplib` (SMTP) | |
| OCR | Tesseract (`pytesseract`) | CPU only |
| Embeddings | A small sentence-embedding model (for example MiniLM) via `sentence-transformers` | CPU, about 100 MB |
| Classifier | scikit-learn logistic regression over embeddings | Probability is the confidence score |
| Realtime | FastAPI WebSocket plus Redis pub/sub | Works across multiple processes |
| Frontend | SvelteKit, TypeScript, Tailwind (optional) | |
| Auth | JWT access token (short-lived) and refresh token, argon2 or bcrypt | |
| Container | Docker Compose | |
| Reverse proxy | Caddy (automatic HTTPS) | |
| CI | GitHub Actions: ruff, pytest, svelte-check, image build | |
| Stretch | Small local LLM via Ollama for summaries; Whisper for voice | Only if the VM has 16 GB RAM |

## 12. Data model

Notation: `pk` primary key, `fk` foreign key, `?` nullable. All tables have `created_at`. Use UUID primary keys, except the human reference `ref` on tickets.

```
departments(id, code unique, name, active)
categories(id, code unique, name, active)
category_departments(category_id fk, department_id fk, is_primary bool)
complaint_types(id, category_id fk, name, active,
                primary_department_override_id fk?, default_priority)
priority_sla(priority pk, ack_minutes, resolve_minutes)

users(id, name, email unique, phone?, whatsapp_number?, role enum[admin,staff],
      department_id fk?, available bool, on_leave_until?, is_backup bool,
      is_incident_contact bool, channels text[], password_hash, active)

clients(id, email unique, name?, phone?)
blocked_senders(id, pattern, reason)

tickets(id, ref unique, client_id fk, category_id fk?, complaint_type_id fk?,
        department_id fk?, assignee_id fk?, status enum, priority enum,
        needs_triage bool, summary text?, confidence float?,
        ack_at?, ack_deadline_at?, resolve_due_at?, resolved_at?, closed_at?,
        resolution_notes?, reassign_count int, purged_at?)

messages(id, ticket_id fk, direction enum[in,out,note], sender_email?,
         author_user_id fk?, message_id_header?, in_reply_to?, subject,
         body text?, ocr_text?, embedding real[]?, sent_at)
attachments(id, message_id fk, filename, mime, size_bytes, storage_path?,
            status enum[ok,rejected,corrupt], reject_reason?)

ingest_log(id, mailbox, imap_uid, uidvalidity, message_id_header?, from_email,
           decision enum[ticketed,appended,discarded_duplicate,filtered_spam,
                         filtered_empty,filtered_blocked,error],
           reason?, ticket_id fk?, raw_path?)
           unique(mailbox, uidvalidity, imap_uid)

ticket_links(id, ticket_id fk, linked_ticket_id fk, link_type enum[related,duplicate,followup])
ticket_access(ticket_id fk, user_id fk, permission enum[view,edit], granted_by fk)
access_requests(id, ticket_id fk, requester_id fk, status enum[pending,approved,denied], decided_by fk?, decided_at?)

notifications(id, ticket_id fk, user_id fk, event, channel enum[in_app,email,sms,whatsapp],
              status enum[pending,sent,failed,acknowledged], attempts int, last_error?, sent_at?)
audit_log(id, ticket_id fk?, actor_user_id fk?, actor_type enum[user,system],
          action, reason_code?, detail jsonb, at)   -- append only
```

Rules enforced in code and by constraints:

- A ticket has one category and one assignee.
- `complaint_types.category_id` must match `tickets.category_id`.
- `audit_log` is append only (no update or delete endpoints, and the app database role has no UPDATE or DELETE on it).
- `ingest_log` unique index on `(mailbox, uidvalidity, imap_uid)` guarantees each email is processed once.

## 13. API specification

Base path `/api/v1`. JSON. Errors use `{ "detail": "...", "code": "..." }`. List endpoints support `page`, `page_size`, `sort`. Role enforcement happens in a shared dependency, never in the frontend.

### 13.1 Auth

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/auth/login` | public | Email and password, returns tokens |
| POST | `/auth/refresh` | any | New access token |
| GET | `/me` | any | Current user, role, enabled channels |
| PATCH | `/me` | any | Update contact numbers, channels, availability |

### 13.2 Tickets

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/tickets` | staff (own and shared), admin (all) | Filters: `status`, `category`, `department`, `priority`, `assignee`, `age_bucket`, `needs_triage`, `q` |
| GET | `/tickets/{ref}` | staff with access, admin | Detail: summary, messages, attachments, links, audit |
| PATCH | `/tickets/{ref}/status` | assignee, edit-access staff, admin | Body: `status`, `resolution_notes?`. Validated by the state machine |
| POST | `/tickets/{ref}/acknowledge` | assignee | Sets acknowledged and moves to In Progress |
| POST | `/tickets/{ref}/messages` | assignee, edit-access staff | Reply to the client (emails it) or add an internal note |
| POST | `/tickets/{ref}/reassign` | admin | Body: `user_id`, `reason` |
| PATCH | `/tickets/{ref}/classification` | admin | Set category, type, department for `needs_triage` tickets |
| GET | `/tickets/{ref}/links` | staff with access, admin | Related and duplicate tickets |
| POST | `/tickets/{ref}/access-requests` | staff | Request access |
| GET | `/access-requests` | staff (to approve), admin | Pending requests |
| POST | `/access-requests/{id}/decide` | ticket owner, admin | `approve` or `deny` |
| GET | `/attachments/{id}` | staff with access, admin | Download (not available after purge) |

### 13.3 Dashboards

| Method | Path | Role | Returns |
|---|---|---|---|
| GET | `/dashboard/staff` | staff | Counts by status and priority, due soon, overdue, shared with me, pending access requests |
| GET | `/dashboard/admin` | admin | Counts by status, category, department, age bucket. Unacknowledged. Uncategorised. Overdue. Workload per staff. Ingestion health (last poll time, queue depth, failed notifications) |

### 13.4 Administration

| Method | Path | Role | Purpose |
|---|---|---|---|
| CRUD | `/admin/departments` | admin | Departments |
| CRUD | `/admin/categories` | admin | Categories and their department mapping |
| CRUD | `/admin/complaint-types` | admin | Complaint types and overrides |
| CRUD | `/admin/users` | admin | Users, roles, department, backup flag, incident contact |
| GET, PUT | `/admin/priority-sla` | admin | Acknowledge and resolve limits |
| CRUD | `/admin/blocked-senders` | admin | Blocklist |
| GET, PUT | `/admin/settings` | admin | Thresholds (confidence, duplicate, similarity), poll interval, auto-close days |
| GET | `/admin/audit` | admin | Searchable audit log, including unexcused timeouts |
| POST | `/admin/audit/{id}/excuse` | admin | Mark a timeout as excused with a reason |

### 13.5 Notifications and system

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/notifications` | any | Own in-app notifications |
| POST | `/notifications/{id}/read` | any | Mark read |
| WS | `/ws?token=` | any | Live events: `ticket.assigned`, `ticket.updated`, `ticket.escalated`, `ticket.reopened`, `access.requested`, `ack.timeout`, `system.alert` |
| GET | `/health` | public | Database, Redis, last IMAP poll time, queue depth |

## 14. Analysis (AI) design

The AI runs on the firm's own cloud VM with no third-party AI service (D-21). Because there is no GPU, the release 1 analyser is lightweight and deterministic. A small LLM is an optional upgrade.

### 14.1 Pipeline order (one job per email)

| Step | Action | Failure handling |
|---|---|---|
| P1 | Fetch and store the raw email, record in `ingest_log` | Duplicate UID means skip |
| P2 | Sender filter: automated headers (`Auto-Submitted`, `Precedence: bulk`, `List-Unsubscribe`), `mailer-daemon`, `no-reply`, blocklist | Log `filtered_*` |
| P3 | Empty body and no attachments means discard | Log `filtered_empty` |
| P4 | Attachment validation (size, signature, type, corruption) | Reject the file, keep the email |
| P5 | Thread and duplicate check (section 9.4) | Append or discard if matched |
| P6 | Create the ticket (Submitted), queue the client acknowledgement email | Retry the job |
| P7 | OCR images. If body is empty and OCR finds no meaningful words, mark `needs_triage` with note "no issue detected" | OCR error means continue with text only |
| P8 | Analyse (section 14.2) | Analyser error means `needs_triage` |
| P9 | Similar-ticket links | Skip on error |
| P10 | Route and assign (section 9.3) | No staff means admin queue |
| P11 | Notify | Retry, then flag unacknowledged on the dashboard |
| P12 | Audit entries | |

### 14.2 Baseline analyser

1. Build the text: subject plus body plus OCR text (cleaned of signatures and quoted replies).
2. Embed the text.
3. Predict the complaint type with a classifier trained on labelled examples. The category follows from the type. The probability is the confidence.
4. If confidence is below `CONFIDENCE_THRESHOLD` (default 0.60, tune on the test set), set `needs_triage` and leave category empty.
5. Priority: apply section 9.2 rules, including urgency words.
6. Summary: extractive and templated. For example: `"{type}: {subject}. Key points: {first two informative sentences}. Details: {amounts, dates, invoice or order numbers found by regex}."` Never include card or account numbers (mask them).
7. Suggested solution: not produced by the baseline (known limitation, see 14.5).

### 14.3 Output contract

Every analyser returns this shape (Python dataclass or dict):

```json
{
  "category_code": "CAT-03",
  "complaint_type": "Duplicate charges",
  "priority": "high",
  "confidence": 0.82,
  "summary": "Duplicate charges: client says they were charged twice for March. Details: invoice INV-2201, amount 45,000.",
  "suggested_solution": null
}
```

### 14.4 Swappable interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Analysis:
    category_code: str | None
    complaint_type: str | None
    priority: str
    confidence: float
    summary: str
    suggested_solution: str | None = None

class Analyzer(ABC):
    @abstractmethod
    async def analyze(self, text: str, ocr_text: str = "") -> Analysis: ...

class BaselineAnalyzer(Analyzer): ...   # embeddings + classifier + rules (release 1)
class LlmAnalyzer(Analyzer): ...        # small local LLM for summary and solution (stretch)

def get_analyzer() -> Analyzer:
    return {"baseline": BaselineAnalyzer, "llm": LlmAnalyzer}[settings.AI_BACKEND]()
```

### 14.5 Known limitations (tell the firm before UAT)

- No "likely solution" suggestions in release 1, and the summaries are extractive.
- Screenshots are read as text only (OCR). The system does not understand charts or UI layouts.
- Accuracy depends on the labelled examples. Wrong or uncertain classifications go to the Uncategorised queue for the admin, by design.

### 14.6 Evaluation (build this on Day 1 of the AI work)

- Labelled test set of 40+ emails covering all six categories (see O-11), including edge cases: screenshot-only, empty, duplicate, reply, multi-topic, spam.
- Script `scripts/eval_analyzer.py` reports category accuracy, type accuracy, confusion matrix, share routed to `needs_triage`, and time per email.
- Gate at end of Sprint 2: category accuracy at or above the target (O-12). If it is below, add examples and re-measure before moving on.

### 14.7 Future: AI auto-reply (not in release 1)

The hook is an `auto_reply_policy` table (category, complaint type, enabled) and a `send_ai_reply()` step after P8. Never enabled for payment, billing, contract, data-privacy or security types. Candidate light issues from the firm: login problems, site navigation, accessing resources, basic issues an average phone user can solve. Requires high confidence, human escalation, and an off switch.

## 15. Notifications

### 15.1 Events and recipients

| Event | Recipients | Channels |
|---|---|---|
| `ticket.assigned` | New assignee | All the user has enabled |
| `ticket.reassigned` | Previous and new assignee, admin (if timeout) | All enabled |
| `ack.timeout` | Previous assignee, admin | In-app, email |
| `ticket.escalated` | Assignee, admin | All enabled |
| `ticket.needs_triage` | Admin | In-app, email |
| `ticket.security` | Incident contact, admin | All channels, immediately |
| `ticket.reply_received` | Assignee | All enabled |
| `access.requested` | Ticket owner | In-app, email |
| `access.decided` | Requester | In-app |
| `system.alert` (IMAP down, queue backlog) | Admin | In-app, email |

### 15.2 Adapter pattern

Every channel implements one interface, so adding or swapping a provider is one class. API keys come from environment variables, so they can be added at the end.

```python
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    name: str
    @abstractmethod
    async def send(self, recipient: str, message: str, ticket_ref: str) -> bool: ...

class InAppChannel(NotificationChannel): ...      # WebSocket push and DB row
class EmailChannel(NotificationChannel): ...      # SMTP
class SmsChannel(NotificationChannel): ...        # provider HTTP API, key from env
class WhatsAppChannel(NotificationChannel): ...   # WhatsApp Business API, template messages

CHANNELS = {c.name: c for c in [InAppChannel(), EmailChannel(), SmsChannel(), WhatsAppChannel()]}

async def notify(user, ticket, event):
    for ch in user.channels:
        ok = await with_retry(CHANNELS[ch].send, user.contact_for(ch), render(event, ticket), ticket.ref)
        record_delivery(ticket, user, ch, event, ok)
```

### 15.3 Delivery rules

- In-app: push over WebSocket immediately, with a stored row so missed events appear on next login.
- External channels: retry with backoff (for example 10 s, 30 s, 90 s). After the final failure, mark the notification failed and flag the ticket "unacknowledged" on the admin dashboard.
- A notification is "acknowledged" when the assignee clicks acknowledge in the app, which also moves the ticket to In Progress.
- WhatsApp: business-initiated messages must use pre-approved templates, and staff must opt in. Build and test against the provider's sandbox. Example template: `New ticket {{1}} ({{2}} priority) assigned to you: {{3}}. Open the app to acknowledge.`
- SMS: keep messages short, with no sensitive content, only the ticket ref and priority.

### 15.4 Client emails

- Auto-acknowledgement subject: `[TKT-000124] We received your complaint`. Body: thanks the client, gives the reference, says replies to this email are added to the same ticket. Contains no complaint details.
- Staff replies are sent through SMTP with the same `[ref]` in the subject and stored as outgoing messages.

## 16. Security and compliance

| Area | Requirement |
|---|---|
| Authentication | Argon2 or bcrypt password hashes, short-lived JWT, rate-limited login, forced password change for seeded users |
| Authorisation | Role and ticket-access check in one shared dependency used by every ticket, message, and attachment endpoint. Tests prove a staff member cannot read another staff member's ticket by ID |
| Transport | HTTPS only (Caddy). WebSocket over WSS |
| Secrets | Environment variables only. Nothing in git. `.env.example` lists the names |
| Attachments | Validate by file signature, enforce 10 MB, store outside the web root with random names, never execute |
| Input | Pydantic validation on all inputs. Sanitise email HTML before display (render as plain text by default) |
| Data minimisation | Mask card and account numbers in summaries. Purge job at Closed (section 9.5) |
| Audit | Append-only log for assignment, status, access, configuration, purge |
| Backups | Daily database dump, encrypted, retained at most 30 days (O-10) |
| Compliance | Record the lawful basis and retention in a short privacy note for the firm. Confirm the purge design with legal (NDPA) |

---

# PART C. BUILD PLAN

## 17. Team roles and working agreements

| Dev | Focus | Owns |
|---|---|---|
| **D1: Core backend** | Schema, auth, ticket API, state machine, routing, timers, admin API, sharing, audit, purge | Everything that decides "who gets what, when" |
| **D2: Pipeline and AI** | IMAP, filters, queue, analyser, OCR, linking, SMS/WhatsApp adapters, hardening, load tests | Everything between the mailbox and the ticket |
| **D3: Frontend and DevOps** | Svelte app, dashboards, WebSocket client, Docker, CI, staging and production deployment | Everything users see, and how it ships |

Adjust the split to your strengths, but keep exactly one owner per task.

**Working agreements**

- Git: short-lived feature branches off `main`, pull request required, at least one review, squash merge. Commit messages like `feat(routing): pick least-loaded staff`.
- Definition of Done for a task: code reviewed and merged, business logic covered by tests, works on staging, and the related docs or OpenAPI updated.
- Daily 15-minute standup. Rebalance work openly: Sprint 2 is the heaviest for D1 and D2, so D3 picks up backend help (for example email adapter, admin CRUD endpoints) whenever the UI is ahead.
- Contract first: D1 publishes the OpenAPI schema with stub endpoints returning fixtures by Day 2, so D3 never waits.
- End of each sprint: a 30-minute demo using a real email, and a short retro.
- Feature freeze at the start of Day 13. After that, only bug fixes.

## 18. Repository layout and environment setup

```
ticketing/
  backend/
    app/
      api/            # routers: auth, tickets, admin, dashboard, notifications, ws
      core/           # config, security, deps (RBAC), logging
      db/             # session, base, migrations helpers
      models/         # SQLAlchemy models
      schemas/        # Pydantic schemas
      services/       # tickets (state machine), routing, linking, audit, sla, purge
      pipeline/       # ingestion, filters, attachments, steps P1-P12
      ai/             # analyzer interface, baseline, ocr, embeddings
      notifications/  # channels (in_app, email, sms, whatsapp), hub, retry
      workers/        # ARQ worker and scheduler jobs
    alembic/
    tests/
    scripts/          # seed_taxonomy.py, eval_analyzer.py, send_test_emails.py, load_test.py
  frontend/
    src/routes/       # login, dashboard, tickets, tickets/[ref], admin/*
    src/lib/          # api client, stores, ws client, components
  deploy/
    docker-compose.yml
    docker-compose.prod.yml
    Caddyfile
    .env.example
  docs/               # this document, runbook, privacy note
```

Services in Docker Compose: `api`, `worker` (includes scheduler jobs), `postgres`, `redis`, `frontend`, `caddy` (staging and production). Optional `ollama` for the stretch task.

Environment variables are listed in Appendix B. Create a **test mailbox** (separate from the firm's real one) on day one, so ingestion is built and tested without touching real client mail.

## 19. Phase 0: Kickoff (before Day 1, about half a day, all three)

| ID | Task | Done when |
|---|---|---|
| P0-01 | Walk through this document. Assign owners. Agree on the git workflow. | Roles and conventions agreed |
| P0-02 | Send the open items (section 5) to the firm. | The firm has the list. Defaults are used until answered |
| P0-03 | Obtain: test mailbox with IMAP and SMTP credentials, firm's real IMAP details (later), domain or subdomain for the app, cloud VM, SMS and WhatsApp sandbox accounts. | Credentials in a shared secret store, not in chat or git |
| P0-04 | Collect or write 40+ sample complaint emails and label them with category and type. | `data/labelled_emails.json` exists |
| P0-05 | Create the repository, board, and CI skeleton. | Repo exists, CI runs |

## 20. Sprint 1 (Days 1-5): Foundation and ingestion

**Goal:** an email sent to the test mailbox appears as a ticket in the app on a deployed staging environment.

| ID | Task | Owner | Depends on | Done when | Reqs |
|---|---|---|---|---|---|
| S1-01 | Repo, Docker Compose (api, worker, postgres, redis, frontend), `.env.example`, CI (lint, tests, build) | D3 | P0-05 | `docker compose up` runs everything locally. CI passes on an empty test | NFR-11 |
| S1-02 | Schema and the first Alembic migration for all tables in section 12 | D1 | S1-01 | Migration applies cleanly. Constraints in place | all |
| S1-03 | Seed script for departments, categories, complaint types, mapping, priority limits, default admin | D1 | S1-02 | Running it twice causes no duplicates. Section 8 data is present | FR-19 |
| S1-04 | Auth: login, refresh, password hashing, RBAC dependency (admin, staff, ticket access check) | D1 | S1-02 | Tests: staff cannot read another staff member's ticket. Admin can | NFR-07 |
| S1-05 | Publish the OpenAPI contract with stub endpoints (tickets, dashboard, auth) returning fixtures | D1 | S1-04 | D3 can build screens against it by Day 2 | |
| S1-06 | IMAP poller: connect, fetch unseen by UID, parse MIME (charset, HTML to text, attachments, headers), store raw message, idempotency via `ingest_log` unique index | D2 | S1-02 | Restarting the poller never creates duplicates. Test with 20 emails | FR-01 |
| S1-07 | Filters and validation: automated headers, blocklist, empty email, attachment size, type by signature, corrupted files. Queue with retry and dead-letter | D2 | S1-06 | Each rule has a test. Every discard appears in `ingest_log` with a reason | FR-02, FR-03 |
| S1-08 | Labelled test set loaded. First baseline analyser prototype (embeddings plus classifier) and `eval_analyzer.py` | D2 | P0-04 | Script prints accuracy and time per email on the test set | FR-06 |
| S1-09 | Svelte shell: login, role-aware layout, API client with token refresh, ticket list and detail pages against the contract | D3 | S1-05 | Staff and admin can log in and see lists. Admin sees all, staff sees only own | FR-15 |
| S1-10 | Pipeline steps P1-P6: email to ticket (status Submitted, `needs_triage` until analysed), ticket ref generator, client record creation | D1, D2 | S1-04, S1-07 | Real email in the test mailbox becomes a ticket with attachments | FR-04 |
| S1-11 | Provision the cloud VM, Caddy with HTTPS, deploy staging from CI | D3 | S1-01 | Staging URL works over HTTPS. A push to `main` deploys | NFR-07 |

**Sprint 1 exit check**

- Send 5 different emails to the test mailbox. They appear in the staging UI within about a minute.
- Restart the worker mid-batch. No duplicates, no losses.
- Login works for both roles, and a staff member cannot open someone else's ticket.
- Demo to the team. Retro. Fix issues before Day 6.

## 21. Sprint 2 (Days 6-10): Intelligence, routing, notifications

**Goal:** a real email is classified, summarised, routed, and the right staff member is notified live. Unacknowledged tickets move on automatically.

| ID | Task | Owner | Depends on | Done when | Reqs |
|---|---|---|---|---|---|
| S2-01 | Analyzer interface and `BaselineAnalyzer` integrated into P8: category, type, priority rules, confidence, masked extractive summary, `needs_triage` fallback | D2 | S1-08, S1-10 | Section 14.3 output produced for every ticket. Uncertain ones go to the Uncategorised queue | FR-06, FR-07 |
| S2-02 | OCR for images (Tesseract), combined with body. Empty-content rule for screenshot-only emails | D2 | S1-10 | A screenshot-only email with readable text is classified. One without is flagged | FR-05, D-09 |
| S2-03 | Thread matching (headers, ref in subject, same-sender similarity), duplicate discard, similar-ticket links. Embeddings stored | D2 | S2-01 | Reply attaches to the old ticket. An identical resend is discarded and logged. Related ticket from another client is linked | FR-12, FR-13, FR-14 |
| S2-04 | Routing engine (section 9.3): department lookup, type override, secondary departments as view-only, least-loaded eligible staff, backup, admin fallback | D1 | S1-03, S2-01 | Table-driven tests for every branch | FR-08 |
| S2-05 | Ticket state machine service: validated transitions, audit entries, event emission. All status changes go through it | D1 | S1-02 | Illegal transitions are rejected in tests | FR-23 |
| S2-06 | Notification core: events, adapter interface, in-app channel with WebSocket hub (Redis pub/sub), email channel (SMTP), retry with backoff, delivery log, outbound client email (auto-ack and staff replies) | D1 | S2-05 | Assignment pushes in-app in under 2 seconds. Email arrives. Client gets the acknowledgement with ref | FR-09, FR-20, FR-21 |
| S2-07 | SMS and WhatsApp adapters with sandbox configuration and templates. Provider keys read from env | D2 | S2-06 | Sandbox messages delivered. Failure retries then flags the ticket | FR-09 |
| S2-08 | Scheduler jobs: acknowledgement check (10 min), resolve-by check, reassignment on timeout (max 2), escalate afterwards, audit with reason codes | D1 | S2-04, S2-05 | With the timeout set to 1 minute in test, an ignored ticket moves to backup and is logged | FR-10, FR-11 |
| S2-09 | Staff dashboard and ticket detail: summary, thread chain, attachments, linked tickets, acknowledge button, status actions, reply to client | D3 | S1-09, S2-05 | A staff member can work a ticket from open to resolved in the UI | FR-15, FR-21 |
| S2-10 | Live notifications in the UI: WebSocket client with reconnect, bell and toast, unread list | D3 | S2-06 | Assigning a ticket pops a notification without refresh | FR-09 |
| S2-11 | **Gate: AI evaluation.** Run `eval_analyzer.py` on the full pipeline output. Tune thresholds | D2, all | S2-01 | Category accuracy meets O-12, or the team adds examples and re-runs. Record the result in `docs/` | O-12 |

**Sprint 2 exit check (demo scenario)**

1. Send a billing complaint with a screenshot. Result: ticket created, category CAT-03, High priority, summary shown, routed to Finance & Billing staff, notification arrives in-app and by email.
2. Ignore it. After the timeout it moves to the backup staff and the audit log shows `ACK_TIMEOUT`.
3. Reply to the ticket email. It joins the same ticket.
4. Send an unrelated vague email. It lands in the Uncategorised queue and the admin is alerted.

If Sprint 2 slips, apply the cut-line in section 27 before starting Sprint 3.

## 22. Sprint 3 (Days 11-15): Admin, rules, hardening, release

**Goal:** the full workflow is complete, tested, deployed to production, and accepted by the firm.

| ID | Task | Owner | Depends on | Done when | Reqs |
|---|---|---|---|---|---|
| S3-01 | Admin API: reassign with reason, classification of `needs_triage`, CRUD for departments, categories, types, users, backup flag, priority limits, blocklist, settings, audit search and excuse | D1 | S2-05 | Every endpoint is admin-only and tested | FR-17, FR-19 |
| S3-02 | Admin dashboard and queues: counts by status, category, department, age; unacknowledged; uncategorised; overdue; staff workload; ingestion health | D3 | S3-01 | Matches database counts in a test fixture | FR-16 |
| S3-03 | Admin configuration UI (taxonomy, users, limits, blocklist, settings) and the reassign and triage screens | D3 | S3-01 | Admin adds a new category and type without any code change, and the next email can be routed with it | FR-19, NFR-10 |
| S3-04 | Access sharing: request, owner approval, edit rights, notifications, UI | D1, D3 | S2-05 | Staff B requests, Staff A approves, Staff B can edit. Others cannot see the ticket | FR-18 |
| S3-05 | Resolve flow and auto-close (3 days). Purge job: delete bodies, attachment files, OCR text, embeddings. Keep metadata and audit | D1 | S2-05 | After Closed, no message bodies or files remain. Audit and metadata do. Reopen within the window works | FR-22, D-18 |
| S3-06 | Security fast path: CAT-06 means Critical, assign immediately, notify incident contact and admin on all channels, skip queue waits | D1 | S2-06 | Test email about unauthorised access triggers notifications within the targets | FR-24 |
| S3-07 | Hardening: attachment signature checks verified, rate limits (login, API), input size limits, sanitised HTML display, security checklist (section 16) completed, dependency audit | D2 | S2-xx | Checklist signed off with evidence | NFR-07 |
| S3-08 | Resilience and load tests: inject 500 emails in an hour. Stop the IMAP connection, stop Redis, break an SMS key, and recover each time | D2 | S2-07 | Zero lost or duplicated tickets. Admin dashboard shows the degraded state and recovery. Results written to `docs/test-report.md` | FR-25, NFR-05, NFR-06 |
| S3-09 | Production deployment: production compose, HTTPS, firm's real mailbox settings, backups (daily, encrypted, 30-day retention), log rotation, uptime check on `/health`, runbook | D3 | S1-11 | Production URL live. A backup restore was tested once | NFR-08, NFR-11 |
| S3-10 | Stretch: `LlmAnalyzer` for summary and suggested solution on the VM, with timing benchmark. Voice transcription | D2 | S2-11 | Only starts if all other S3 tasks are on track. Otherwise it moves to the backlog | FR-26 |
| S3-11 | Acceptance run against all criteria in section 23.2, with the firm | All | all | Every criterion passes or has a written, agreed exception | all |

**Sprint 3 timeline**

| Day | Focus |
|---|---|
| 11-12 | S3-01 to S3-06 (build) |
| 13 | **Feature freeze.** S3-07, S3-08, S3-09. Bug fixes only |
| 14 | UAT with the firm on staging with real-format data (S3-11) |
| 15 | Fix UAT findings. Production go-live. Handover (section 26). Buffer |

---

# PART D. RELEASE

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
| Classifier accuracy too low on real emails | Medium | High | Early evaluation, gate at S2-11, low-confidence emails go to the admin queue, add labelled examples quickly |
| Sprint 2 overloaded (D1 and D2) | High | High | Daily rebalance, contract-first API, cut-line below |
| WhatsApp approval or provider delays | Medium | Medium | Adapter plus sandbox. Ship with live keys if ready, otherwise in-app, email and SMS go live first |
| Real mailbox details arrive late | Medium | Medium | Build and test on a test mailbox from Day 1 |
| Purge conflicts with reporting or legal needs | Medium | Medium | Purge content only, keep metadata and audit, confirm with legal (O-03, O-10) |
| Burst of emails overwhelms analysis | Low | Medium | Queue, backpressure, load test at 500 an hour |
| Staff receive too many notifications | Medium | Low | Per-user channel settings, short messages |

**Cut-line.** The core path is: email to ticket, classify, route, notify, dashboard. If time runs short, drop in this order and tell the firm:

1. Voice transcription (S3-10)
2. LLM summaries and suggested solutions (S3-10)
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

# APPENDICES

## Appendix A. Use case inventory

| ID | Use case | Primary actor | Release |
|---|---|---|---|
| UC-01 | Receive and filter incoming email | System | 1 |
| UC-02 | Create ticket from email | System | 1 |
| UC-03 | Analyse, categorise, summarise | System / AI | 1 |
| UC-04 | Auto-assign ticket to department and staff | System | 1 |
| UC-05 | Notify assigned staff | System | 1 |
| UC-06 | Work and update ticket status | Staff | 1 |
| UC-07 | Resolve ticket and purge sensitive data | Staff, System | 1 |
| UC-08 | Handle client reply on an existing thread | System | 1 |
| UC-09 | Link duplicate and similar tickets | System | 1 |
| UC-10 | View admin dashboard | Admin | 1 |
| UC-11 | View staff dashboard | Staff | 1 |
| UC-12 | Reassign ticket | Admin | 1 |
| UC-13 | Manage categories, departments, mapping | Admin | 1 |
| UC-14 | Manage users, roles, backup staff | Admin | 1 |
| UC-15 | Share ticket access (request and approve) | Staff | 1 |
| UC-16 | Escalate unacknowledged or overdue ticket | System | 1 |
| UC-17 | Triage an uncategorised ticket | Admin | 1 |
| UC-18 | AI auto-reply to light issues | AI | Later |
| UC-19 | Process voice recording attachment | AI | Stretch |

## Appendix B. Configuration reference

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | |
| `REDIS_URL` | Redis connection | |
| `JWT_SECRET` | Token signing | |
| `APP_BASE_URL` | Links in emails and notifications | |
| `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASSWORD`, `IMAP_FOLDER` | Mailbox access | folder `INBOX` |
| `IMAP_POLL_SECONDS` | Poll interval | 30 |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Outbound email | |
| `SMS_PROVIDER`, `SMS_API_KEY`, `SMS_SENDER_ID` | SMS gateway | |
| `WHATSAPP_API_KEY`, `WHATSAPP_PHONE_ID` | WhatsApp Business API | |
| `AI_BACKEND` | `baseline` or `llm` | `baseline` |
| `CONFIDENCE_THRESHOLD` | Below this goes to triage | 0.60 |
| `DUPLICATE_SIMILARITY` | Discard threshold | 0.92 |
| `SIMILAR_LINK_SIMILARITY` | Link threshold | 0.80 |
| `ACK_TIMEOUT_MINUTES` | Acknowledgement limit | 10 |
| `MAX_AUTO_REASSIGN` | Reassignments before Escalated | 2 |
| `MAX_ATTACHMENT_MB` | Attachment size limit | 10 |
| `AUTO_CLOSE_DAYS` | Resolved to Closed | 3 |
| `REOPEN_WINDOW_DAYS` | Reopen after Closed | 14 |
| `BACKUP_RETENTION_DAYS` | Backup retention | 30 |

(Thresholds and limits are also editable through the admin settings screen where noted in section 13.4.)

## Appendix C. Glossary

| Term | Meaning |
|---|---|
| Ticket ref | Human-readable ID such as `TKT-000124` |
| Needs triage | Ticket the analyser could not classify with enough confidence |
| Acknowledge | Assignee confirms they have started, which moves the ticket to In Progress |
| Backup staff | Users flagged as covering when no other staff in the department is available |
| Purge | Deleting message content and attachment files after closure, while keeping metadata and the audit log |
| Confidence | Classifier probability for the chosen complaint type |
| Primary / secondary department | Primary owns the ticket. Secondary is informed with view access |
