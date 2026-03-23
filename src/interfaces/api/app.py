"""FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Загрузка индекса при старте приложения"""
    store = get_vector_store()
    await store.load()
    chunks_count = len(store._chunks) if hasattr(store, "_chunks") else 0
    print(f"Vector store loaded: {chunks_count} chunks")
    yield


from .routers import chat_router, documents_router, health_router

app = FastAPI(
    title="RAG Document Search API",
    description="API для поиска информации в документах через RAG",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat_router.router)
app.include_router(documents_router.router)
app.include_router(health_router.router)


@app.get("/")
async def root():
    return {"message": "RAG Document Search API", "docs": "/docs"}
