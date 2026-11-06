# D2 · Ingestion and Intelligence

**You own:** everything between the mailbox and the ticket: IMAP polling, filters, attachment validation, the pipeline runner, OCR, the analyser and its evaluation, thread/duplicate/similar-ticket matching, SMS and WhatsApp adapters, the Uncategorised (triage) queue, hardening, and load/resilience tests.

**Study first (about 2 hours):** `M00`, `M03`, `M06` (all of it), `M02` section 9.4, `M07` section 15.2-15.3, `M10`. Then `M04` (ingest_log, messages, attachments).

**How to use this file:** one agent session per task. Paste the "Prompt" block, point the agent at the "Read" files, review the diff, run tests, merge.

| Task | Sprint / Days | Depends on | Task |
|---|---|---|---|
| D2-01 | S1 · Day 1-2 | D1-02 | IMAP poller |
| D2-02 | S1 · Day 2-3 | D2-01 | Filters, attachment validation, queue |
| D2-03 | S1 · Day 2-4 | P0-04 | Labelled data, baseline analyser, eval script |
| D2-04 | S1 · Day 4-5 | D2-02, D3-02 | Pipeline runner (steps P1-P6) |
| D2-05 | S2 · Day 6 | D2-04 | OCR |
| D2-06 | S2 · Day 7 | D2-03, D2-04 | Analyser integration (P8) and triage fallback |
| D2-07 | S2 · Day 8-9 | D2-06, D1-09 | Thread matching, duplicates, similar links |
| D2-08 | S2 · Day 9-10 | D3-06 | SMS and WhatsApp adapters |
| D2-09 | S2 · Day 10 | D2-06 | Gate: AI evaluation and tuning |
| D2-10 | S3 · Day 11-12 | D3-05 | Uncategorised queue (API and UI) |
| D2-11 | S3 · Day 12-13 | all S2 | Hardening and security checklist |
| D2-12 | S3 · Day 13 | D1-11 | Resilience and load tests |
| D2-13 | S3 · Day 15 | all | Stretch: local LLM summaries, voice (only if on track) |

**Hand-offs you owe others:** `Analyzer` interface and `Analysis` dataclass by Day 4 (D3 `apply_analysis`). `IncomingMessage` and `StoredAttachment` dataclasses agreed with D3 on Day 1. `imap:last_poll` and `queue:depth` Redis keys by Day 3 (D1-11, D3-11). **You depend on D3-02 (`create_ticket_from_email`) landing by end of Day 3**: until then stub it as per AGENTS.md.

---

## D2-01 · IMAP poller

**Read:** `docs/spec/M06-ingestion-and-ai.md` (14.1 P1), `docs/spec/M01-requirements.md` (FR-01), `docs/spec/M04-data-model.md` (ingest_log), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md (pipeline step P1), docs/spec/M01-requirements.md FR-01, docs/spec/M04-data-model.md (ingest_log) and docs/spec/M10-shared-contracts.md.

