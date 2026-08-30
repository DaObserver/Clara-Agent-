# Clara — AI Healthcare Navigation Agent

Clara is an AI healthcare navigation agent that helps people understand medical paperwork, organize next steps, track care tasks, and maintain a persistent post-visit care plan.

Clara is designed to explain and organize documented medical information — not diagnose conditions or replace a healthcare professional.

## Live Links

- **Live App:** https://clara-agent-2026.web.app/
- **GitHub Repository:** https://github.com/DaObserver/Clara-Agent-
- **Cloud Run Backend:** https://clara-backend-600669891269.us-east1.run.app/
- **Demo Video:** https://youtube.com/shorts/igIV08SaBkw

## Why Clara Exists

After a medical visit, patients may receive multiple documents containing:

- discharge instructions
- medication directions
- follow-up appointments
- lab orders
- restrictions
- recovery instructions
- provider notes

That information can be difficult to understand and easy to forget.

Clara turns those documents into one clear, actionable care experience.

## Core Capabilities

- Multi-document medical review
- Plain-English medical explanations
- Persistent My Plan
- Medication organization
- Pending task tracking
- Task completion updates
- Firestore persistence across sessions
- Cloud-hosted backend
- Permanently hosted frontend

## Architecture

![Clara Architecture](assets/clara-architecture.png)

### High-Level Flow

```text
User
  ↓
Firebase Hosting
  ↓
React + Vite Frontend
  ↓
Google Cloud Run
  ↓
FastAPI Backend
  ↓
Google Agent Development Kit (ADK)
  ↓
Gemini via Vertex AI
  ↓
Google Cloud Firestore
```

## Google Technologies Used

- **Google Agent Development Kit (ADK)** — agent orchestration and tool use
- **Gemini via Vertex AI** — reasoning and multi-document understanding
- **Google Cloud Firestore** — persistent care-plan state
- **Google Cloud Run** — deployed FastAPI backend
- **Firebase Hosting** — deployed React frontend
- **Google Cloud IAM / Service Accounts** — secure service-to-service authentication

## Project Structure

```text
Clara-Agent-
├── clara/                  # Backend + ADK agent
│   └── README.md           # Backend technical documentation
├── frontend/               # React/Vite frontend
│   └── README.md           # Frontend technical documentation
├── assets/
│   └── clara-architecture.png
└── README.md               # Project landing page
```

## Documentation

- [Backend / Clara Agent](clara/README.md)
- [Frontend](frontend/README.md)

## Quick Start

### Backend

```bash
cd clara
uv sync
uv run python app/fast_api_app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

### Required Environment Variables

```text
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=clara-agent-2026
GOOGLE_CLOUD_LOCATION=global
```

For local development, configure Google Cloud authentication using an authorized service account or Application Default Credentials.

Do not commit credentials, service-account keys, `.env` files, or other secrets to the repository.

## How Clara Works

1. The user uploads one or more medical documents.
2. The React frontend sends the documents to the FastAPI backend.
3. Google ADK coordinates Clara's agent workflow and tool use.
4. Gemini through Vertex AI reviews and organizes the medical information.
5. Clara creates a structured care plan containing documented medications, follow-ups, and pending tasks.
6. The care plan is stored in Firestore.
7. Users can return later, retrieve their saved plan, and update task status without re-uploading the original documents.

## Persistent Care Plan

Clara uses Google Cloud Firestore to preserve structured care-plan information across sessions.

This allows Clara to:

- remember saved follow-up tasks
- maintain completed and pending task status
- retrieve medication information
- restore the user's care plan after a page refresh or new session

The interface itself may reset when refreshed, but the saved care-plan state remains available in Firestore and can be retrieved again by Clara.

## Safety

Clara is an AI healthcare navigation assistant, not a doctor.

Clara does not:

- diagnose medical conditions
- prescribe medications
- replace a healthcare professional
- invent medical instructions
- guess undocumented medication details

Clara is designed to explain and organize information already documented by a patient's healthcare team.

## Current Prototype

The current Clara prototype supports:

- multiple PDF and image uploads
- combined document review
- structured My Plan creation
- medication-specific retrieval
- pending-task filtering
- task completion tracking
- persistent Firestore state
- Cloud Run backend deployment
- Firebase-hosted frontend

## Deployment

### Frontend

The production frontend is deployed with Firebase Hosting:

https://clara-agent-2026.web.app/

### Backend

The production FastAPI backend is deployed to Google Cloud Run:

https://clara-backend-600669891269.us-east1.run.app/

### Persistent Storage

Care-plan state is stored in Google Cloud Firestore.

## Built For

Google AI Agent Hackathon — 2026
