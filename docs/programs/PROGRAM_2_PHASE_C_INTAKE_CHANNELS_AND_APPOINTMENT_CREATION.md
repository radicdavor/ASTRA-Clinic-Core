# Program 2 Phase C — Intake Channels and Appointment Creation

## Canonical rule

Manual staff entry, web booking and AI secretary intake all call `create_appointment_with_journey`. The service applies the same patient/episode validation, provider/room/service scheduling rules, conflict checks, appointment audit and one-to-one journey creation.

| Channel | Existing/new boundary | Appointment source | Journey channel |
|---|---|---|---|
| Manual | `POST /api/appointments` | `manual` or existing staff source | `manual` |
| Web | `POST /api/intake/web/appointments` | forced `web_booking` | `web` |
| AI secretary | `POST /api/ai/appointments/create` | forced `ai_agent` | `ai_secretary` |

The web endpoint is an authenticated contract, not a public production portal. Public identity verification, rate limiting and consent UX remain a later deployment boundary. The AI endpoint retains scoped API-key permissions and cannot read unrestricted history, approve readiness, override conflicts, alter billing or make clinical decisions.

Patient creation continues through the canonical patient API (or scoped AI patient API). Duplicate detection remains required by the calling UI before creation. No channel owns a separate patient or appointment model.

Preparation/document requests are deliberately not sent inside the database transaction. Later phases create versioned assignments and queued communication events after the canonical journey exists.
