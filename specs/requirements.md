# Qatar Foundation Admin Portal — Requirements

## 1. Overview

Build a Flask backend that powers the existing Admin UI in [`sky/`](sky/). The UI must remain unchanged. Backend covers admin auth and per-admin opportunity CRUD against PostgreSQL.

## 2. Glossary

- **Admin** — registered user of the portal.
- **Opportunity** — record created and owned by exactly one Admin.
- **EARS** — Easy Approach to Requirements Syntax (Ubiquitous, Event-driven, State-driven, Optional, Unwanted).

## 3. User Stories & EARS Acceptance Criteria

### US-1.1 Admin Sign Up

**Story:** As a new admin, I want to create an account so I can access the portal.

- **U-1.1.1** The system shall accept signup payloads containing `full_name`, `email`, `password`, `confirm_password`.
- **E-1.1.2** When any required field is missing or empty, the system shall reject the request with HTTP 422 and a per-field error.
- **U-1.1.3** The system shall validate that `email` matches RFC 5322 format.
- **U-1.1.4** The system shall require `password` length ≥ 8 characters.
- **E-1.1.5** When `password != confirm_password`, the system shall reject with HTTP 422.
- **F-1.1.6** If `email` is already registered, the system shall return HTTP 409 with message "Account already exists".
- **E-1.1.7** When signup succeeds, the system shall persist the admin and respond HTTP 201 so the UI can redirect to login.

### US-1.2 Admin Login

**Story:** As a registered admin, I want to log in to access the dashboard.

- **U-1.2.1** The system shall accept `email`, `password`, and `remember_me` (boolean).
- **F-1.2.2** If credentials are invalid, the system shall return HTTP 401 with the exact message "Invalid email or password" without indicating which field failed.
- **E-1.2.3** When credentials are valid, the system shall establish a server-side session bound to the admin.
- **O-1.2.4** Where `remember_me` is true, the system shall mark the session permanent with `REMEMBER_COOKIE_DURATION = 30 days`.
- **F-1.2.5** If `remember_me` is false, the system shall use a browser-session cookie that expires when the browser closes.
- **E-1.2.6** When session is established, subsequent calls to `GET /api/opportunities` shall return only opportunities owned by the logged-in admin.

### US-1.3 Forgot Password

**Story:** As an admin who forgot my password, I want a reset link.

- **U-1.3.1** The system shall accept `email` on `POST /api/auth/forgot-password`.
- **U-1.3.2** The system shall always respond HTTP 200 with the same generic success message regardless of whether the email exists.
- **F-1.3.3** If the email is registered, the system shall generate a single-use reset token, store its SHA-256 hash with `expires_at = now + 1h`, and log the reset URL to server stdout.
- **F-1.3.4** If the token is expired or already used, `POST /api/auth/reset-password` shall return HTTP 400 with message "Reset link is invalid or has expired".
- **E-1.3.5** When a valid token and new password are submitted, the system shall update the admin's password and mark the token used.

### US-2.1 View All Opportunities

- **E-2.1.1** When `GET /api/opportunities` is called by a logged-in admin, the system shall return all opportunities where `admin_id = current_user.id`.
- **U-2.1.2** Each opportunity in the response shall include `id`, `name`, `category`, `duration`, `start_date`, `description`.
- **F-2.1.3** If the admin has no opportunities, the system shall return HTTP 200 with an empty array `[]`.
- **U-2.1.4** The system shall not return any seeded or hardcoded data.

### US-2.2 Add a New Opportunity

- **U-2.2.1** The system shall accept `POST /api/opportunities` with required fields `name`, `duration`, `start_date`, `description`, `skills`, `category`, `future_opportunities` and optional `max_applicants`.
- **U-2.2.2** The system shall accept `category ∈ {Technology, Business, Design, Marketing, Data Science, Other}` and reject any other value with HTTP 422.
- **U-2.2.3** The system shall accept `skills` as a comma-separated string and persist it as a normalized list of trimmed non-empty strings.
- **F-2.2.4** If any required field is missing or empty, the system shall return HTTP 422 with per-field errors.
- **E-2.2.5** When the request is valid, the system shall persist the row with `admin_id = current_user.id` and respond HTTP 201 with the created object.

### US-2.3 Opportunities Persist After Login

- **U-2.3.1** Opportunities shall be stored in PostgreSQL.
- **F-2.3.2** If a request from admin A targets an opportunity owned by admin B, the system shall respond HTTP 404 (no enumeration leak).
- **U-2.3.3** The system shall not rely on browser memory or localStorage for data persistence.

### US-2.4 View Opportunity Details

- **E-2.4.1** When `GET /api/opportunities/<id>` is called by the owner, the system shall return all stored fields including optional `max_applicants`.
- **F-2.4.2** If the requester is not the owner, the system shall respond HTTP 404.

### US-2.5 Edit an Opportunity

- **E-2.5.1** When `PUT /api/opportunities/<id>` is called by the owner with valid payload, the system shall update only that row and respond HTTP 200 with the updated object.
- **U-2.5.2** The system shall apply the same field validations as create.
- **F-2.5.3** If the requester is not the owner, the system shall respond HTTP 404.

### US-2.6 Delete an Opportunity

- **E-2.6.1** When `DELETE /api/opportunities/<id>` is called by the owner, the system shall permanently delete the row and respond HTTP 204.
- **F-2.6.2** If the requester is not the owner, the system shall respond HTTP 404.
- **U-2.6.3** Confirmation prompt is a UI concern; the API shall not require a confirmation flag.

## 4. Non-functional Requirements

- **NFR-1** Passwords stored as bcrypt hashes (cost ≥ 12).
- **NFR-2** Sessions: `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- **NFR-3** CSRF protection via Flask-WTF on all state-changing routes.
- **NFR-4** All API responses are JSON; errors follow `{"error": "code", "message": "...", "fields": {...}}`.
- **NFR-5** Test coverage ≥ 80% on routes and models.
- **NFR-6** Migrations managed by Flask-Migrate / Alembic; no manual schema edits.

## 5. Out of Scope

- Email delivery (reset links logged only).
- Admin-to-admin sharing or roles beyond owner.
- File uploads, applicant-facing endpoints.
