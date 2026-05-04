# Qatar Foundation Admin Portal — Implementation Tasks

Ordered checklist. Each task is independently executable in 💻 Code mode and traces back to specific EARS criteria in [`specs/requirements.md`](specs/requirements.md).

## Phase 0 — Project bootstrap

- [ ] **T0.1** Create `qatar-backend/` and run `uv init`.
- [ ] **T0.2** Add deps to [`pyproject.toml`](qatar-backend/pyproject.toml): `flask`, `flask-sqlalchemy`, `flask-migrate`, `flask-login`, `flask-bcrypt`, `flask-wtf`, `flask-cors`, `psycopg[binary]`, `pydantic`, `email-validator`, `python-dotenv`, `gunicorn`. Dev deps: `pytest`, `pytest-flask`, `pytest-cov`, `ruff`.
- [ ] **T0.3** Generate [`requirements.txt`](qatar-backend/requirements.txt) via `uv pip compile pyproject.toml -o requirements.txt`.
- [ ] **T0.4** Create [`.env.example`](qatar-backend/.env.example) listing every variable in design §10.
- [ ] **T0.5** Create [`run.py`](qatar-backend/run.py) calling `create_app()` and exposing `app` for gunicorn.
- [ ] **T0.6** Add `.gitignore` (Python, venv, `.env`, `__pycache__`, `.pytest_cache`, `migrations/versions/__pycache__`).

## Phase 1 — App skeleton

- [ ] **T1.1** Implement [`app/extensions.py`](qatar-backend/app/extensions.py) instantiating `db`, `migrate`, `login_manager`, `bcrypt`, `csrf`, `cors`.
- [ ] **T1.2** Implement [`app/config.py`](qatar-backend/app/config.py) with `BaseConfig`, `DevConfig`, `TestConfig`, `ProdConfig` pulling from env via `python-dotenv`.
- [ ] **T1.3** Implement [`app/__init__.py`](qatar-backend/app/__init__.py) `create_app(config_name)` that initializes extensions, registers blueprints, and registers error handlers.
- [ ] **T1.4** Configure CORS with `supports_credentials=True` and origin from `FRONTEND_ORIGIN`.
- [ ] **T1.5** Configure session cookies: `HttpOnly`, `SameSite=Lax`, `Secure` (prod), permanent + `REMEMBER_COOKIE_DURATION` for remember-me.

## Phase 2 — Database

- [ ] **T2.1** Define `Admin` (with `UserMixin`), `Opportunity`, `PasswordReset` in [`app/models.py`](qatar-backend/app/models.py) using SQLAlchemy 2.x typed mappings.
- [ ] **T2.2** Add the `category` Postgres enum and `skills` `ARRAY(Text)` column.
- [ ] **T2.3** Add `created_at` / `updated_at` defaults via `server_default=func.now()`.
- [ ] **T2.4** Register `user_loader` in extensions returning `db.session.get(Admin, uuid)`.
- [ ] **T2.5** Initialize migrations: `flask db init`, `flask db migrate -m "initial"`, `flask db upgrade`.
- [ ] **T2.6** Enable the `citext` extension in the initial migration before creating `admins.email`.

## Phase 3 — Schemas

- [ ] **T3.1** Implement Pydantic v2 schemas in [`app/schemas.py`](qatar-backend/app/schemas.py): `SignupIn`, `LoginIn`, `ForgotIn`, `ResetIn`, `OpportunityIn`, `AdminOut`, `OpportunityOut`.
- [ ] **T3.2** Add `EmailStr`, `min_length=8` on password fields, cross-field validator for `password == confirm_password`.
- [ ] **T3.3** Implement custom validator on `OpportunityIn.skills` to accept CSV string or list and normalize to `list[str]` (trimmed, non-empty).
- [ ] **T3.4** Constrain `OpportunityIn.category` to the enum literal type.
- [ ] **T3.5** Configure response models with `model_config = ConfigDict(from_attributes=True)` for ORM serialization.

## Phase 4 — Utilities

- [ ] **T4.1** Implement `owner_required` decorator in [`app/utils.py`](qatar-backend/app/utils.py) that loads the `Opportunity` by `<id>`, calls `abort(404)` if not owner, and injects the row into the wrapped handler.
- [ ] **T4.2** Implement `error_response(code, message, fields=None, status)` helper.
- [ ] **T4.3** Register handlers in `create_app` for `pydantic.ValidationError` → 422, `werkzeug.HTTPException` → JSON envelope, generic `Exception` → 500 (logged).
- [ ] **T4.4** Implement a small `parse_json(schema)` helper that calls `schema.model_validate(request.get_json(silent=True) or {})` and rethrows as `ValidationError`.

## Phase 5 — Auth blueprint

- [ ] **T5.1** Implement [`app/routes/auth.py`](qatar-backend/app/routes/auth.py) blueprint at `/api/auth`.
- [ ] **T5.2** `POST /signup` → validate `SignupIn`, hash via `bcrypt.generate_password_hash`, insert; on duplicate email return 409 with `Account already exists`. (US-1.1)
- [ ] **T5.3** `POST /login` → validate `LoginIn`, lookup admin, `bcrypt.check_password_hash`; on success `login_user(admin, remember=remember_me)` and on `remember_me` set `session.permanent = True`; on failure return 401 `Invalid email or password`. (US-1.2)
- [ ] **T5.4** `POST /logout` → `logout_user()` returns 204.
- [ ] **T5.5** `GET /me` → return current admin and ensure CSRF cookie is set on response.
- [ ] **T5.6** `POST /forgot-password` → always 200; if admin exists, generate `secrets.token_urlsafe(32)`, store `sha256(token)` with `expires_at=now+1h`, log `reset_url` via `current_app.logger.info`. (US-1.3)
- [ ] **T5.7** `POST /reset-password` → look up by `token_hash`, verify `expires_at>now` and `used_at IS NULL`; update admin password, mark token used; on failure return 400 with the standard error message. (US-1.3)

