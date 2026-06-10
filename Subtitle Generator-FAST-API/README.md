# Subly - AWS Cognito full-stack starter

FastAPI backend, Next.js frontend, and AWS Cognito as the identity provider.
The frontend never talks to Cognito directly. It calls the backend auth APIs,
and the backend brokers Cognito registration, login, logout, and JWT validation.

```text
Next.js (3000) -> FastAPI (8000) -> AWS Cognito User Pool
       subsequent API calls use Authorization: Bearer <access_token>
```

## Project layout

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI app and Dockerfile. Brokers all Cognito calls. |
| `Frontend/` | Next.js app. Custom login/signup UI, backend API only. |
| `docker-compose.yml` | Runs backend and frontend. Cognito is hosted in AWS. |
| `sample.env` | Template for your local `.env` values. |
| `QUICK_START.md` | Short student guide for the minimum Cognito setup. |

For the shortest student setup, start with [QUICK_START.md](QUICK_START.md).

## Configure Cognito

Create a Cognito User Pool and a confidential app client for this backend. The
app client must have a client secret and allow `USER_PASSWORD_AUTH` because the
app uses its own React login form and the backend calls Cognito with the
submitted credentials.

Copy the environment template:

```bash
cp sample.env .env
```

Fill in:

```env
AWS_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxxxx
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Those are the only `.env` values needed for the starter app.

## Run with Docker

```bash
docker compose up --build
```

Services:

| Service | URL |
| --- | --- |
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |

## Run locally

Backend:

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Frontend:

```bash
cd Frontend
npm install
npm run dev
```

## Auth API

| Method | Path | Auth | Body | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/auth/register` | none | `{"email","password","first_name?","last_name?"}` | `{"ok":true,"message","confirmed"}` |
| `POST` | `/auth/login` | none | `{"email","password"}` | Cognito token bundle |
| `POST` | `/auth/logout` | none | `{"refresh_token"}` | `{"ok":true}` |
| `GET` | `/auth/me` | Bearer | none | Current Cognito user profile |
| `GET` | `/api/me` | Bearer | none | Legacy alias for `/auth/me` |

The backend validates Cognito access tokens using the User Pool JWKS:

```text
https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json
```

It checks `iss`, `token_use`, and the app client id before trusting a token.

## Cognito notes

- User pool issuer defaults to
  `https://cognito-idp.${AWS_REGION}.amazonaws.com/${COGNITO_USER_POOL_ID}`.
- Groups are read from the `cognito:groups` claim and returned as `roles`.
- `/auth/logout` revokes the refresh token using Cognito `RevokeToken`.
- `/auth/me` validates the access token, then calls Cognito `GetUser` to enrich
  the response with attributes such as email and names.
