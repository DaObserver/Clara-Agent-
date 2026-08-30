# Clara — AI Healthcare Navigation Agent

Clara is an AI healthcare navigation agent that helps people understand medical paperwork, organize next steps, track care tasks, and maintain a persistent post-visit care plan.

Clara is designed to explain and organize documented medical information — not diagnose conditions or replace a healthcare professional.

## Live Links

- **Live App:** https://clara-agent-2026.web.app/
- **GitHub Repository:** https://github.com/DaObserver/Clara-Agent-
- **Cloud Run Backend:** https://clara-backend-600669891269.us-east1.run.app/
- **Demo Video:** ADD_YOUTUBE_OR_VIMEO_LINK_HERE

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
