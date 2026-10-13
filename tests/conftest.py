import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module

@pytest.fixture
def client(monkeypatch, tmp_path):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "vector_dir", str(tmp_path / "vectors"))
    # Tests replace retrieval and generation, so no model download/network is needed.
    class FakeRetriever:
        def add_document(self, text, filename, document_id): return 2
        def search(self, question, top_k=None):
            if "unavailable" in question.lower():
                return []
            return [{"text": "The service launched in 2024 and supports PDF uploads.",
                     "source": "sample.md", "score": 0.91}]
    monkeypatch.setattr(main_module, "retriever", FakeRetriever())
    monkeypatch.setattr(main_module, "get_retriever", lambda: main_module.retriever)
    return TestClient(app)
