# M04 · Data model

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** D1 (owner), everyone reads

---

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

---

## 12.A Addendum: gaps found while splitting the spec (apply in task D1-02)

The master spec refers to these things but the schema in section 12 does not define them. Add them in the first migration.

| Addition | Why |
|---|---|
| `settings(key pk, value jsonb, updated_by fk?, updated_at)` | `/admin/settings` needs a table. Env vars (Appendix B) are defaults, DB values override. |
| `ticket_assignments(id, ticket_id fk, user_id fk, assigned_at, ended_at?, reason_code)` | Section 9.5 keeps "assignee history" after purge, and routing must exclude anyone who already timed out on this ticket. |
| `tickets.assigned_at` | Needed to compute `ack_deadline_at` and workload ordering ("oldest last assignment"). |
| `notifications.read_at?` | `POST /notifications/{id}/read` needs it. |
| `users.must_change_password bool` | Section 16: forced password change for seeded users. |
| `complaint_types.keywords text[]` | The baseline classifier can only predict types it has examples for. Keywords let a newly admin-created type be matched without retraining (AC-17). |
| Excusing a timeout | `audit_log` is append only, so an excuse is a NEW audit row (`ACK_TIMEOUT_EXCUSED`, `detail.audit_id` = the original row). "Unexcused timeouts" = timeout rows with no excuse row. |
| Setting key `purge_summary_categories` | List of category codes whose summary is also cleared on purge (default CAT-03, CAT-06). |
