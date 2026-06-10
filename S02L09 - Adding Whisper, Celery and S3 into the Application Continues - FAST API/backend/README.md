# StudyEasy Application — Backend Starter

A layered backend starter. Add a **controller** (route), a **service** (business logic), a **schema** (request/response DTO), and — if persistence is needed — a **model**.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Server: `http://127.0.0.1:8000` · Swagger UI: `/docs`

The sample endpoint is at `GET /api/v1/hello`.

## Project layout

```
.
├── main.py                          # entry point
├── requirements.txt
└── app/
    ├── main.py                      # app factory, mounts the api router
    ├── config.py                    # Pydantic settings (env-driven)
    ├── api/
    │   └── router.py                # aggregates all controllers under /api/v1
    ├── controllers/                 # HTTP layer — route handlers, depends on services
    │   └── hello_controller.py
    ├── services/                    # business logic — pure Python
    │   └── hello_service.py
    ├── schemas/                     # DTOs for request/response
    │   └── hello_schema.py
    └── models/                      # ORM/domain models live here
```

## Conventions

- **controllers/** — thin. Parse input, call a service, return a schema. No business logic.
- **services/** — all business rules, orchestration, and I/O. Framework-agnostic.
- **schemas/** — DTOs that define the API contract. One file per resource.
- **models/** — database / domain entities. Keep separate from schemas so the wire format can evolve independently of storage.
- **api/router.py** — the single place where controllers are registered. Add new controllers here.
- **config.py** — all configuration via `pydantic-settings`. Read from environment / `.env`.

## Adding a new endpoint

1. Define the DTO in `app/schemas/<resource>_schema.py`
2. Implement the logic in `app/services/<resource>_service.py`
3. Wire the route in `app/controllers/<resource>_controller.py`
4. Register the controller's router in `app/api/router.py`
