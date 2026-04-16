from fastapi import FastAPI

from dotenv import load_dotenv

load_dotenv()

from app.routers.generate import router as generate_router
from app.routers.review import router as review_router
from app.routers.rewrite import router as rewrite_router
from app.routers.read_run import router as read_run_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Persona-Driven Agentic Content Generator",
        version="0.1.0",
        description=(
            "Stateless FastAPI backend implementing a run-scoped agent workflow: "
            "generate → review → rewrite (repeat).\n\n"
            "State is persisted per run as JSON files under `db/` with file locks and atomic writes.\n\n"
            "Personas supported: `bbc`, `taylor_swift`."
        ),
        openapi_tags=[
            {"name": "generate", "description": "Create a new run and generate version 1."},
            {"name": "review", "description": "Review the latest version and attach a review artifact."},
            {"name": "rewrite", "description": "Rewrite based on selected reviewer feedback and append a new version."},
        ],
    )

    app.include_router(generate_router)
    app.include_router(review_router)
    app.include_router(rewrite_router)
    app.include_router(read_run_router)

    @app.get("/")
    def root() -> dict:
        return {
            "message": "API is running. Visit /docs for interactive documentation.",
            "health": "/health",
            "docs": "/docs",
        }

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
