# Subly — Application Flow

End-to-end flow of how a user's media file becomes a downloadable SRT.

---

## 1. High-level architecture

```mermaid
flowchart LR
    subgraph Browser["Browser (Next.js 16)"]
        UI_Upload["/new-project<br/>drag-and-drop"]
        UI_Detail["/projects/[id]<br/>polls every 2s"]
        UI_Dash["/dashboard<br/>list view"]
    end

    subgraph API["FastAPI (backend)"]
        EP_Post["POST /api/v1/projects"]
        EP_Get["GET  /api/v1/projects/{id}"]
        EP_List["GET  /api/v1/projects"]
        EP_Srt["GET  /api/v1/projects/{id}/srt"]
    end

    subgraph Infra["Shared infra"]
        DB[("SQLite<br/>(/data volume)")]
        Redis[("Redis<br/>broker + results")]
        S3[("Amazon S3<br/>uploads/ + subtitles/")]
        Cognito{{"AWS Cognito<br/>JWT auth"}}
    end

    subgraph Worker["Celery worker"]
        Task["transcribe(project_id)"]
        Whisper["faster-whisper<br/>(model=small)"]
    end

    UI_Upload   -- "Bearer JWT + multipart file" --> EP_Post
    UI_Detail   -- "Bearer JWT, every 2s"       --> EP_Get
    UI_Dash     -- "Bearer JWT"                  --> EP_List
    UI_Detail   -- "Bearer JWT"                  --> EP_Srt

    EP_Post -.validates token.-> Cognito
    EP_Get  -.validates token.-> Cognito
    EP_List -.validates token.-> Cognito
    EP_Srt  -.validates token.-> Cognito

    EP_Post -- "put_object<br/>uploads/{pid}/file" --> S3
    EP_Post -- "INSERT project" --> DB
    EP_Post -- "send_task('transcribe')" --> Redis

    Redis --> Task
    Task -- "get_object" --> S3
    Task --> Whisper
    Whisper -- "segments" --> Task
    Task -- "UPDATE status / progress" --> DB
    Task -- "put_object<br/>subtitles/{pid}/file.srt" --> S3

    EP_Get  -- "SELECT" --> DB
    EP_List -- "SELECT WHERE user_sub" --> DB
    EP_Srt  -- "presign_get_url" --> S3
    EP_Srt  -- "URL" --> UI_Detail
    UI_Detail -- "302 to presigned URL" --> S3
```

---

## 2. Sequence — upload → transcribe → download

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Next.js
    participant API as FastAPI
    participant DB as SQLite
    participant Q as Redis (Celery)
    participant W as Celery worker
    participant WH as faster-whisper
    participant S3 as Amazon S3

    User->>FE: pick file + language, click "Upload & Process"
    FE->>API: POST /api/v1/projects (Bearer JWT, multipart)
    API->>S3: put_object uploads/{pid}/file
    API->>DB: INSERT project (status=PENDING → QUEUED, user_sub)
    API->>Q: send_task("transcribe", pid)
    API-->>FE: 201 { id, status: "QUEUED" }
    FE->>User: redirect /projects/{pid}

    par UI polling
        loop every 2 s until terminal
            FE->>API: GET /api/v1/projects/{pid}
            API->>DB: SELECT WHERE id = pid AND user_sub = me
            API-->>FE: { status, progress, error, has_srt }
        end
    and Worker pipeline
        Q->>W: deliver task(pid)
        W->>DB: UPDATE status = TRANSCRIBING
        W->>S3: download uploads/{pid}/file → /tmp
        W->>WH: model.transcribe(path, language, vad_filter)
        loop for each segment
            WH-->>W: segment (start, end, text)
            W->>W: write SRT line
            opt every +5% progress
                W->>DB: UPDATE progress
            end
        end
        W->>S3: put_object subtitles/{pid}/file.srt
        W->>DB: UPDATE srt_key, status = COMPLETED, progress = 100
    end

    Note over FE,API: Next poll sees status = COMPLETED
    FE->>User: show "Download SRT" button
    User->>FE: click Download SRT
    FE->>API: GET /api/v1/projects/{pid}/srt
    API->>S3: generate_presigned_url(get_object, ttl=15 min)
    API-->>FE: { url }
    FE->>S3: GET presigned URL
    S3-->>User: file.srt
```

---

## 3. Project status machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: row created
    PENDING --> QUEUED: task enqueued
    QUEUED --> TRANSCRIBING: worker picks up
    TRANSCRIBING --> TRANSCRIBING: progress 0→99
    TRANSCRIBING --> COMPLETED: SRT uploaded
    TRANSCRIBING --> FAILED: exception (S3, Whisper, ffmpeg…)
    QUEUED --> FAILED: task lost / worker crash
    COMPLETED --> [*]
    FAILED --> [*]
```

---

## 4. Where each piece of state lives

| State | Lives in | Notes |
|---|---|---|
| User identity (JWT) | Cognito + browser `localStorage` | Validated on every API call |
| Project rows (status, progress, keys) | SQLite at `/data/subly.db` | Shared docker volume between API and worker |
| Uploaded source media | S3 `uploads/{project_id}/<filename>` | Stored only as long as the project exists |
| Generated SRT | S3 `subtitles/{project_id}/<stem>.srt` | Served via 15-min presigned URL |
| Task queue + results | Redis `redis://redis:6379/0` and `…/1` | Celery broker + result backend |
| Whisper model weights | Docker volume `subly-whisper-cache` | Downloaded once on first transcription |