Task: implement backend/app/pipeline/ingestion.py.
1. Poll the mailbox (IMAP_* env settings) with imap-tools every IMAP_POLL_SECONDS as an ARQ cron job imap_poll(). Fetch by UID, tracking UIDVALIDITY (if it changes, handle safely without reprocessing: rely on the unique index).
2. Parse MIME: charset handling, HTML to plain text (never keep raw HTML for display), body, subject, sender name/address, Message-ID, In-Reply-To, References, headers Auto-Submitted / Precedence / List-Unsubscribe, attachments (filename, mime, size, bytes). Save the raw .eml to a storage path outside any web root with a random name.
3. Idempotency: first INSERT the ingest_log row (mailbox, uidvalidity, imap_uid, message_id_header, from_email, raw_path) using ON CONFLICT DO NOTHING; only if the insert happened, enqueue the ARQ job process_email(ingest_log_id). Mark the IMAP message seen only after the job is safely enqueued.
4. Resilience: reconnect with exponential backoff, never crash the worker on IMAP errors, write Redis imap:last_poll after every successful poll and status:imap = "down" with an error time when failing; if IMAP is down the cron simply tries again.
5. Define the dataclasses IncomingMessage and StoredAttachment exactly as in M10 in backend/app/pipeline/types.py.
Tests: use a fake/mock IMAP (or a GreenMail container in compose) with 20 emails including Unicode, HTML-only and attachment cases; restarting the poller mid-batch creates no duplicates and loses nothing.
Done when: S1-06 style test passes: 20 emails -> 20 ingest_log rows, 20 queued jobs, zero duplicates after a restart.
```

**Reqs:** FR-01, NFR-06.

---

## D2-02 · Filters, attachment validation, queue behaviour

**Read:** `docs/spec/M06-ingestion-and-ai.md` (P2-P4), `docs/spec/M01-requirements.md` (FR-02, FR-03), `docs/spec/M00-context-and-decisions.md` (D-09..D-11)

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md (steps P2, P3, P4), docs/spec/M01-requirements.md FR-02 and FR-03, docs/spec/M00-context-and-decisions.md decisions D-09, D-10, D-11.

Task: implement backend/app/pipeline/filters.py and attachments.py and the queue retry policy.
1. Sender/automation filter (P2): Auto-Submitted (anything except "no"), Precedence bulk/junk/list, List-Unsubscribe, mailer-daemon/postmaster, no-reply patterns, and the blocked_senders table (exact or @domain). Each match sets ingest_log.decision to filtered_spam or filtered_blocked with a reason string.
2. Empty rule (P3): no usable body text and no attachments -> filtered_empty. (Screenshot-only mail is NOT empty; it continues.)
3. Attachment validation (P4): max MAX_ATTACHMENT_MB (use get_setting), allowed types png/jpg/jpeg/webp/pdf and mp3/m4a/wav/ogg, checked by FILE SIGNATURE (magic bytes), not the extension; detect corruption (Pillow verify for images, open check for PDF, header check for audio). Rejected files get status rejected/corrupt with reject_reason; the email still continues and the ticket will be created from the text. Store accepted files with random names outside the web root.
4. Queue policy for process_email: ARQ retries with backoff (10 s, 30 s, 90 s, 5 min), then move to a dead-letter list (Redis list or table) and write ingest_log.decision=error with the exception class (no bodies). A dead-letter count must be exposed as Redis queue:dead.
Every filtered or discarded email MUST appear in ingest_log with a reason; nothing is silently dropped.
Tests: one test per rule, spoofed extension (exe renamed .png) rejected, 11 MB file rejected, corrupted PNG rejected, oversize/invalid attachment does not stop ticket creation.
Done when: AC-03, AC-04, AC-05 behaviours are proven by tests.
```

**Reqs:** FR-02, FR-03, AC-03..05.

---

## D2-03 · Labelled test set, baseline analyser prototype, evaluation script

**Read:** `docs/spec/M06-ingestion-and-ai.md` (all), `docs/spec/M02-domain-rules.md` (8, 9.2)

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md (all of section 14) and docs/spec/M02-domain-rules.md sections 8 and 9.2.

