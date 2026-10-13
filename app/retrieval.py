
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.chunking import chunk_text


class Retriever:
    def __init__(self):
        self.settings = get_settings()
        Path(self.settings.vector_dir).mkdir(
            parents=True, exist_ok=True
        )

        self.client = chromadb.PersistentClient(
            path=self.settings.vector_dir
        )

        self.collection = self.client.get_or_create_collection(
            name=self.settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self.embedder = SentenceTransformer(
            self.settings.embedding_model
        )

    def add_document(
        self, text: str, filename: str, document_id: str
    ) -> int:
        chunks = chunk_text(
            text,
            self.settings.chunk_size,
            self.settings.chunk_overlap
        )

        if not chunks:
            return 0

        # Remove old chunks when the same filename is uploaded again.
        self.collection.delete(where={"source": filename})

        ids = [
            f"{document_id}-{chunk.index}"
            for chunk in chunks
        ]

        embeddings = self.embedder.encode(
            [chunk.text for chunk in chunks],
            normalize_embeddings=True
        ).tolist()

        self.collection.upsert(
            ids=ids,
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source": filename,
                    "document_id": document_id,
                    "chunk_index": chunk.index
                }
                for chunk in chunks
            ]
        )

        return len(chunks)

    def search(
        self, question: str, top_k: int | None = None
    ) -> list[dict]:
        if self.collection.count() == 0:
            return []

        limit = top_k or self.settings.top_k

        query_embedding = self.embedder.encode(
            [question],
            normalize_embeddings=True
        ).tolist()

        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(self.collection.count(), limit * 4),
            include=["documents", "metadatas", "distances"]
        )

        rows = []
        seen = set()

        for doc, meta, distance in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0]
        ):
            # Avoid returning duplicate chunk text.
            key = " ".join(doc.split()).casefold()

            if key in seen:
                continue

            seen.add(key)
            score = max(-1.0, min(1.0, 1.0 - float(distance)))

            rows.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "score": score,
                "document_id": meta.get("document_id"),
                "chunk_index": meta.get("chunk_index")
            })

            if len(rows) >= limit:
                break

        return rows
