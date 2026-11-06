# M10 · Shared contracts between developers

> New document (not in the master spec). The three devs work in parallel through agents. These are the **function signatures and conventions** each module exposes to the others. Agents must code against these exactly. If a signature must change, all three devs agree first, then update this file in the same PR.

## 1. Module ownership

| Dev | Module | Owns (backend + its UI) |
|---|---|---|
| **D1** | Platform, Access and Governance | Repo/CI, schema, seed, auth/RBAC, audit, admin config API+UI, access sharing, purge/auto-close, admin dashboard, notification UI, production deploy |
| **D2** | Ingestion and Intelligence | IMAP, filters, attachments, pipeline runner, OCR, analyser, evaluation, thread/duplicate/similar linking, SMS/WhatsApp adapters, triage queue, hardening, load/resilience tests |
| **D3** | Ticket Lifecycle, Routing and Notifications | State machine, ticket service+API, routing, scheduler timers, notification core/WebSocket/email, staff UI, reassign, security fast path, staging, docs |

## 2. Python interfaces

```python
# ---- D1: services/audit.py ------------------------------------------------
async def log_audit(session, *, ticket_id: UUID | None, actor_user_id: UUID | None,
                    actor_type: Literal["user", "system"], action: str,
                    reason_code: str | None = None, detail: dict | None = None) -> None: ...

# ---- D1: core/deps.py + services/access.py -------------------------------
async def can_access(session, user, ticket, need: Literal["view", "edit"] = "view") -> bool: ...
# deps: get_current_user, require_admin, require_ticket_access(need)

# ---- D1: services/settings.py --------------------------------------------
async def get_setting(session, key: str) -> Any: ...   # DB value, else env default (Appendix B)

# ---- D3: services/tickets.py ---------------------------------------------
@dataclass
class IncomingMessage:
    ingest_log_id: UUID; message_id_header: str | None; in_reply_to: str | None
    references: list[str]; subject: str; body_text: str
    sender_email: str; sender_name: str | None; sent_at: datetime
    attachments: list["StoredAttachment"]          # already validated by D2

async def create_ticket_from_email(session, msg: IncomingMessage) -> Ticket: ...   # status Submitted, needs_triage=True until analysed
async def append_message(session, ticket: Ticket, msg: IncomingMessage) -> Message: ...
async def transition(session, ticket: Ticket, to_status: str, *, actor: Actor,
                     reason_code: str | None = None, resolution_notes: str | None = None) -> Ticket: ...
    # THE ONLY place status changes. Validates (spec 9.1), audits, emits events. Raises IllegalTransition.
async def apply_analysis(session, ticket: Ticket, analysis: "Analysis") -> Ticket: ...  # writes category/type/priority/confidence/summary/needs_triage

# ---- D3: services/routing.py ---------------------------------------------
async def route_ticket(session, ticket: Ticket) -> RoutingResult: ...        # spec 9.3 steps 1-5, sets assignee + ack_deadline_at, status Assigned
async def reassign_next(session, ticket: Ticket, reason_code: str, *, actor: Actor) -> RoutingResult: ...  # step 6

# ---- D3: notifications/service.py ----------------------------------------
async def emit_event(session, event: str, ticket: Ticket, *, recipients: list[User] | None = None,
                     payload: dict | None = None) -> None: ...
# event names: spec 15.1. Recipients default per the table in 15.1.
class NotificationChannel(ABC): ...   # spec 15.2. D3 registers in_app + email. D2 registers sms + whatsapp.

# ---- D2: ai/analyzer.py --------------------------------------------------
class Analyzer(ABC): async def analyze(self, text: str, ocr_text: str = "") -> Analysis   # spec 14.4
def get_analyzer() -> Analyzer

# ---- D2: pipeline/matching.py --------------------------------------------
async def find_matching_ticket(session, msg: IncomingMessage, embedding: list[float]) -> MatchResult: ...   # spec 9.4
# ---- D2: pipeline/runner.py ----------------------------------------------
# ARQ job: process_email(ctx, ingest_log_id: UUID)   # runs steps P1-P12 in order
```

## 3. Queue job names (ARQ)

| Job | Owner | Trigger |
|---|---|---|
| `process_email(ingest_log_id)` | D2 | After the IMAP poller stores a raw email |
| `send_notification(notification_id)` | D3 | `emit_event` (retries 10 s, 30 s, 90 s) |
| `send_client_email(message_id)` | D3 | Auto-acknowledgement and staff replies |
| `check_ack_timeouts()` (cron, 30 s) | D3 | Scheduler |
| `check_resolve_deadlines()` (cron, 60 s) | D3 | Scheduler |
| `auto_close_resolved()` (cron, hourly) | D1 | Scheduler |
| `purge_closed()` (cron, hourly) | D1 | Scheduler |
| `imap_poll()` (cron, `IMAP_POLL_SECONDS`) | D2 | Scheduler |

## 4. Conventions every agent must follow

1. Async SQLAlchemy 2 sessions only. One session per request or job. Services take a `session`, never create their own.
2. **Status changes only through `transition()`.** Assignment only through `route_ticket` / `reassign_next` / admin reassign (D3).
3. Every state change, assignment, access change, config change and purge calls `log_audit`.
4. Thresholds, limits and intervals come from `get_setting()`. Never hard-code them. Taxonomy comes from the database.
5. Never log message bodies, OCR text or personal data. Never put secrets in git.
6. Errors: `{ "detail": "...", "code": "..." }`. Lists use `page`, `page_size`, `sort`.
7. Return 404 (not 403) when a staff member asks for a ticket they cannot access, so ticket existence is not leaked.
8. Each PR includes tests for the business logic it adds, and updates the OpenAPI/docs it touches.
9. Redis keys: `imap:last_poll`, `queue:depth`, `ws:user:{id}` (pub/sub channel), `status:*` for health flags.

## 5. Frontend route ownership (SvelteKit)

| Route | Owner |
|---|---|
| `/login`, layout, nav, API client, shared components | D3 |
| `/tickets`, `/tickets/[ref]`, `/dashboard` (staff), `/profile` | D3 |
| `/admin/reassign` (modal on ticket detail) | D3 |
| `/admin/taxonomy`, `/admin/users`, `/admin/limits`, `/admin/blocklist`, `/admin/settings`, `/admin/audit` | D1 |
| `/admin/dashboard`, notification bell/toast/list component, `/access` (requests + approvals) | D1 |
| `/admin/uncategorised` | D2 |