Task: build the baseline analyser and its evaluation tooling, runnable without the rest of the system.
1. data/labelled_emails.json: if real anonymised emails are not available, generate at least 60 synthetic complaint emails from the taxonomy (at least 8 per category, covering several complaint types, varied tone and length, some with amounts/invoice numbers, some multi-topic, some very short, some with urgency words). Include edge-case entries: screenshot-only (ocr_text provided), empty, duplicate pair, reply, spam. Fields: id, subject, body, ocr_text, expected_category, expected_type, expected_priority, kind.
2. backend/app/ai/embeddings.py (small MiniLM sentence-transformers model, CPU, loaded once, cached) and backend/app/ai/text_clean.py (strip signatures and quoted replies).
3. backend/app/ai/analyzer.py: the Analysis dataclass, Analyzer ABC and get_analyzer() exactly as in section 14.4 and M10.
4. backend/app/ai/baseline.py: BaselineAnalyzer = embeddings + scikit-learn logistic regression over complaint types; category follows from the type; confidence = predicted probability. Priority from the section 9.2 rules (CAT-06, System downtime, Suspected account compromise = critical; the High list; Low = feature requests; else medium), raised one level (max high) by urgency words ("urgent", "again", "third time", "still not fixed", "asap"). Summary: extractive and templated per 14.2 step 6; mask anything that looks like a card or account number (Luhn-valid 13-19 digits, long digit strings) before writing it; never include them. suggested_solution stays None.
5. scripts/train_classifier.py (trains from the labelled set, saves a versioned model file) and scripts/eval_analyzer.py (train/test split or cross-validation; prints category accuracy, type accuracy, confusion matrix, share routed to triage at the current threshold, average and p95 time per email).
Tests: masking, priority rules table-driven, urgency raise, output shape, analyzer p95 under 10 s on CPU for the test set.
Done when: `python scripts/eval_analyzer.py` prints the metrics. Record the first numbers in docs/ai-eval.md.
```

**Reqs:** FR-06, NFR-02, O-11, O-12.

---

## D2-04 · Pipeline runner (steps P1-P6) and ticket creation

**Read:** `docs/spec/M06-ingestion-and-ai.md` (14.1), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md section 14.1 (the P1-P12 table) and docs/spec/M10-shared-contracts.md.

Task: implement backend/app/pipeline/runner.py, the ARQ job process_email(ctx, ingest_log_id).
1. Load the stored raw email and ingest_log row, build the IncomingMessage, then run the ordered steps. Make each step its own small function in pipeline/steps/ taking a shared PipelineContext, so later tasks add steps without touching the runner. Log every step (name, duration, outcome) as structured logs without bodies.
2. Implement P1-P6 using D2-02 filters/attachments: filter -> empty check -> attachment validation -> (P5 placeholder for thread/duplicate check, returns "no match" for now) -> create the ticket with create_ticket_from_email (D3-02 service; stub marked # STUB(owner D3) if it is not merged yet) -> enqueue send_client_email for the auto-acknowledgement (D3-06; stub if missing).
3. Leave empty, clearly named placeholder steps for P7 (OCR), P8 (analyse), P9 (similar links), P10 (route), P11 (notify), P12 (audit) so the order is visible. Each must be a safe no-op until implemented.
4. Idempotent: running the same job twice must not create two tickets (guard with ingest_log.decision/ticket_id). Update ingest_log.decision and ticket_id at the end.
Tests with fixture emails: normal email -> ticket Submitted with needs_triage true; spam, empty, blocked are logged and create no ticket; email with an invalid attachment still creates a ticket; job re-run creates no duplicate.
Done when: a real email in the test mailbox becomes a ticket with attachments in the staging UI (S1 exit check).
```

**Reqs:** FR-04, FR-25.

---

## D2-05 · OCR for screenshots

**Read:** `docs/spec/M06-ingestion-and-ai.md` (P7, 14.5), `docs/spec/M00-context-and-decisions.md` (D-08, D-09)

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md (step P7 and known limitations 14.5) and docs/spec/M00-context-and-decisions.md D-08 and D-09.

Task: implement OCR as pipeline step P7 (pipeline/steps/ocr.py) with backend/app/ai/ocr.py.
- pytesseract on accepted image attachments, with light preprocessing (grayscale, upscale small images, threshold). Per-image timeout (10 s). Extract text from PDF attachments with a PDF text library (no OCR of PDF pages in release 1).
- Store the extracted text in messages.ocr_text (combined, with no file contents logged).
- Empty-content rule (D-09): if the email body is empty or trivial and OCR yields no meaningful words (fewer than 5 alphabetic tokens of 3+ letters), mark needs_triage with the note "no issue detected" and skip analysis; the ticket stays and the admin sees it. Screenshot with readable text proceeds to analysis.
- OCR failure never fails the job: log, continue with text only.
- Add tesseract-ocr to the backend Dockerfile.
Tests with 3 generated PNG fixtures (readable complaint text, blank image, gibberish).
Done when: AC-02 passes: screenshot-only email with readable text is classified in step P8 (once D2-06 lands), one without text is flagged for triage.
```

**Reqs:** FR-05, D-08, D-09, AC-02.

---

## D2-06 · Analyser integration (P8) and triage fallback

**Read:** `docs/spec/M06-ingestion-and-ai.md` (P8, 14.2, 14.3), `docs/spec/M01-requirements.md` (FR-06, FR-07), `docs/spec/M10-shared-contracts.md`

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md (P8, 14.2, 14.3), docs/spec/M01-requirements.md FR-06 and FR-07 and docs/spec/M10-shared-contracts.md.

Task: implement pipeline step P8 and the P10/P11 hooks for triage.
1. P8: build the text (subject + body + OCR, cleaned), call get_analyzer().analyze, and persist through D3's apply_analysis(session, ticket, analysis) (stub if missing). Persist category, complaint type, priority, confidence, summary.
2. Threshold: CONFIDENCE_THRESHOLD via get_setting. Below it -> needs_triage = true, category left empty, summary still stored, emit ticket.needs_triage (admin, in-app + email) via emit_event. The ticket is NOT routed to a department; it waits in the Uncategorised queue (assignee null, department null).
3. Analyser exceptions -> needs_triage with a note; never fail the job.
4. Keyword fallback for types without training examples: BaselineAnalyzer must also consult complaint_types.keywords from the DB so a type the admin just created can be matched without retraining (AC-17). Blend simply: if no trained type reaches the threshold but a keyword set matches, return that type with a fixed modest confidence (configurable) and flag source="keywords" in the analysis detail.
5. Wire P10: if not needs_triage, call route_ticket (D3-05); P11 emit ticket.assigned happens inside routing/notification code (D3). Keep your step a thin call.
Tests: confident ticket gets category and is routed; vague email lands in triage and the admin is notified; analyser raising an exception lands in triage; new admin-created type with keywords is matched.
Done when: AC-01 (up to routing), AC-06 pass.
```

