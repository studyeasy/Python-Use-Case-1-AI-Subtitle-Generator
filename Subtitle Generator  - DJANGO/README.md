# Subly (Django) — AWS Cognito-fronted full-stack starter

A Django + DRF backend, a Next.js frontend, and AWS Cognito as the identity
provider. **The frontend never talks to Cognito directly** — it only calls the
Django backend, which brokers everything to Cognito.

```
┌──────────────┐  email + password  ┌──────────────┐  cognito-idp + JWKS ┌──────────────┐
│  Next.js     │ ─────────────────▶ │  Django/DRF  │ ──────────────────▶ │  AWS Cognito │
│  (3000)      │ ◀───── tokens ──── │  (8000)      │ ◀──── tokens ────── │  User Pool   │
└──────┬───────┘                    └──────────────┘                     └──────────────┘
       │ Authorization: Bearer <access_token>
       ▼
   Subsequent requests to /auth/me and the rest of the API.
```

## Folder layout

| Folder              | What it is                                                       |
|---------------------|------------------------------------------------------------------|
| `backend/`          | Django + DRF app + `Dockerfile`. Brokers all Cognito calls.      |
| `frontend/`         | Next.js app — no Cognito client, only backend calls.             |
| `docker-compose.yml`| Runs backend + frontend. Cognito is hosted in AWS.               |

---

## Configure Cognito

Create a Cognito User Pool and a confidential app client for this backend. The
app client must have a client secret and allow `USER_PASSWORD_AUTH` because the
app uses its own React login form and the backend calls Cognito with the
submitted credentials.

Required values:

```
AWS_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxxxx
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The backend needs IAM credentials to call Cognito. Either run `aws configure`
on the host, or pass `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` to docker
compose via environment variables.

---

## Quick start

```bash
docker compose up --build
```

Then open:

- Web app: <http://localhost:3000>
- Swagger UI: <http://localhost:8000/docs>
- Backend health: <http://localhost:8000/health>

---

## Backend API (Django + DRF)

| Method | Path             | Auth      | Body                                                | Returns                                              |
|--------|------------------|-----------|-----------------------------------------------------|------------------------------------------------------|
| GET    | `/health`        | none      | —                                                   | `{"status":"ok"}`                                    |
| POST   | `/auth/register` | none      | `{"email","password","first_name?","last_name?"}`   | `{"ok":true,"message","confirmed"}`                  |
| POST   | `/auth/login`    | none      | `{"email","password"}`                              | Cognito token bundle                                 |
| POST   | `/auth/logout`   | none      | `{"refresh_token"}`                                 | `{"ok":true}`                                        |
| GET    | `/auth/me`       | **Bearer**| —                                                   | Current Cognito user profile                         |
| GET    | `/api/v1/hello`  | none      | —                                                   | Sample hello-world payload                           |
| GET    | `/api/me`        | **Bearer**| —                                                   | Legacy alias for `/auth/me`                          |

Bearer-protected requests must include:

```
Authorization: Bearer <access_token>
```

### How it works

- **Login**: `myapp/auth.py:CognitoClient.login` calls Cognito's `InitiateAuth`
  API with `USER_PASSWORD_AUTH`, attaching a `SECRET_HASH` when the app client
  has a client secret.
- **Register**: the same client calls Cognito `SignUp`. If
  `COGNITO_AUTO_CONFIRM_SIGN_UP=true` the backend then calls
  `AdminConfirmSignUp` + `AdminUpdateUserAttributes` so the user can log in
  immediately.
- **Logout**: posts the refresh token to Cognito's `RevokeToken` endpoint.
- **JWT validation**: `CognitoAuthentication` (DRF auth class) caches the
  JWKS for 1 hour, refreshes on key rotation, verifies signature, `iss`,
  `token_use`, and the app client id before trusting a token.

The backend validates Cognito access tokens against:

```
https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json
```

---

## Environment variables

### Backend

| Var                              | Default                  | Purpose                                                       |
|----------------------------------|--------------------------|---------------------------------------------------------------|
| `DJANGO_DEBUG`                   | `false`                  | Django debug mode.                                            |
| `DJANGO_SECRET_KEY`              | dev fallback             | Django secret. **Override in production.**                    |
| `AWS_REGION`                     | `eu-west-2`              | AWS region of the User Pool.                                  |
| `AWS_ACCESS_KEY_ID`              | _empty_                  | IAM credentials for the cognito-idp client (optional).        |
| `AWS_SECRET_ACCESS_KEY`          | _empty_                  | Pair to the access key.                                       |
| `COGNITO_USER_POOL_ID`           | _empty_                  | User Pool id, e.g. `eu-west-2_abc12345`.                      |
| `COGNITO_APP_CLIENT_ID`          | _empty_                  | App client id used for login + register.                      |
| `COGNITO_APP_CLIENT_SECRET`      | _empty_                  | App client secret (required if the client has one).           |
| `COGNITO_AUTH_FLOW`              | `USER_PASSWORD_AUTH`     | Auth flow used by `InitiateAuth`.                             |
| `COGNITO_TOKEN_USE`              | `access`                 | Expected `token_use` claim — `access` or `id`.                |
| `COGNITO_GROUPS_CLAIM`           | `cognito:groups`         | Claim name to map into `roles`.                               |
| `COGNITO_AUTO_CONFIRM_SIGN_UP`   | `false`                  | Auto-confirm new users (admin call).                          |
| `COGNITO_ISSUER_OVERRIDE`        | _empty_                  | Override the expected `iss` claim.                            |
| `COGNITO_JWKS_URL_OVERRIDE`      | _empty_                  | Override the JWKS URL.                                        |
| `CORS_ORIGINS`                   | `http://localhost:3000`  | Comma-separated CORS allowlist.                               |

