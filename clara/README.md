# Clara Backend — Google ADK + FastAPI + Vertex AI + Firestore

This directory contains Clara's backend agent system.

Clara is an AI healthcare navigation agent that reviews medical paperwork, explains documented information in plain English, creates a structured care plan, and maintains persistent care-plan state across sessions.

## Backend Responsibilities

The backend is responsible for:

- receiving medical documents from the frontend
- sending documents to Clara for combined review
- orchestrating agent behavior with Google ADK
- using Gemini through Vertex AI for reasoning and document understanding
- creating and retrieving saved care plans
- storing persistent care-plan state in Firestore
- updating task completion status
- exposing the Clara API through FastAPI

## Main Technologies

- **Google Agent Development Kit (ADK)** — agent orchestration, sessions, tool use
- **Gemini via Vertex AI** — reasoning and document understanding
- **Google Cloud Firestore** — persistent care-plan storage
- **FastAPI** — backend HTTP API
- **Google Cloud Run** — production backend hosting
- **Google Cloud IAM / Service Accounts** — cloud authentication and permissions
- **uv** — Python dependency management

## Main Files

```text
clara/
├── app/
│   ├── agent.py
│   ├── fast_api_app.py
│   └── app_utils/
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

### `app/agent.py`

Defines Clara's ADK agent, instructions, tools, Firestore access, and care-plan behavior.

### `app/fast_api_app.py`

Exposes Clara through FastAPI and connects HTTP requests to the ADK runner.

## API Endpoints

### `GET /health`

Health check for the deployed backend.

Example response:

```json
{
  "status": "ok"
}
```

### `POST /clara/review`

Accepts one or more medical documents and asks Clara to review them together as one care episode.

The request includes:

- file name
- MIME type
- base64 file data
- review prompt

Clara is instructed to reconcile overlapping information and avoid duplicate tasks.

### `POST /clara/message`

Continues an existing Clara session.

This is used for actions such as:

```text
Save My Plan
```

### `POST /clara/query`

Creates a fresh agent session for persistent care-plan actions such as:

- View My Plan
- View Medications
- View Pending Tasks
- Mark a task complete

Because the care plan is stored in Firestore, these requests can retrieve updated state even after the frontend session changes.

## Persistent State

Clara uses Google Cloud Firestore as its durable care-plan storage.

This allows Clara to:

1. save a care plan
2. retrieve it in a later session
3. update task status
4. preserve completed and pending state
5. return the updated plan after a browser refresh or new agent session

This persistent state is one of the key differences between Clara and a one-time document summarizer.

## Multi-Document Review

The backend accepts multiple documents in a single review request.

Clara receives the documents together and is instructed to:

- treat them as one care episode
- reconcile overlapping instructions
- avoid duplicate tasks
- create one combined care plan
- use only documented information

## Safety Design

Clara is designed to explain and organize documented information.

The agent is instructed not to:

- diagnose
- prescribe
- invent missing medical instructions
- guess medication doses or timing
- replace professional medical care

## Authentication and Cloud Access

Local development may use environment variables for authentication.

Sensitive credentials must not be committed.

Ignored files include:

```text
.env
clara-service-account.json
```

The production Cloud Run deployment uses Google Cloud service identity and IAM roles rather than shipping a service-account key with the application.

Cloud Run uses environment variables such as:

```text
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=clara-agent-2026
GOOGLE_CLOUD_LOCATION=global
```

## Local Development

From the backend directory:

```bash
uv sync
uv run python app/fast_api_app.py
```

The local backend defaults to:

```text
http://localhost:8000
```

## Cloud Deployment

The production backend is deployed to Google Cloud Run.

The application reads the Cloud Run `PORT` environment variable when deployed and falls back to port `8000` for local development.

## Agentic Behavior

Clara is more than a text-generation interface.

The agent:

- interprets user intent
- reviews multiple documents
- uses tools
- retrieves persistent state
- updates Firestore records
- tracks completion status
- generates responses based on current saved state

That tool use and persistent state allow Clara to support an ongoing healthcare navigation workflow rather than a single isolated response.
