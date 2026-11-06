# SamConsultingFirm Ticket Management Tool: Developer Pack

The master spec is split into small modules and the build plan is rewritten as **agent prompts** for three backend engineers using Antigravity.

```
AGENTS.md                      <- rules the agent reads on every task (repo root)
docs/spec/                     <- the study modules (copy into the repo as docs/spec/)
docs/tasks/                    <- one file per developer, every task is a copy-paste prompt
```

## 1. Study modules (`docs/spec/`)

Section numbers from the master spec are preserved, so "section 9.3" always means the same thing.

| Module | Contains (master spec sections) | Read by |
|---|---|---|
| M00 Context and decisions | 1-5, glossary | Everyone, first |
| M01 Requirements | 6-7, use cases | Everyone |
| M02 Domain rules | 8 taxonomy, 9 lifecycle/priority/routing/matching/purge | D3 (all), D1 (9.1, 9.5), D2 (9.4) |
| M03 Architecture and setup | 10, 11, 18, 19 | Everyone |
| M04 Data model | 12 + addendum 12.A (gaps fixed) | Everyone, D1 owns |
| M05 API | 13 | By endpoint ownership |
| M06 Ingestion and AI | 14 | D2 owns |
| M07 Notifications | 15 | D3 core, D2 adapters |
| M08 Security and config | 16, Appendix B | D1, D2 |
| M09 Testing and release | 23-28 | Everyone |
| **M10 Shared contracts (new)** | Function signatures, job names, conventions, route ownership | Everyone, read before the first prompt |

## 2. Roles (all backend engineers, one vertical module each)

Each dev owns a business area end to end (backend and its screens), so the agent does the frontend work too and nobody is the "frontend person".

| Dev | Module | Tasks | Focus |
|---|---|---|---|
| **D1** | Platform, Access and Governance | 12 | Schema, auth/RBAC, audit, admin config, access sharing, purge, admin dashboard, production deploy |
| **D2** | Ingestion and Intelligence | 12 (+1 stretch) | IMAP, filters, pipeline, OCR, analyser and evaluation, matching, SMS/WhatsApp, triage, hardening, load tests |
| **D3** | Lifecycle, Routing and Notifications | 12 | State machine, ticket API, routing, timers, notification core, staff UI, reassignment, security fast path, staging, docs |

Why this split: each module has about the same amount of work per sprint, and the critical path (schema -> state machine -> pipeline -> routing -> notifications) is spread so nobody waits on one person for long. Task files: `docs/tasks/D1-...`, `D2-...`, `D3-...`.

## 3. Daily workflow with the agent

1. Pick the next task in your file. Check its "Depends on" are merged (or code against the stubs in M10).
2. Open a new agent session. Make sure `AGENTS.md` is in the repo. Paste the task's **Prompt** block.
3. Ask for the plan first, approve it, let the agent implement.
4. Run `ruff`, `pytest` (and `svelte-check`). Review the diff yourself against the "Done when" line.
5. PR, one review from a teammate, squash merge. Tick the task. Anything the agent stubbed or assumed goes in the PR description.
6. Keep prompts small. If a task grows, split it into two sessions, never one huge prompt.

Rules for the team: one owner per task. Feature freeze at the start of Day 13. Daily 15-minute standup. If a signature in M10 must change, all three agree first.

## 4. Calendar

| Day | D1 | D2 | D3 |
|---|---|---|---|
| 1 | D1-01, D1-02 (models first!) | D2-01 | D3-04 (mock data) |
| 2 | D1-02, D1-03 | D2-02, D2-03 | D3-04, D3-02 start |
| 3 | D1-04 | D2-03 | **D3-02 merged** |
| 4 | D1-05 | D2-03, D2-04 | D3-03 |
| 5 | Help D3-04, sprint demo | D2-04 | D3-01, sprint demo |
| 6 | D1-06 | D2-05 | D3-05 |
| 7 | D1-06, D1-07 | D2-06 | D3-06 |
| 8 | D1-07, D1-08 | D2-07 | D3-06, D3-07 |
| 9 | D1-08, D1-09, D1-10 | D2-07, D2-08 | D3-07, D3-08 |
| 10 | D1-09, D1-10, demo | D2-08, **D2-09 gate**, demo | D3-08, demo |
| 11 | D1-11 | D2-10 | D3-09, D3-10 |
| 12 | D1-11, D1-12 | D2-10, D2-11 | D3-10, D3-11 |
| 13 | D1-12 | D2-11, D2-12 | D3-12 (**feature freeze**, bug fixes only) |
| 14 | ALL-01: UAT with the firm | ALL-01 | ALL-01 |
| 15 | Fixes, go-live | Fixes, D2-13 stretch if on track | Fixes, handover |

**Sprint exit checks:** Sprint 1: 5 emails become tickets on staging within a minute, restart mid-batch loses and duplicates nothing, staff cannot open another staff member's ticket. Sprint 2: the four-step demo scenario (billing complaint with screenshot -> classified, routed, notified; ignored -> moves to backup with `ACK_TIMEOUT` audit; reply joins the same ticket; vague email lands in Uncategorised). Cut-line if Sprint 2 slips: `M09` section 27.

## 5. Gaps found in the original spec (already resolved in this pack)

| Gap | Resolution |
|---|---|
| No `settings` table for `/admin/settings`; no assignment history table although purge keeps "assignee history"; no `read_at`, `must_change_password` | Added in `M04` 12.A, built in D1-02 |
| "Append-only" audit log vs "admin can excuse a timeout" | Excuse is a new audit row `ACK_TIMEOUT_EXCUSED` (D1-05) |
| AC-17 (admin adds a type, next email is classified) is impossible with a trained classifier alone | `complaint_types.keywords` plus a keyword fallback in the analyser (D1-06, D2-06) |
| Staff cannot see other tickets, yet must "request access" | Request by ref, generic response, no details leaked (D1-08) |
| State machine was in Sprint 2 but everything depends on it | Moved to Sprint 1 (D3-02, Day 3) |
| Contract-first stubs only made sense with a separate frontend dev | Replaced by the function contracts in M10 |
| Purged tickets can still be reopened inside the window but have no content | Documented in D1-09; the reopened ticket starts with the new client message |

## 6. Still open with the firm (defaults in M00 section 5)

O-01 to O-12, especially: O-04 (HR department has no category), O-06 (incident contact), O-08 ("must run locally" meaning), O-11 (sample emails for evaluation), SMS provider choice. The tasks use the defaults.
