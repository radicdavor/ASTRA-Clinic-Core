# ADR: Web session authentication

Status: accepted for Module 2 — Full-stack Production Validation.

## Context

The previous browser login flow received a JWT access token from `/auth/login` and stored it in JavaScript-readable browser storage. That reduced exposure compared with long-lived local storage, but XSS could still read the token directly and reuse it outside the browser.

## Decision

Browser authentication now uses an opaque server-side session.

- Browser endpoint: `/auth/browser/login`
- Bearer token endpoint retained for non-browser clients: `/auth/login`
- Session cookie: `astra_session`
- CSRF cookie/header: `astra_csrf` and `X-CSRF-Token`
- Session lifetime: `BROWSER_SESSION_MINUTES`, default 480 minutes
- Storage: only a SHA-256 hash of the random session token is stored in `user_sessions`
- Logout: `/auth/browser/logout` revokes the server-side session and clears cookies
- Revocation primitive: backend service supports revoking all sessions for a user

The browser frontend no longer stores access tokens in `localStorage` or `sessionStorage`, and no browser API call sends an `Authorization: Bearer` header. It sends cookies with `credentials: "include"` and keeps only non-secret UI/session presentation state such as the current user display data and active clinic selection.

## Cookie policy

Production:

- `astra_session`: `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`
- `astra_csrf`: readable by JavaScript, `Secure`, `SameSite=Lax`, `Path=/`

Development and DB-backed E2E may use non-secure cookies because local tests run over HTTP. Production startup validation rejects explicitly insecure production cookie settings.

No cookie `Domain` is set by the application; deployment should keep cookies host-scoped unless a reviewed reverse-proxy design requires otherwise.

## Canonical public topology

Production browser authentication uses one public HTTPS origin. Nginx or the managed gateway serves React at `/` and proxies `/api/*` and `/auth/*` to FastAPI. The frontend uses relative same-origin requests; FastAPI may run on a private service address but that address is not a second browser origin. This is the only recommended browser deployment model. A cross-site frontend/API topology requires a separate reviewed contract and is not represented by the production example.

## CSRF and CORS

State-changing browser-session requests (`POST`, `PUT`, `PATCH`, `DELETE`) require a matching `X-CSRF-Token` header and `astra_csrf` cookie. The CSRF token is separate from the session token and does not authenticate the user.

The middleware also rejects disallowed `Origin` or `Referer` values when they are present. CORS is credentials-enabled only for explicit configured origins and explicit headers including `X-CSRF-Token` and `X-Clinic-Id`.

Bearer API and API-key requests remain supported without browser CSRF, because they are not cookie-authenticated browser requests.

## Bearer compatibility

`/auth/login` remains available for Swagger/OpenAPI, CLI use, integration tests and future non-browser clients. Browser login must not call it. If a request supplies conflicting browser cookie and Bearer/API-key credentials, the backend rejects it instead of silently choosing one identity.

## Clinic scope

The session stores only authentication continuity. It does not cache clinic memberships or permissions as authority. Current permissions and clinic memberships are resolved from current database state on protected requests.

## Cleanup and retention

Expired and revoked sessions can be removed through the session cleanup service. A production scheduler or maintenance command should call this periodically; request handling does not run expensive cleanup on every request.

## XSS limitation

HttpOnly cookies prevent JavaScript from directly reading the session token. They do not eliminate XSS risk: injected JavaScript could still attempt actions in the active browser session. Therefore React escaping, CSRF/Origin checks, CSP and careful rendering of clinical text remain necessary.

## Test strategy

The implementation is covered by:

- backend session, logout, revocation, CSRF and Bearer-compatibility tests;
- production configuration tests for secure cookies;
- CORS preflight and security header tests;
- frontend client tests proving no token storage and cookie credentials flow;
- DB-backed Playwright tests covering login, reload persistence, logout, clinic isolation and CSRF negative behavior.
