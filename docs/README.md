# docs/

Generated output lands here. Nothing in this folder is committed except this
file, because everything else is the product of one particular run.

`test_answers.md` — written by `python run_test_questions.py --show-chunks`.
It records the system's actual answer to each of the ten assignment questions,
the source file and page behind every answer, the similarity score of each
retrieved chunk, and — for the five cross-document questions — whether
retrieval actually reached both PDFs or only one.

That last check is the point. An answer built from the policy handbook alone
cites real clause numbers and reads perfectly well, while being untethered from
the supplier figures it is supposed to be about.

Regenerate it with a valid `OPENAI_API_KEY` in `.env`:

```bash
python ingest.py
python run_test_questions.py --show-chunks
```
