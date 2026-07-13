# Program 2 — Phase E: Document Ingestion, OCR and Source Storage

## Status

Phase E provides one canonical ingestion contract for journey documents, immutable local source storage, processing jobs, a deterministic text-only OCR stub, a metadata-only classification candidate and an email-ingestion review boundary.

## Canonical pipeline

Supported intake channel values are `web_upload`, `ai_secretary_email`, `staff_upload`, `reception_scan`, `direct_scan` and `external_integration`. All accepted uploads create the existing `ClinicalDocument` entity and link it to `PatientJourney`, appointment, patient and clinical episode when one exists. No parallel document model was introduced.

The lifecycle is recorded as `received`, `stored`, `ocr_pending`, `ocr_completed` or `ocr_failed`, `classification_pending`, `classified`, and later review/summary states. Processing attempts are separate `DocumentProcessingJob` rows with provider, attempt count, status, error and result metadata.

## Source-of-truth rules

- The original byte stream is stored under a generated server path, never under a user-controlled path.
- Original filename, MIME type, byte length, SHA-256 checksum, channel, timestamp and provenance are stored.
- Source retrieval verifies the checksum.
- The stored source path cannot be changed through the document update API.
- OCR text and classification are derived layers; neither replaces the original source.

Baseline browser upload accepts PDF, JPEG, PNG, TIFF and plain text up to the configured size limit. Hardware scanner drivers are deferred; reception scan is represented as an upload channel.

## OCR boundary

`LocalDemoOCRProvider` is intentionally limited to UTF-8 plain text. For PDF and images it records `failed` with a visible provider-not-configured error. It never silently reports successful OCR. A live OCR vendor and credentials are not connected and remain not authorized.

## Classification boundary

The local classifier only inspects title and original filename. Its output is stored as a candidate with confidence and `review_required=true`. The human-selected document type remains authoritative.

## Email boundary

`EmailIngestionEnvelope` defines message ID, sender and attachment names. With no authorized mailbox integration, every message with an attachment returns `manual_review_required`; sender identity is never automatically matched to a patient. Messages without attachments are rejected. No mailbox was connected.

## RBAC and audit

Dedicated permissions cover upload, scan, source viewing and document processing review. Reception may upload and label a scan but may not execute OCR/classification review. Receipt, OCR queue/result and classification candidate actions are audited and source receipt also creates a journey event.

## Deferred

- production object storage and retention policy
- malware scanning service
- live mailbox connection
- live OCR provider
- automatic background worker
- scanner-specific driver
- Phase F source-linked AI summary