**Reqs:** FR-06, FR-07, AC-01, AC-06, AC-17.

---

## D2-07 · Thread matching, duplicates, similar tickets

**Read:** `docs/spec/M02-domain-rules.md` (9.4), `docs/spec/M01-requirements.md` (FR-12..FR-14), `docs/spec/M09-testing-and-release.md` (AC-09, AC-10)

```text
Read AGENTS.md, docs/spec/M02-domain-rules.md section 9.4 and 9.1 (reopen rows), docs/spec/M01-requirements.md FR-12 to FR-14, AC-09 and AC-10 in docs/spec/M09-testing-and-release.md, and docs/spec/M10-shared-contracts.md.

Task: implement pipeline/matching.py with find_matching_ticket and wire it into step P5 and P9.
P5 (before ticket creation), in this order:
1. Thread headers: In-Reply-To / References match a stored messages.message_id_header -> that ticket.
2. Reference in the subject, regex \[TKT-\d{6}\] -> that ticket.
3. Same sender, open ticket from the last 30 days, embedding cosine >= SIMILAR threshold (0.80, get_setting) -> treat as a reply.
4. Otherwise a new ticket.
If matched: if cosine >= DUPLICATE_SIMILARITY (0.92) against a message already on the ticket and there is no new attachment -> discard, ingest_log decision discarded_duplicate with reason; else append via append_message (D3-02) and emit ticket.reply_received to the assignee. If the ticket is Resolved or Closed, call D1-09's can_reopen: inside the window transition to Reopened through transition() and let routing assign; outside the window create a NEW ticket linked as followup. Pending Client Response goes back to In Progress (via transition).
P9 for new tickets: compare with open tickets from OTHER clients in the same category, cosine >= 0.80 creates a related link (ticket_links). Never merge.
Store each message embedding (real[]) and compare in Python against only recent open tickets (volume is small).
Tests (table-driven): header match, subject match, same-sender similarity, identical resend discarded, different wording linked, cross-client related link, reply to Resolved reopens, reply after window creates followup.
Done when: AC-09 and AC-10 pass.
```

**Reqs:** FR-12, FR-13, FR-14, AC-09, AC-10.

---

## D2-08 · SMS and WhatsApp adapters

**Read:** `docs/spec/M07-notifications.md` (15.2, 15.3), `docs/spec/M08-security-and-config.md` (Appendix B)

