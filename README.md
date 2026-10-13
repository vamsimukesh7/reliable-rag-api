# Reliable RAG API

A small, modular FastAPI knowledge assistant. It ingests PDF/TXT/Markdown files, chunks and embeds their text, retrieves relevant chunks from ChromaDB, and uses an LLM to answer with source excerpts. It abstains when retrieved evidence does not pass a configurable relevance threshold.

## Architecture

```text
POST /ingest -> validate upload -> extract text -> chunk -> SentenceTransformer embeddings -> persistent ChromaDB
POST /ask    -> embed question -> cosine retrieval -> threshold gate -> Ollama/OpenAI -> answer + evidence
```

- **API:** FastAPI; interactive docs at `/docs`.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` by default.
- **Vector store:** local persistent ChromaDB.
- **Generation:** Ollama by default, or OpenAI API.
- **Abstention:** if no retrieved chunk reaches `SIMILARITY_THRESHOLD`, the API returns a fixed unavailable message and no evidence.
- **Evidence:** each answer returns source filename, retrieved excerpt, and similarity score.
- **Configuration:** environment variables via `.env`; see `.env.example`.

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux use: cp .env.example .env
```

### Option A: local Ollama (default)

Install Ollama separately, then pull the configured model:

```bash
ollama pull qwen2.5:3b
ollama serve
uvicorn app.main:app --reload
```

The first run downloads the embedding model from Hugging Face. Keep Ollama running in another terminal. On Windows/macOS/Linux, `http://localhost:11434` is the usual Ollama URL.

### Option B: OpenAI API

Edit `.env`:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Then run `uvicorn app.main:app --reload`. Never commit `.env` or real API keys.

## API usage

### Ingest a document

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample_docs/product_overview.md"
```

Example response:

```json
{
  "filename": "product_overview.md",
  "chunks_indexed": 1,
  "document_id": "generated-id"
}
```

### Ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Which vector database is used?\"}"
```

Response shape:

```json
{
  "answer": "The documents say the vector store is ChromaDB [1].",
  "abstained": false,
  "evidence": [
    {"source":"product_overview.md","excerpt":"...persistent ChromaDB collection...","score":0.72}
  ],
  "retrieval_count": 4,
  "status": "answered"
}
```

For unsupported questions, `answer` is an explicit unavailable message, `abstained` is true, and `evidence` is empty. Scores depend on the embedding model and corpus.

### Endpoint summary

| Endpoint | Purpose |
|---|---|
| `GET /health` | Basic process health |
| `POST /ingest` | Upload PDF, TXT, or Markdown |
| `POST /ask` | Ask a question; optional `top_k` from 1–10 |

## Docker

Create `.env` from `.env.example`, then:

```bash
docker compose up --build
```

The default Ollama URL inside a container may need to be changed to the host's reachable address. For example, on Docker Desktop, try `http://host.docker.internal:11434`. Alternatively configure OpenAI. Persistent data is mounted at `./data`.

## Tests

Tests mock retrieval and LLM calls so they run without downloading models or needing an API key:

```bash
pytest -q
```

The test suite covers chunking edge cases, empty and low-relevance retrieval abstention, answer evidence, health endpoint, unsupported file types, empty uploads, and Q&A response behavior.

## Evaluation

- `evaluation/questions.json`: 10 questions covering answerable, unanswerable, and multi-evidence cases.
- `sample_docs/product_overview.md`: sample source document.
- `evaluation/README.md`: manual evaluation procedure.

Record the actual test output in your submission; do not claim tests passed until you run them in your environment.

## Limitations and next steps

1. Similarity thresholds are model- and corpus-dependent; a fixed threshold can reject valid answers or admit weak matches.
2. The LLM can still misread evidence. Inline citations are prompt-guided rather than independently verified against exact claims.
3. Scanned PDFs need OCR, which is not included.
4. This starter uses local persistent ChromaDB and is designed for a single instance; production deployments need concurrency and lifecycle hardening.
5. Authentication, tenant isolation, rate limiting, virus scanning, document deletion, and observability dashboards are not implemented.
6. A successful HTTP response is not proof of factual correctness; review the evaluation questions against a representative corpus.

## Security notes

- Upload size and extension are validated; filenames are normalized to their basename and stored under generated IDs.
- Do not expose the API publicly without authentication, request limits, and deployment-specific hardening.
- LLM failure returns an HTTP 503 rather than fabricating an answer.
