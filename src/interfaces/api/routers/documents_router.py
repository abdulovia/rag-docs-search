"""Documents Router — endpoints для управления документами"""

import shutil
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ....application.use_cases.index_documents import IndexDocumentsUseCase
from ..dependencies import get_index_use_case, get_vector_store

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    use_case: IndexDocumentsUseCase = Depends(get_index_use_case),
):
    """Загрузить документ для индексации"""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".md", ".markdown"):
        raise HTTPException(400, f"Unsupported file format: {suffix}")

    # Сохраняем файл
    upload_dir = Path("data/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Индексируем
    try:
        result = await use_case.execute(file_path)
        return result
    except Exception as e:
        raise HTTPException(500, f"Indexing error: {str(e)}")


@router.get("/documents")
async def list_documents():
    """Список всех документов (файлы + индексированные)"""
    docs_dir = Path("data/documents")

    # Файлы в директории
    files = []
    if docs_dir.exists():
        for f in docs_dir.iterdir():
            if f.suffix.lower() in (".pdf", ".md", ".markdown"):
                files.append({
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                })

    # Индексированные документы из vector store
    store = get_vector_store()

    # Если store пустой, пробуем загрузить
    if not store._chunks:
        await store.load()

    indexed_sources: Dict[str, Dict[str, Any]] = {}
    for chunk in store._chunks:
        source = chunk.metadata.get("source", "unknown")
        if source not in indexed_sources:
            indexed_sources[source] = {
                "filename": source,
                "chunks_count": 0,
            }
        indexed_sources[source]["chunks_count"] += 1

    # Объединяем информацию
    all_docs = []

    # Сначала индексированные
    for source, info in indexed_sources.items():
        file_exists = any(f["filename"] == source for f in files)
        all_docs.append({
            "filename": source,
            "indexed": True,
            "chunks_count": info["chunks_count"],
            "file_exists": file_exists,
        })

    # Затем неиндексированные файлы
    for f in files:
        if not any(d["filename"] == f["filename"] for d in all_docs):
            all_docs.append({
                "filename": f["filename"],
                "indexed": False,
                "chunks_count": 0,
                "file_exists": True,
                "size_bytes": f["size_bytes"],
            })

    return {"documents": all_docs}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Удалить документ из индекса и файловой системы"""
    # Удаляем из векторного хранилища
    store = get_vector_store()
    await store.load()

    # Считаем сколько чанков удалено
    original_count = len(store._chunks)

    # Фильтруем чанки
    store._chunks = [
        chunk for chunk in store._chunks
        if chunk.metadata.get("source") != filename
    ]

    deleted_count = original_count - len(store._chunks)

    # Перестраиваем индекс если что-то удалили
    if deleted_count > 0:
        await store._rebuild_index()
        await store.persist()

    # Удаляем файл
    file_path = Path("data/documents") / filename
    file_deleted = False
    if file_path.exists():
        file_path.unlink()
        file_deleted = True

    return {
        "status": "deleted",
        "filename": filename,
        "chunks_deleted": deleted_count,
        "file_deleted": file_deleted,
    }


@router.post("/documents/reindex")
async def reindex_all():
    """Переиндексировать все документы из data/documents/"""
    use_case = get_index_use_case()
    docs_dir = Path("data/documents")

    if not docs_dir.exists():
        return {"status": "no_documents", "results": []}

    # Удаляем старый индекс
    store = get_vector_store()
    store._chunks = []
    store._chunk_map = {}
    await store.persist()

    # Индексируем заново
    results = await use_case.index_from_directory(docs_dir)

    total_chunks = sum(r.get("chunks_count", 0) for r in results)

    return {
        "status": "reindexed",
        "documents_processed": len(results),
        "total_chunks": total_chunks,
        "results": results,
    }
