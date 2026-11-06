# M08 · Security, compliance, configuration reference

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** D1 (owner), D2 (hardening)

---

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
