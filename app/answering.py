import json
from app.config import get_settings

ABSTENTION = "I couldn't find enough information in the provided documents to answer that question."

SYSTEM_PROMPT = """You are a careful document-grounded assistant.
Answer only with facts supported by the supplied evidence.
If evidence does not directly support an answer, say that the information is unavailable.
Do not use outside knowledge. Distinguish facts from uncertainty.
Cite evidence inline using [1], [2], matching the numbered evidence.
Keep answers concise."""


def build_prompt(question: str, evidence: list[dict]) -> str:
    blocks = []
    for i, item in enumerate(evidence, 1):
        blocks.append(
            f"[{i}] Source: {item['source']} (similarity={item['score']:.3f})\n{item['text']}")
    return f"Question: {question}\n\nEvidence:\n" + "\n\n".join(blocks) + "\n\nAnswer using only this evidence."


def generate_answer(question: str, evidence: list[dict]) -> str:
    settings = get_settings()
    prompt = build_prompt(question, evidence)
    if settings.llm_provider.lower() == "openai":
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
    if settings.llm_provider.lower() == "ollama":
        import requests
        response = requests.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/chat",
            json={"model": settings.ollama_model, "stream": False,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": prompt}],
                  "options": {"temperature": 0}},
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    raise RuntimeError("LLM_PROVIDER must be 'ollama' or 'openai'")


def answer_question(question: str, rows: list[dict]) -> dict:
    settings = get_settings()
    print("Retrieved rows:", rows)
    print("Similarity threshold:", settings.similarity_threshold)
    usable = [r for r in rows if r["score"] >= settings.similarity_threshold]
    if not usable:
        return {"answer": ABSTENTION, "abstained": True, "evidence": [],
                "retrieval_count": len(rows), "status": "insufficient_evidence"}
    try:
        answer = generate_answer(question, usable)
    except Exception as exc:
        # Fail closed: never manufacture an answer when the model is unavailable.
        raise RuntimeError(
            f"LLM generation failed: {type(exc).__name__}") from exc
    if not answer:
        answer = ABSTENTION
    abstained = answer.strip() == ABSTENTION
    return {
        "answer": answer, "abstained": abstained,
        "evidence": [{"source": r["source"], "excerpt": r["text"], "score": round(r["score"], 4)} for r in usable],
        "retrieval_count": len(rows),
        "status": "insufficient_evidence" if abstained else "answered"
    }
