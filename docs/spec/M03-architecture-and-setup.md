# M03 · Architecture, tech stack, repo layout, kickoff

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** Everyone

---

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
