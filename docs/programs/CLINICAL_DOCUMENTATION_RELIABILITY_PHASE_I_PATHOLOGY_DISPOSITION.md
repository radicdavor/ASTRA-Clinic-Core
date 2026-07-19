# Phase I - Pathology communication disposition

Status: implemented for synthetic pathology follow-up.

A pathology case cannot close until a structured communication disposition is recorded. Direct closure from clinician review or notification-ready state is rejected without this disposition.

Supported communication dispositions include documented patient contact, follow-up-visit review, no notification required, declined notification, unable to contact, external-care transfer, and duplicate cancellation. Dispositions that require a clinical or administrative explanation require a note; unable-to-contact requires at least three documented attempts.

The workflow separates:

- physical visit closure;
- later pathology result receipt;
- clinician pathology review;
- communication disposition;
- pathology-case closure.

Pending pathology may remain open after the physical visit is closed.

No autonomous pathology interpretation or automatic patient communication is authorized.
