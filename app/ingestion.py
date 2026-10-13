from pathlib import Path
from pypdf import PdfReader

SUPPORTED = {".pdf", ".txt", ".md", ".markdown"}

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"Unsupported file type: {suffix}. Allowed: PDF, TXT, Markdown.")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")
