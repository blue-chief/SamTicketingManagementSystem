# M05 · REST/WebSocket API specification

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** All, by endpoint ownership (see README)

---

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
