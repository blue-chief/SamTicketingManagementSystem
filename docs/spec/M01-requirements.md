# M01 · Functional and non-functional requirements, use cases

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** Everyone

---

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
