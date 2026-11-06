# M02 · Taxonomy and business rules (lifecycle, priority, routing, matching, purge)

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** D3 (lifecycle, routing), D1 (purge), D2 (matching)

---

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
