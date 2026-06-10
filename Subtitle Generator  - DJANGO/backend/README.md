# Subly — Backend

Django + DRF backend, protected by AWS Cognito-issued JWTs.

- **Project:** `mywebsite`
- **App:** `myapp`

## Run

### With Docker (recommended)

From the project root:

```bash
docker compose up --build
```

See the [root README](../README.md) for the full Cognito setup.

### Locally (without Docker)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

You'll need Cognito env vars exported (`AWS_REGION`, `COGNITO_USER_POOL_ID`,
`COGNITO_APP_CLIENT_ID`, `COGNITO_APP_CLIENT_SECRET`) and IAM credentials
available either via `aws configure` or `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY`.

Server: `http://127.0.0.1:8000` · Swagger UI: `/docs`

## Endpoints

| Method | Path             | Auth          | Description                                |
| ------ | ---------------- | ------------- | ------------------------------------------ |
| GET    | `/health`        | Public        | Health check.                              |
| POST   | `/auth/register` | Public        | Create a Cognito user.                     |
| POST   | `/auth/login`    | Public        | Exchange credentials for Cognito tokens.   |
| POST   | `/auth/logout`   | Public        | Revoke a Cognito refresh token.            |
| GET    | `/auth/me`       | Bearer token  | Returns the current user's profile.        |
| GET    | `/api/v1/hello`  | Public        | Smoke-test endpoint.                       |
| GET    | `/api/me`        | Bearer token  | Legacy alias for `/auth/me`.               |

Call `/auth/me` with the access token from the frontend (or any client):

```bash
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/auth/me
```

## Environment variables

| Variable                       | Default                  | Purpose                                                       |
| ------------------------------ | ------------------------ | ------------------------------------------------------------- |
| `AWS_REGION`                   | `eu-west-2`              | AWS region of the User Pool.                                  |
| `COGNITO_USER_POOL_ID`         | _empty_                  | User Pool id, e.g. `eu-west-2_abc12345`.                      |
| `COGNITO_APP_CLIENT_ID`        | _empty_                  | App client id used for login + register.                      |
| `COGNITO_APP_CLIENT_SECRET`    | _empty_                  | App client secret (required if the client has one).           |
| `COGNITO_AUTH_FLOW`            | `USER_PASSWORD_AUTH`     | Auth flow used by `InitiateAuth`.                             |
| `COGNITO_TOKEN_USE`            | `access`                 | Expected `token_use` claim — `access` or `id`.                |
| `COGNITO_GROUPS_CLAIM`         | `cognito:groups`         | Claim name to map into `roles`.                               |
| `COGNITO_AUTO_CONFIRM_SIGN_UP` | `false`                  | Auto-confirm new users (admin call).                          |
| `COGNITO_ISSUER_OVERRIDE`      | _empty_                  | Override the expected `iss` claim.                            |
| `COGNITO_JWKS_URL_OVERRIDE`    | _empty_                  | Override the JWKS URL.                                        |
| `CORS_ORIGINS`                 | `http://localhost:3000`  | Comma-separated list of allowed origins.                      |
| `DJANGO_SECRET_KEY`            | dev fallback             | Override for production.                                      |
| `DJANGO_DEBUG`                 | `true`                   | Set to `false` in production.                                 |

## Project layout

```
.
├── Dockerfile
├── main.py                  # local entry point
├── manage.py
├── requirements.txt
├── mywebsite/
│   ├── settings.py          # DRF + Cognito config
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── myapp/
    ├── apps.py
    ├── auth.py              # CognitoAuthentication (JWT validation) + CognitoClient
    ├── urls.py
    ├── views.py
    └── schemas.py
```

## How auth works

`myapp/auth.py` provides `CognitoAuthentication`, a DRF
`BaseAuthentication` subclass that:

1. Reads the `Authorization: Bearer <token>` header.
2. Fetches Cognito's JWKS
   (`https://cognito-idp.<region>.amazonaws.com/<user-pool-id>/.well-known/jwks.json`)
   and caches the keys in process for 1 hour.
3. Verifies the JWT's signature, `iss`, `token_use`, and app client id.
4. Enriches the claims by calling Cognito `GetUser` with the access token.
5. Attaches a lightweight `CognitoUser` to `request.user` exposing
   `sub`, `username`, `email`, `name`, `roles`, and the raw `claims` dict.

It's wired up as the DRF default authentication class in `settings.py`, so
**every endpoint requires a valid token by default**. Use
`@authentication_classes([]) + @permission_classes([AllowAny])` to opt out
(see `hello_world` in `views.py`).

## Adding a new endpoint

1. Define the serializer in `myapp/schemas.py`.
2. Add the view function in `myapp/views.py` decorated with `@extend_schema(...)`.
3. Wire the route in `myapp/urls.py` (or `mywebsite/urls.py` for top-level paths).
