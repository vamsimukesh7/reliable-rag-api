from dataclasses import dataclass

@dataclass
class TextChunk:
    text: str
    index: int

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[TextChunk]:
    text = " ".join(text.split())
    if not text:
        return []
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        # Prefer a sentence/word boundary near the end without creating tiny chunks.
        if end < len(text):
            boundary = max(text.rfind(". ", start + chunk_size // 2, end),
                           text.rfind(" ", start + chunk_size // 2, end))
            if boundary > start:
                end = boundary + 1
        part = text[start:end].strip()
        if part:
            chunks.append(TextChunk(part, len(chunks)))
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks
