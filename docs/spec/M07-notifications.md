# M07 · Notification events, channels, delivery rules, client emails

> Extracted from the master spec (SamConsultingFirm Ticket Management Tool v1.0). **Section numbers are unchanged**, so cross-references such as "section 9.3" still work: find the module that holds that section (see `README.md`).
> **Primary readers:** D3 (core), D2 (SMS/WhatsApp)

---

## 15. Notifications

### 15.1 Events and recipients

| Event | Recipients | Channels |
|---|---|---|
| `ticket.assigned` | New assignee | All the user has enabled |
| `ticket.reassigned` | Previous and new assignee, admin (if timeout) | All enabled |
| `ack.timeout` | Previous assignee, admin | In-app, email |
| `ticket.escalated` | Assignee, admin | All enabled |
| `ticket.needs_triage` | Admin | In-app, email |
| `ticket.security` | Incident contact, admin | All channels, immediately |
| `ticket.reply_received` | Assignee | All enabled |
| `access.requested` | Ticket owner | In-app, email |
| `access.decided` | Requester | In-app |
| `system.alert` (IMAP down, queue backlog) | Admin | In-app, email |

### 15.2 Adapter pattern

Every channel implements one interface, so adding or swapping a provider is one class. API keys come from environment variables, so they can be added at the end.

```python
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    name: str
    @abstractmethod
    async def send(self, recipient: str, message: str, ticket_ref: str) -> bool: ...

class InAppChannel(NotificationChannel): ...      # WebSocket push and DB row
class EmailChannel(NotificationChannel): ...      # SMTP
class SmsChannel(NotificationChannel): ...        # provider HTTP API, key from env
class WhatsAppChannel(NotificationChannel): ...   # WhatsApp Business API, template messages

CHANNELS = {c.name: c for c in [InAppChannel(), EmailChannel(), SmsChannel(), WhatsAppChannel()]}

async def notify(user, ticket, event):
    for ch in user.channels:
        ok = await with_retry(CHANNELS[ch].send, user.contact_for(ch), render(event, ticket), ticket.ref)
        record_delivery(ticket, user, ch, event, ok)
```

### 15.3 Delivery rules

- In-app: push over WebSocket immediately, with a stored row so missed events appear on next login.
- External channels: retry with backoff (for example 10 s, 30 s, 90 s). After the final failure, mark the notification failed and flag the ticket "unacknowledged" on the admin dashboard.
- A notification is "acknowledged" when the assignee clicks acknowledge in the app, which also moves the ticket to In Progress.
- WhatsApp: business-initiated messages must use pre-approved templates, and staff must opt in. Build and test against the provider's sandbox. Example template: `New ticket {{1}} ({{2}} priority) assigned to you: {{3}}. Open the app to acknowledge.`
- SMS: keep messages short, with no sensitive content, only the ticket ref and priority.

### 15.4 Client emails

- Auto-acknowledgement subject: `[TKT-000124] We received your complaint`. Body: thanks the client, gives the reference, says replies to this email are added to the same ticket. Contains no complaint details.
- Staff replies are sent through SMTP with the same `[ref]` in the subject and stored as outgoing messages.
