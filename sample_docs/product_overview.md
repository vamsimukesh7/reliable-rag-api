# Knowledge Assistant Product Overview

The Example Knowledge Assistant launched in 2024. It accepts PDF, TXT, and Markdown files for ingestion. Uploaded files are split into overlapping text chunks, embedded with the sentence-transformers/all-MiniLM-L6-v2 model, and indexed in a persistent ChromaDB collection.

The API exposes a POST /ingest endpoint for uploading documents and a POST /ask endpoint for questions. The default retrieval count is four chunks. The answer response includes the source filename, an excerpt from each retrieved chunk, and a similarity score.

The application can use a locally hosted Ollama model or the OpenAI API. The default local model is qwen2.5:3b. The system should only answer when retrieved evidence is relevant. If no evidence passes the configured similarity threshold, it returns an explicit message that the information could not be found in the provided documents.

The project includes automated tests for chunking, answer abstention, evidence responses, API health, and upload validation. The sample content does not specify a company CEO or annual revenue.
