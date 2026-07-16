# Program 2 Multi-Service Visit Track — Phase E

## Initial specialty form catalog

Status: implemented as idempotent synthetic/demo catalog seed.

Published version 1 is seeded for:

- generic specialist consultation;
- gastroenterology consultation;
- gynecology consultation using only the approved common consultation fields;
- aesthetic consultation;
- gastroscopy;
- colonoscopy;
- HarmonyCa treatment.

Gastroscopy and colonoscopy intentionally do not contain a generic `Status` field. Their finding areas, extent, interventions, specimens, complications, diagnoses and recommendations are separate controlled fields. HarmonyCa records product, quantity, unit, LOT, expiry, anatomical regions, technique, tolerance, complications, aftercare and signature instead of accepting only one unstructured sentence.

## Bindings

The seed creates specialty/activity defaults and explicit bindings for the existing coded gastroenterology, endoscopy, colonoscopy and HarmonyCa services. Bindings use stable service codes and form keys, never display names.

## Limitations before closure

- The governed form-administration screen, draft cloning, preview, explicit publish and retirement workflows still need implementation.
- Gynecology intentionally contains no invented specialty-specific clinical fields.
- New specialties and new field component types remain prohibited without approved definitions and bindings.

