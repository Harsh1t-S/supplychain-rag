# docs/

`test_answers.md` — the answers this app actually produced for all ten
assignment questions, written by `python run_test_questions.py --show-chunks`.
It records each answer, the source document and page behind it, the similarity
score of every retrieved chunk, and — for the five cross-document questions —
whether retrieval reached both PDFs or only one.

That last check is the point. An answer built from the policy handbook alone
cites real clause numbers and reads perfectly well, while being untethered from
the supplier figures it is supposed to be about. All five cross-document
questions reached both documents.

`screenshot-*.png` — the working app: indexing, a cross-document answer, the
trap question being refused, and the FastAPI docs page.

Regenerate the answers with a valid `OPENAI_API_KEY` in `.env`:

```bash
python ingest.py
python run_test_questions.py --show-chunks
```
