# FastAPI is the main class used to create your web application.
from fastapi import FastAPI, Request

# JSONResponse is used to send back responses in JSON format, which is what web frontends expect.
from fastapi.responses import JSONResponse, HTMLResponse

# StaticFiles allows your server to provide files like CSS and JavaScript directly.
from fastapi.staticfiles import StaticFiles

# Jinja2Templates is used to render HTML files, allowing you to pass data from Python to the HTML.
from fastapi.templating import Jinja2Templates

# CORSMiddleware is crucial for allowing your frontend (running in a browser)
# to make API calls to your backend, even if they are on different ports.
from fastapi.middleware.cors import CORSMiddleware

# --- Standard Python Imports ---

# The 'pathlib' library helps create file paths that work correctly on any operating system (Windows, Mac, Linux).
import asyncio
from pathlib import Path
# --- Your Application's Imports ---

# It will contain the core RAG logic.
# Prefer package-relative imports; only fall back to absolute package imports when
# this module is loaded outside the package context. Do not mask missing third-party
# deps (e.g., 'dotenv') with a broad ImportError handler.
try:
    from .model import generate_answer, warmup_models
    from .database import save_query_answer
except ModuleNotFoundError as e:
    if e.name in {"app", "backend", "app.backend"}:
        from app.backend.model import generate_answer, warmup_models
        from app.backend.database import save_query_answer
    else:
        raise

#Application setup

# This line creates the main application instance. 'app' is the conventional name.
app= FastAPI()


@app.on_event("startup")
async def _startup_warmup() -> None:
    # Warm up heavy models in the background (don't block server start)
    asyncio.create_task(asyncio.to_thread(warmup_models))

# This adds the CORS middleware to your application.
# Without this, your browser would block JavaScript requests from the frontend to the backend for security reasons.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows requests from any origin. Good for development, but you'd restrict this in production.
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, etc.).
    allow_headers=["*"], # Allows all HTTP headers.
)

# --- 2. Path and Directory Configuration ---

# Repo layout:
# app/
#   backend/app.py   (this file)
#   frontend/static/
#   frontend/templates/
_app_root = Path(__file__).resolve().parents[1]

_frontend_dir = _app_root / "frontend"
_static_dir = _frontend_dir / "static"
_templates_dir = _frontend_dir / "templates"

templates: Jinja2Templates | None = None
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
if _templates_dir.exists():
    templates = Jinja2Templates(directory=str(_templates_dir))


# --- 3. API Routes (Endpoints) ---

# This is a "route decorator". It tells FastAPI that the function below
# should handle GET requests to the root URL ("/").
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    """Serves the main index.html page (if present), otherwise a small health page."""
    if templates is not None:
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse("<h3>QA Backend is running</h3><p>POST /ask</p>")


# This decorator tells FastAPI to handle POST requests to the "/ask" URL.
# This is the main endpoint your frontend will call.
@app.post("/ask")
async def ask_question(request: Request):
    """
    Receives a question and video URL, generates an answer,
    logs it to the database, and returns the answer.
    """

    try:
        # The 'await request.json()' line reads the body of the POST request
        # and parses it as JSON into a Python dictionary.
        data = await request.json()
        video_url = data.get("video_url")
        question = data.get("question")
        

        # --- This is the core orchestration step ---
        # 1. Call the RAG model to get an answer.
        answer = generate_answer(video_url, question)

        # 2. Call your database function to save the interaction.
        save_query_answer(video_url=video_url, question=question, answer=answer)

        # Prepare a successful response
        response_data = {"answer": answer}

    except Exception as e:
        # If any part of the 'try' block fails, this code runs.
        # It's important for error handling.
        print(f"An error occurred in /ask endpoint: {e}")
        # We send back a clear error message to the frontend in the same JSON format.
        response_data = {"answer": f"An error occurred: {e}"}

    # Finally, return the result (either the answer or the error) as a JSON response.
    return JSONResponse(content=response_data)
