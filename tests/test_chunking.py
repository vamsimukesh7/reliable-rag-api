import pytest
from app.chunking import chunk_text

def test_chunk_text_splits_and_preserves_content():
    chunks = chunk_text("word " * 300, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(c.text for c in chunks)

def test_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []

def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)
