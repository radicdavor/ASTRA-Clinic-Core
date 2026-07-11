# Program 1 Synthetic Read-Only UI Evaluation Track Phase D

## Local Synthetic Evaluation Session Runner - Scope

Status: complete.

## Purpose

Phase D implements a moderator-facing local runner for the Phase C external clinician evaluation kit. It presents the controlled preflight, eight ordered tasks, transient status controls, stop handling, and reset behavior.

The runner is a guide, not a session record. It does not prove that a participant session occurred.

## Architecture Check

- human above software: the moderator retains responsibility and stop authority
- one source of truth: task wording is repository-controlled
- one shared language: Phase C safety, task, and stop terminology is preserved
- modular Clinic Core: isolated Program 1 frontend module and route
- API First: not applicable to transient presentation state; no domain behavior is added
- AI boundary: no AI output or decision
- audit boundary: no important system change occurs; controlled evidence remains outside the runner

Change category: information/read-only local presentation with transient UI state.

## Route

`/program1/synthetic-evaluation`

Navigation label: `Program 1 Evaluacija`.

## Prohibited Extensions

- no participant name, contact, organization, or free-text collection
- no patient or clinical-case input
- no localStorage, sessionStorage, cookie, IndexedDB, file, or database persistence
- no export, print, clipboard, download, upload, or screenshot function
- no backend Program 1 request or evaluation endpoint
- no session history, analytics, telemetry, or recording
- no automatic score, pass/fail, clinical conclusion, or recommendation
- no production, clinical use, or go-live authorization

