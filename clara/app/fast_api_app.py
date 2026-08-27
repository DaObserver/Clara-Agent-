# ruff: noqa

import base64
import sys
import uuid
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent import app as clara_app

app = FastAPI(
    title="Clara",
    description="API for Clara AI Healthcare Navigation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_ID = "demo-user"
session_service = InMemorySessionService()
runner = Runner(app=clara_app, session_service=session_service)


class ClaraDocument(BaseModel):
    file_name: str
    mime_type: str
    file_base64: str


class ClaraReviewRequest(BaseModel):
    documents: list[ClaraDocument]
    prompt: str


class ClaraMessageRequest(BaseModel):
    session_id: str
    message: str


class ClaraQueryRequest(BaseModel):
    message: str


async def run_clara(session_id: str, message: types.Content) -> str:
    final_text = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        if not event.content or not event.content.parts:
            continue

        try:
            is_final = event.is_final_response()
        except Exception:
            is_final = False

        text_parts = [
            part.text
            for part in event.content.parts
            if getattr(part, "text", None)
        ]

        if text_parts:
            text = "\n".join(text_parts)
            if is_final:
                final_text = text
            elif not final_text:
                final_text += text + "\n"

    return final_text.strip()


async def create_clara_session() -> str:
    session_id = f"clara-{uuid.uuid4().hex}"
    session = await session_service.create_session(
        app_name=clara_app.name,
        user_id=USER_ID,
        session_id=session_id,
    )
    return session.id


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/clara/review")
async def clara_review(request: ClaraReviewRequest):
    if not request.documents:
        raise HTTPException(status_code=400, detail="Upload at least one medical document.")

    if len(request.documents) > 10:
        raise HTTPException(
            status_code=400,
            detail="Clara currently supports up to 10 documents at a time.",
        )

    session_id = await create_clara_session()

    parts = [
        types.Part.from_text(
            text=(
                f"{request.prompt}\n\n"
                f"You are reviewing {len(request.documents)} document(s) together. "
                "Treat them as one care episode. Reconcile overlapping information, "
                "avoid duplicate tasks, and do not invent information that is not documented."
            )
        )
    ]

    for index, document in enumerate(request.documents, start=1):
        try:
            file_bytes = base64.b64decode(document.file_base64, validate=True)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not decode {document.file_name}.",
            ) from exc

        parts.append(
            types.Part.from_text(text=f"Document {index}: {document.file_name}")
        )
        parts.append(
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=document.mime_type or "application/octet-stream",
            )
        )

    message = types.Content(role="user", parts=parts)

    try:
        response_text = await run_clara(session_id=session_id, message=message)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Clara could not review the documents: {exc}",
        ) from exc

    return {
        "success": True,
        "session_id": session_id,
        "document_count": len(request.documents),
        "file_names": [document.file_name for document in request.documents],
        "response": response_text,
    }


@app.post("/clara/message")
async def clara_message(request: ClaraMessageRequest):
    session = await session_service.get_session(
        app_name=clara_app.name,
        user_id=USER_ID,
        session_id=request.session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="That Clara session was not found. Review the documents again.",
        )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=request.message)],
    )

    try:
        response_text = await run_clara(
            session_id=request.session_id,
            message=message,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Clara could not continue the session: {exc}",
        ) from exc

    return {
        "success": True,
        "session_id": request.session_id,
        "response": response_text,
    }


@app.post("/clara/query")
async def clara_query(request: ClaraQueryRequest):
    session_id = await create_clara_session()

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=request.message)],
    )

    try:
        response_text = await run_clara(session_id=session_id, message=message)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Clara could not answer the request: {exc}",
        ) from exc

    return {
        "success": True,
        "session_id": session_id,
        "response": response_text,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.fast_api_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
