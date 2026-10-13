from app.answering import answer_question, ABSTENTION
from app.config import get_settings

def test_unanswerable_question_abstains(monkeypatch):
    monkeypatch.setattr(get_settings(), "similarity_threshold", 0.25)
    result = answer_question("What is unavailable?", [])
    assert result["abstained"] is True
    assert result["answer"] == ABSTENTION
    assert result["evidence"] == []

def test_low_similarity_abstains(monkeypatch):
    monkeypatch.setattr(get_settings(), "similarity_threshold", 0.5)
    result = answer_question("What happened?", [{"text":"x","source":"a.txt","score":0.2}])
    assert result["abstained"] is True

def test_grounded_answer_returns_evidence(monkeypatch):
    import app.answering as answering
    monkeypatch.setattr(get_settings(), "similarity_threshold", 0.25)
    monkeypatch.setattr(answering, "generate_answer", lambda q, e: "It launched in 2024 [1].")
    result = answer_question("When did it launch?", [{"text":"Launched in 2024","source":"facts.txt","score":0.9}])
    assert result["status"] == "answered"
    assert result["evidence"][0]["source"] == "facts.txt"
