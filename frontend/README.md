# Clara Frontend — React + Vite + Firebase Hosting

This directory contains the Clara web interface.

The frontend provides a clean healthcare-navigation experience for uploading medical documents, reviewing Clara's explanations, viewing the saved care plan, checking medications, tracking pending tasks, and marking tasks complete.

## Main Technologies

- **React** — user interface
- **Vite** — frontend build system
- **Firebase Hosting** — permanent web hosting
- **Cloud Run API** — production Clara backend

## Main Files

```text
frontend/
├── src/
│   ├── App.jsx
│   ├── App.css
│   ├── index.css
│   └── main.jsx
├── public/
├── firebase.json
├── .firebaserc
├── vite.config.js
├── package.json
└── README.md
```

## User Experience

The frontend supports:

### Multi-Document Upload

Users can:

- select multiple PDFs or images
- add additional documents
- remove individual documents before review
- submit all selected files as one care episode

### Clara Review

The frontend sends the uploaded documents to the Cloud Run backend and displays Clara's combined plain-English review.

### My Plan

Users can retrieve their saved care plan from Firestore through the Clara backend.

### Medications

The medications view requests only the medication information saved in the care plan.

### Pending Tasks

The pending tasks view shows only unfinished care tasks.

### Mark Complete

Users can type the name of a completed task and ask Clara to update the saved task status.

The updated pending-task list is then retrieved again.

### Persistent Experience

The frontend does not rely only on React state for care-plan persistence.

Persistent care-plan data is retrieved from Firestore through the Cloud Run backend, allowing the user's saved care state to survive browser refreshes and new sessions.

## Production API

The production frontend calls the Clara backend hosted on Google Cloud Run:

```text
https://clara-backend-600669891269.us-east1.run.app
```

The main API routes used by the frontend are:

```text
POST /clara/review
POST /clara/message
POST /clara/query
```

## Local Development

Install dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev -- --host 0.0.0.0
```

The development frontend normally runs on:

```text
http://localhost:5173
```

## Production Build

Build the frontend with:

```bash
npm run build
```

Vite creates the production files in:

```text
dist/
```

## Firebase Hosting

Firebase Hosting serves the production React application from the `dist` directory.

Initialize Hosting with:

```bash
firebase init hosting
```

Production deployment:

```bash
firebase deploy --only hosting
```

The Firebase-hosted frontend remains available independently of the Codespaces development server.

## Safety Presentation

The frontend visibly communicates Clara's safety boundary:

> Designed to explain — not diagnose.

The interface reinforces that Clara:

- does not diagnose conditions
- does not prescribe medication
- does not replace healthcare professionals

## Relationship to the Backend

```text
Firebase Hosting
      ↓
React + Vite
      ↓
Cloud Run
      ↓
FastAPI
      ↓
Google ADK
      ↓
Vertex AI / Gemini
      ↓
Firestore
```

The frontend is intentionally separated from the backend so the user interface can remain lightweight while agent reasoning, tool execution, authentication, and persistent storage remain in the cloud backend.