### Frontend (`frontend/.env.local`)

| Var                   | Default                  | Purpose                          |
|-----------------------|--------------------------|----------------------------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`  | Django backend base URL.         |

There are **no** Cognito env vars on the frontend by design.

---

## Running locally without Docker

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Make sure your Cognito env vars are exported and `aws configure` has been run.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Docker commands

| Command                                  | What it does                                |
|------------------------------------------|---------------------------------------------|
| `docker compose up --build`              | Build images and start backend + frontend.  |
| `docker compose up --build -d`           | Same, but detached.                         |
| `docker compose logs -f backend`         | Follow backend logs.                        |
| `docker compose restart backend`         | Restart only the backend.                   |
| `docker compose down`                    | Stop and remove containers.                 |

---

## Smoke test (curl)

```bash
curl http://localhost:8000/health

curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","password":"Passw0rd!","first_name":"New","last_name":"User"}'

curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","password":"Passw0rd!"}'

TOKEN="..."
curl http://localhost:8000/auth/me -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"...\"}"
```

---

## Troubleshooting

**`503 Could not fetch Cognito JWKS`**
The backend container can't reach `cognito-idp.<region>.amazonaws.com`. Check
network egress and `AWS_REGION` / `COGNITO_USER_POOL_ID`.

**`401 Invalid Cognito app client`**
Token was issued for a different app client. Make sure `COGNITO_APP_CLIENT_ID`
matches the client that issued the token.

**`403 User is not confirmed`**
The Cognito user pool requires confirmation. Either confirm the user manually
in the AWS console, set `COGNITO_AUTO_CONFIRM_SIGN_UP=true`, or implement a
confirmation flow.

**`409` from `/auth/register`**
A user with that email already exists in the User Pool.

**Browser CORS error**
Add the origin to `CORS_ORIGINS` (comma-separated) and restart.

**Port 8000 / 3000 already in use**
Stop whatever's listening, or change the host port mapping in
`docker-compose.yml`.

---

## Limitations / known warnings

- **No token refresh** — Cognito access tokens are short-lived and the
  frontend doesn't auto-refresh. Adding a `/auth/refresh` route is a small
  follow-up.
- **`localStorage` storage** — tokens are XSS-vulnerable; for production
  move the refresh token into an HttpOnly cookie minted by the backend.
- **App client secret in env** — pass it via your deployment's secret store,
  not committed config.
