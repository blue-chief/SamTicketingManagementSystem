# M00 · Context, scope, decisions, open items

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** Everyone (read first)

---

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