```text
Read AGENTS.md, docs/spec/M07-notifications.md sections 15.2 and 15.3, docs/spec/M08-security-and-config.md Appendix B and docs/spec/M10-shared-contracts.md.

Task: implement SmsChannel and WhatsAppChannel as NotificationChannel subclasses (backend/app/notifications/channels/sms.py, whatsapp.py) and register them with D3's channel registry.
- Provider-agnostic design: a SmsProvider interface (send(to, text) -> bool) selected by SMS_PROVIDER, with (a) a "log" provider that only logs the ticket ref and result, for dev, (b) a generic HTTP provider configurable by env, (c) a clearly marked place to add the firm's chosen provider class. Keys only from env (SMS_API_KEY, SMS_SENDER_ID, WHATSAPP_API_KEY, WHATSAPP_PHONE_ID); the system must start and run with them empty.
- SMS text: short, only ticket ref and priority, no complaint content. Example: "New ticket TKT-000124 (High) assigned to you. Open the app to acknowledge."
- WhatsApp: pre-approved template messages only; template name and parameters ({{1}} ref, {{2}} priority, {{3}} short summary label) configurable; the user must have opted in (users.channels contains whatsapp and a whatsapp_number).
- Return False (do not raise) on provider errors so D3's retry/backoff handles it; log the error class without secrets. Timeouts of 10 s.
- Phone number normalisation to E.164 (default country Nigeria +234 when a local number starts with 0).
Tests with mocked HTTP: success, provider 500 (retry path), missing key (channel disabled with a clear log), number normalisation, message content contains no complaint text.
Done when: sandbox messages are delivered when keys exist, and a failing key is retried and finally flags the ticket as unacknowledged (AC-08, with D3-06).
```

**Reqs:** FR-09, D-22, AC-08.

---

## D2-09 · Gate: AI evaluation and tuning

**Read:** `docs/spec/M06-ingestion-and-ai.md` (14.6), `docs/spec/M00-context-and-decisions.md` (O-12)

```text
Read AGENTS.md and docs/spec/M06-ingestion-and-ai.md section 14.6 and open items O-11 and O-12 in docs/spec/M00-context-and-decisions.md.

Task: run the Sprint 2 evaluation gate on the REAL pipeline output (process the labelled emails through process_email on the test stack, not just the analyser in isolation).
1. Extend scripts/eval_analyzer.py with a --pipeline mode that feeds the labelled emails through the pipeline and compares the resulting tickets with the expected labels.
2. Report: category accuracy, type accuracy, confusion matrix, share routed to needs_triage, wrong-but-confident errors (the dangerous ones), time per email.
3. Tune CONFIDENCE_THRESHOLD, DUPLICATE_SIMILARITY and SIMILAR_LINK_SIMILARITY on the set and choose defaults. If category accuracy is below 80 percent, add examples (especially for the confused categories listed in the matrix), retrain, and re-measure. Do not tune on the same emails you report on: hold out a test split.
4. Write docs/ai-eval.md with method, numbers, chosen thresholds and known weak spots. Update the seed defaults.
Done when: category accuracy is at or above 80 percent on the held-out set, or the team has agreed in writing what to do about the shortfall.
```

**Reqs:** O-12, FR-06. *(All three devs review the result.)*

---

## D2-10 · Uncategorised queue (API and UI)

**Read:** `docs/spec/M05-api.md` (13.2), `docs/spec/M01-requirements.md` (FR-07, UC-17)

```text
Read AGENTS.md, docs/spec/M05-api.md section 13.2 (classification endpoint), docs/spec/M01-requirements.md FR-07 and use case UC-17, and docs/spec/M10-shared-contracts.md.

Task:
1. PATCH /api/v1/tickets/{ref}/classification (admin only): body category_id, complaint_type_id, optional department_id. Validate the type belongs to the category, set the values, clear needs_triage, audit it with before/after, then call route_ticket (D3-05) so the ticket gets a department and staff and the normal notification flow runs.
2. Store the admin's correction as labelled data (table or JSONL export) so scripts/train_classifier.py can include admin-corrected examples next time.
3. UI /admin/uncategorised: queue of needs_triage tickets (oldest first) showing the summary, original text, OCR text, the analyser's best guess with confidence, and a form to pick category and type (type dropdown filtered by category) and assign. Plain-text rendering only.
Tests: invalid type/category pair rejected, staff gets 403, a classified ticket is routed and the assignee is notified, correction recorded.
Done when: the S2 demo step "vague email lands in Uncategorised, admin classifies it, it gets routed" works end to end.
```

**Reqs:** FR-07, FR-17, UC-17, AC-06.

---

## D2-11 · Hardening and security checklist

**Read:** `docs/spec/M08-security-and-config.md` (section 16), `docs/spec/M09-testing-and-release.md` (23.1)

