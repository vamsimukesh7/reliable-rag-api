# Evaluation set

`questions.json` contains 10 starter questions: 5 answerable, 3 intentionally unanswerable, and 2 multi-evidence questions.

Run a manual smoke evaluation after starting the API:
1. Ingest `sample_docs/product_overview.md`.
2. POST each question to `/ask`.
3. Verify answers against the expected field and inspect returned excerpts.
4. For unanswerable questions, verify `abstained=true`.

The expected field is a grading hint, not a guarantee of exact wording. Similarity thresholds and LLM behavior should be tuned against a larger representative corpus.
