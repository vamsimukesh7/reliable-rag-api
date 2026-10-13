def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_unsupported_file_rejected(client):
    response = client.post("/ingest", files={"file": ("evil.exe", b"hello", "application/octet-stream")})
    assert response.status_code == 415

def test_empty_file_rejected(client):
    response = client.post("/ingest", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 400

def test_ask_returns_answer_and_evidence(client, monkeypatch):
    import app.main as main_module
    monkeypatch.setattr(main_module, "answer_question", lambda q, rows: {
        "answer":"The service launched in 2024 [1].", "abstained":False,
        "evidence":[{"source":"sample.md","excerpt":"The service launched in 2024.","score":0.91}],
        "retrieval_count":1, "status":"answered"})
    response = client.post("/ask", json={"question":"When did the service launch?"})
    assert response.status_code == 200
    assert response.json()["evidence"][0]["source"] == "sample.md"

def test_ask_unanswerable(client, monkeypatch):
    import app.main as main_module
    monkeypatch.setattr(main_module, "answer_question", lambda q, rows: {
        "answer":"I couldn't find enough information in the provided documents to answer that question.",
        "abstained":True, "evidence":[], "retrieval_count":0, "status":"insufficient_evidence"})
    response = client.post("/ask", json={"question":"What is unavailable?"})
    assert response.status_code == 200
    assert response.json()["abstained"] is True
