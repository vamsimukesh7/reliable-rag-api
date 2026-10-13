from pathlib import Path
from uuid import uuid4
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.ingestion import extract_text, SUPPORTED
from app.retrieval import Retriever
from app.schemas import IngestResponse, AskRequest, AskResponse
from app.answering import answer_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-api")
settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, version="1.0.0",
              description="Evidence-grounded document Q&A with explicit abstention.")
retriever = None

def get_retriever():
    global retriever
    if retriever is None:
        retriever = Retriever()
    return retriever

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}

@app.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    filename = Path(file.filename or "upload.txt").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(status_code=415, detail="Supported formats: .pdf, .txt, .md, .markdown")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    document_id = uuid4().hex
    destination = Path(settings.upload_dir) / f"{document_id}_{filename}"
    try:
        destination.write_bytes(content)
        text = extract_text(destination)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No extractable text found in document")
        count = get_retriever().add_document(text, filename, document_id)
        if count == 0:
            raise HTTPException(status_code=422, detail="Document contained no indexable text")
        logger.info("Indexed document=%s chunks=%d", filename, count)
        return IngestResponse(filename=filename, chunks_indexed=count, document_id=document_id)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True)
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(exc).__name__}") from exc

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        rows = get_retriever().search(request.question, request.top_k)
        return answer_question(request.question, rows)
    except RuntimeError as exc:
        logger.error("Question answering unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Question answering failed")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {type(exc).__name__}") from exc

@app.exception_handler(Exception)
async def unexpected_exception_handler(request, exc):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
