# M06 · Email ingestion pipeline and analysis (AI)

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** D2 (owner)

---

## 14. Analysis (AI) design

The AI runs on the firm's own cloud VM with no third-party AI service (D-21). Because there is no GPU, the release 1 analyser is lightweight and deterministic. A small LLM is an optional upgrade.

### 14.1 Pipeline order (one job per email)

| Step | Action | Failure handling |
|---|---|---|
| P1 | Fetch and store the raw email, record in `ingest_log` | Duplicate UID means skip |
| P2 | Sender filter: automated headers (`Auto-Submitted`, `Precedence: bulk`, `List-Unsubscribe`), `mailer-daemon`, `no-reply`, blocklist | Log `filtered_*` |
| P3 | Empty body and no attachments means discard | Log `filtered_empty` |
| P4 | Attachment validation (size, signature, type, corruption) | Reject the file, keep the email |
| P5 | Thread and duplicate check (section 9.4) | Append or discard if matched |
| P6 | Create the ticket (Submitted), queue the client acknowledgement email | Retry the job |
| P7 | OCR images. If body is empty and OCR finds no meaningful words, mark `needs_triage` with note "no issue detected" | OCR error means continue with text only |
| P8 | Analyse (section 14.2) | Analyser error means `needs_triage` |
| P9 | Similar-ticket links | Skip on error |
| P10 | Route and assign (section 9.3) | No staff means admin queue |
| P11 | Notify | Retry, then flag unacknowledged on the dashboard |
| P12 | Audit entries | |

### 14.2 Baseline analyser

1. Build the text: subject plus body plus OCR text (cleaned of signatures and quoted replies).
2. Embed the text.
3. Predict the complaint type with a classifier trained on labelled examples. The category follows from the type. The probability is the confidence.
4. If confidence is below `CONFIDENCE_THRESHOLD` (default 0.60, tune on the test set), set `needs_triage` and leave category empty.
5. Priority: apply section 9.2 rules, including urgency words.
6. Summary: extractive and templated. For example: `"{type}: {subject}. Key points: {first two informative sentences}. Details: {amounts, dates, invoice or order numbers found by regex}."` Never include card or account numbers (mask them).
7. Suggested solution: not produced by the baseline (known limitation, see 14.5).

### 14.3 Output contract

Every analyser returns this shape (Python dataclass or dict):

```json
{
  "category_code": "CAT-03",
  "complaint_type": "Duplicate charges",
  "priority": "high",
  "confidence": 0.82,
  "summary": "Duplicate charges: client says they were charged twice for March. Details: invoice INV-2201, amount 45,000.",
  "suggested_solution": null
}
```

### 14.4 Swappable interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Analysis:
    category_code: str | None
    complaint_type: str | None
    priority: str
    confidence: float
    summary: str
    suggested_solution: str | None = None

class Analyzer(ABC):
    @abstractmethod
    async def analyze(self, text: str, ocr_text: str = "") -> Analysis: ...

class BaselineAnalyzer(Analyzer): ...   # embeddings + classifier + rules (release 1)
class LlmAnalyzer(Analyzer): ...        # small local LLM for summary and solution (stretch)

def get_analyzer() -> Analyzer:
    return {"baseline": BaselineAnalyzer, "llm": LlmAnalyzer}[settings.AI_BACKEND]()
```

### 14.5 Known limitations (tell the firm before UAT)

- No "likely solution" suggestions in release 1, and the summaries are extractive.
- Screenshots are read as text only (OCR). The system does not understand charts or UI layouts.
- Accuracy depends on the labelled examples. Wrong or uncertain classifications go to the Uncategorised queue for the admin, by design.

### 14.6 Evaluation (build this on Day 1 of the AI work)

- Labelled test set of 40+ emails covering all six categories (see O-11), including edge cases: screenshot-only, empty, duplicate, reply, multi-topic, spam.
- Script `scripts/eval_analyzer.py` reports category accuracy, type accuracy, confusion matrix, share routed to `needs_triage`, and time per email.
- Gate at end of Sprint 2: category accuracy at or above the target (O-12). If it is below, add examples and re-measure before moving on.

### 14.7 Future: AI auto-reply (not in release 1)

The hook is an `auto_reply_policy` table (category, complaint type, enabled) and a `send_ai_reply()` step after P8. Never enabled for payment, billing, contract, data-privacy or security types. Candidate light issues from the firm: login problems, site navigation, accessing resources, basic issues an average phone user can solve. Requires high confidence, human escalation, and an off switch.