## Phase 6 — Opportunities blueprint

- [ ] **T6.1** Implement [`app/routes/opportunities.py`](qatar-backend/app/routes/opportunities.py) blueprint at `/api/opportunities`.
- [ ] **T6.2** `GET /` → list rows where `admin_id == current_user.id` (returns `[]` if none). (US-2.1, US-2.3)
- [ ] **T6.3** `POST /` → validate `OpportunityIn`, persist with `admin_id=current_user.id`, return 201. (US-2.2)
- [ ] **T6.4** `GET /<id>` → use `@owner_required`; return full row including optional `max_applicants`. (US-2.4)
- [ ] **T6.5** `PUT /<id>` → use `@owner_required`; validate, update only that row, return updated object. (US-2.5)
- [ ] **T6.6** `DELETE /<id>` → use `@owner_required`; delete row, return 204. (US-2.6)
- [ ] **T6.7** Register the blueprint in [`app/routes/__init__.py`](qatar-backend/app/routes/__init__.py) and apply `@login_required` consistently.

## Phase 7 — Frontend wiring (no UI changes)

- [ ] **T7.1** In [`sky/admin.js`](sky/admin.js), add an `api(path, opts)` helper that uses `credentials: 'include'` and injects `X-CSRFToken` from the `csrf_token` cookie for non-GET requests.
- [ ] **T7.2** Replace the auth flows (signup, login, forgot, reset, logout) to call `/api/auth/*`.
- [ ] **T7.3** Replace the opportunity list rendering with data from `GET /api/opportunities`; add empty-state message. (US-2.1)
- [ ] **T7.4** Wire create modal submit → `POST /api/opportunities`; append the new card without page refresh. (US-2.2)
- [ ] **T7.5** Wire details modal → `GET /api/opportunities/<id>`. (US-2.4)
- [ ] **T7.6** Wire edit modal → pre-fill from `GET`, submit `PUT`; refresh card in place. (US-2.5)
- [ ] **T7.7** Wire delete button → confirm prompt → `DELETE /api/opportunities/<id>`; remove card from DOM. (US-2.6)
- [ ] **T7.8** Remove all hardcoded opportunity cards (Full Stack, Data Science, etc.) from the JS bootstrap data.
- [ ] **T7.9** Verify [`sky/admin.html`](sky/admin.html) and [`sky/admin.css`](sky/admin.css) are unchanged.

## Phase 8 — Testing

- [ ] **T8.1** Set up [`tests/conftest.py`](qatar-backend/tests/conftest.py) with `app`, `db`, `client`, `admin_a`, `admin_b`, `auth_a`, `auth_b` fixtures.
- [ ] **T8.2** Write [`tests/test_auth.py`](qatar-backend/tests/test_auth.py) covering: signup happy + duplicate email + invalid email + short password + mismatched confirm; login success + invalid (assert exact `Invalid email or password`); remember-me cookie Max-Age ≈ 30 days; forgot-password constant 200 for known/unknown email; reset-password expiry, single-use, invalid token.
- [ ] **T8.3** Write [`tests/test_opportunities.py`](qatar-backend/tests/test_opportunities.py) covering: list scoping (A only sees A's rows); ownership isolation returns 404 on GET/PUT/DELETE for B's row from A; CRUD round-trip; invalid category → 422; empty state returns `[]`; CSRF rejection on POST/PUT/DELETE without `X-CSRFToken`.
- [ ] **T8.4** Run `pytest --cov=app --cov-fail-under=80`.

## Phase 9 — Ops & docs

- [ ] **T9.1** Add `Procfile` with `web: gunicorn run:app`.
- [ ] **T9.2** Optional `Dockerfile` (`python:3.12-slim`, install deps, run gunicorn).
- [ ] **T9.3** Write [`README.md`](qatar-backend/README.md) covering: prerequisites, env setup, `uv sync`, `flask db upgrade`, `flask run`, `pytest`, deployment notes.
- [ ] **T9.4** Add `Makefile` (or uv scripts) for `make run`, `make test`, `make migrate`, `make lint`.

## Acceptance gates

- All EARS criteria in [`specs/requirements.md`](specs/requirements.md) traced to a passing test.
- UI in [`sky/`](sky/) renders identically; only [`sky/admin.js`](sky/admin.js) is modified.
- No hardcoded opportunity data anywhere in the codebase.
- `pytest --cov` reports ≥ 80% on `app/`.

## Traceability matrix

| Story  | Tasks                  |
| ------ | ---------------------- |
| US-1.1 | T2.1, T3.1, T3.2, T5.2 |
| US-1.2 | T1.5, T3.1, T5.3       |
| US-1.3 | T2.1, T5.6, T5.7       |
| US-2.1 | T2.1, T6.2, T7.3       |
| US-2.2 | T3.3, T3.4, T6.3, T7.4 |
| US-2.3 | T2.1, T2.5, T6.2, T6.4 |
| US-2.4 | T4.1, T6.4, T7.5       |
| US-2.5 | T4.1, T6.5,            |
| US-2.6 | T4.1, T6.6, T7.7       |
