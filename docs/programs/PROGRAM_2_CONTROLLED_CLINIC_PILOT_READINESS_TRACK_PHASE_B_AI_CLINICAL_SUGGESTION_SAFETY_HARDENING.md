# Phase B — AI clinical suggestion safety hardening

AI diagnosis suggestions are a high-risk optional aid and are **disabled / pilot blocked**.

## Controls

- `AI_DIAGNOSIS_SUGGESTIONS_ENABLED=false` is the default in code, Compose and `.env.example`.
- A configured API key does not enable the endpoint.
- Production additionally requires `AI_DIAGNOSIS_SUGGESTIONS_PRODUCTION_AUTHORIZED=true`; unsafe enablement fails startup.
- The endpoint fails closed with HTTP 503 and a Croatian explanation when flag, key, production authorization or canonical catalog is absent.
- The repository has no authorized canonical WHO ICD-10 catalog. No catalog was invented or downloaded.
- Generated codes are normalized, unknown codes are rejected and labels are replaced with catalog labels when a repository catalog is supplied in a future authorized track.
- The request builder accepts only anamnesis, status, brought findings and physician opinion. It sends no name, birth date, identifier, appointment/journey ID or source binary. `store: false` is explicit but is not treated as GDPR/processor approval.

## User interface and audit

Suggestions are shown in a separate panel: **AI prijedlozi dijagnoza — nisu dio kliničkog nalaza dok ih liječnik pojedinačno ne prihvati.** They are never inserted automatically and there is no “accept all”. Each suggestion has `Dodaj u dijagnoze` and `Odbaci`.

Generation audit stores provider, model, count and synthetic request correlation, not clinical text. Individual acceptance/rejection stores actor/time through the audit service, encounter ID, provider/model, code and final canonical code. Acceptance is rejected if the code is not in the canonical catalog or the encounter is complete.

## Evidence and unresolved governance

Backend tests cover disabled state, missing boundaries, mocked provider, canonical-label replacement, unknown-code rejection, completed encounter, permission boundary, individual decisions, audit minimization and request payload. Frontend tests cover separation, individual actions, no automatic insertion, no accept-all and disabled state.

Because the canonical catalog, privacy review, processor governance and human evidence are absent, the final state remains: **AI diagnosis suggestions: DISABLED / PILOT BLOCKED**.