```text
Read AGENTS.md, docs/spec/M08-security-and-config.md section 16 and docs/spec/M09-testing-and-release.md sections 23.1 (security row) and 24.

Task: harden the system and produce evidence.
1. Rate limits (login already exists; add per-IP/per-user API limits via Redis), request body size limits, secure headers (HSTS handled by Caddy; add CSP, X-Content-Type-Options, frame options in the app), strict CORS to APP_BASE_URL.
2. Verify attachment handling: signature checks, size limits, random storage names, files never served inline or executed, download with Content-Disposition attachment.
3. Verify all email content is displayed as plain text (no raw HTML rendering anywhere in the frontend); add tests/checks.
4. Security tests: RBAC bypass attempts on EVERY ticket, message and attachment endpoint (IDOR by ref and UUID), login brute force, malformed JWT, upload abuse (zip bomb-sized image, polyglot file, path traversal filename), SQL/command injection attempts in filters and search `q`.
5. Dependency audit: pip-audit and npm audit in CI; fix or document findings.
6. Fill docs/security-checklist.md from section 16, one row per requirement with the evidence (test name or file).
Do not change business logic owned by other modules; open a ticket/note for any defect you find and fix only security-relevant ones in the smallest possible change.
Done when: the checklist is complete with evidence and the new tests pass in CI.
```

**Reqs:** NFR-07.

---

## D2-12 · Resilience and load tests

**Read:** `docs/spec/M09-testing-and-release.md` (AC-16, AC-18), `docs/spec/M01-requirements.md` (FR-25, NFR-05, NFR-06)

```text
Read AGENTS.md, docs/spec/M09-testing-and-release.md (AC-08, AC-16, AC-18 and 23.1), docs/spec/M01-requirements.md FR-25, NFR-05, NFR-06.

Task: write scripts/load_test.py and scripts/chaos_test.sh and run them on staging.
1. Load: generate 500 varied emails (mix from the labelled set plus replies, duplicates, spam, empty and bad attachments) delivered to the test mailbox over a compressed window (and one run spread over an hour). Verify: zero lost emails (every UID has an ingest_log row), zero duplicate tickets, correct decisions for the planted spam/empty/duplicate emails, p95 analysis time, queue depth over time.
2. Chaos, each followed by recovery verification: stop the IMAP connection (block the port), stop Redis for 2 minutes, kill the worker mid-batch, break the SMS API key, kill Postgres briefly. After recovery everything queued is processed exactly once and in order, and the admin dashboard showed the degraded state during the outage (needs D1-11) and cleared after.
3. Write docs/test-report.md: method, numbers, charts as simple tables, defects found, fixes made.
Fix defects in your own modules; report others to their owner.
Done when: AC-16 and AC-18 are demonstrated with results saved in docs/test-report.md.
```

**Reqs:** FR-25, NFR-05, NFR-06, AC-16, AC-18.

---

## D2-13 · Stretch: local LLM summaries and voice transcription

**Only start if every other S3 task is on track. Otherwise move to the backlog.**

**Read:** `docs/spec/M06-ingestion-and-ai.md` (14.4, 14.5), `docs/spec/M01-requirements.md` (FR-26), `docs/spec/M09-testing-and-release.md` (cut-line, section 27)

```text
Read AGENTS.md, docs/spec/M06-ingestion-and-ai.md sections 14.4 and 14.5, docs/spec/M01-requirements.md FR-26 and the cut-line in docs/spec/M09-testing-and-release.md section 27.

Task (only if the VM has 16 GB RAM): 
1. LlmAnalyzer (AI_BACKEND=llm) behind the existing Analyzer interface, using a small local model via Ollama on the VM for the summary and suggested_solution ONLY; classification and priority stay with the baseline. Never send data to a third-party API. Timeout and fallback to the baseline summary on any failure. Never produce a suggested solution for payment, billing, contract, privacy or security categories.
2. Optional: voice-recording attachments transcribed locally with Whisper (small/base model) and the transcript added to the analysis text.
3. A timing benchmark (seconds per email) in docs/ai-eval.md.
Done when: switching AI_BACKEND changes behaviour without code changes and the benchmark is recorded.
```

**Reqs:** FR-26, D-21.
