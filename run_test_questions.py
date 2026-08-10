"""
Run all ten assignment questions against the indexed collection and write the
answers to docs/test_answers.md, ready to paste into the README.

    python ingest.py            # index first
    python run_test_questions.py

Add --show-chunks to also dump which chunks were retrieved for each question,
which is what you look at when an answer comes out wrong.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from config import CHUNK_OVERLAP, CHUNK_SIZE, DEFAULT_TOP_K, EMBEDDING_MODEL, LLM_MODEL
from ingest import stats
from rag import answer_question

QUESTIONS: list[tuple[str, str]] = [
    ("Single document", "Which supplier had the highest spend in Q1, and what was its on-time delivery percentage?"),
    ("Single document", "How many line stoppages happened in Q1, what was the total downtime, and what caused them?"),
    ("Single document", "What is the approval authority for a purchase order worth ₹1.4 crore?"),
    ("Single document", "What are the four supplier classification categories, and what qualifies a supplier as Critical?"),
    ("Cross document", "Kaveri Metals recorded 88.1% on-time delivery and 1,150 defects per million in Q1. Which policy clauses does this trigger, and what exactly must the buyer do?"),
    ("Cross document", "The microcontroller supplier is single-source. What does the sourcing policy require in this situation, and what is the company already doing about it?"),
    ("Cross document", "Microcontrollers are imported with a 46-day lead time. Using the safety-stock policy, how many days of stock should be held for this part?"),
    ("Cross document", "Trident Circuit Boards had a defect rate of 640 parts per million. What is the cost consequence under the policy?"),
    ("Cross document", "Which suppliers would fall below the B rating band on on-time delivery alone, and what is the escalation path for them?"),
    ("Trap", "What is the annual salary of the Head of Procurement?"),
]


def main() -> None:
    show_chunks = "--show-chunks" in sys.argv

    s = stats()
    if not s["total_chunks"]:
        print("Nothing indexed. Run `python ingest.py` first.")
        raise SystemExit(1)

    out = Path("docs")
    out.mkdir(exist_ok=True)
    target = out / "test_answers.md"

    lines: list[str] = [
        "# Test question results",
        "",
        f"Generated {datetime.now():%d %B %Y, %H:%M}",
        "",
        f"- Chunks indexed: **{s['total_chunks']}** "
        f"({', '.join(f'{k}: {v}' for k, v in s['documents'].items())})",
        f"- Chunk size / overlap: **{CHUNK_SIZE} / {CHUNK_OVERLAP}**",
        f"- Embeddings: `{EMBEDDING_MODEL}` · LLM: `{LLM_MODEL}` · top_k: **{DEFAULT_TOP_K}**",
        "",
        "---",
        "",
    ]

    for n, (kind, question) in enumerate(QUESTIONS, start=1):
        print(f"[{n}/10] {kind}: {question[:60]}...")
        result = answer_question(question, top_k=DEFAULT_TOP_K)

        lines.append(f"## Q{n} — {kind}")
        lines.append("")
        lines.append(f"**Question:** {question}")
        lines.append("")
        lines.append("**Answer:**")
        lines.append("")
        lines.append(result["answer"])
        lines.append("")

        if result["sources"]:
            lines.append("**Sources retrieved:**")
            lines.append("")
            for src in result["sources"]:
                lines.append(
                    f"- `{src['file']}` page {src['page']} "
                    f"(similarity {src['similarity']})"
                )
            lines.append("")

        files_hit = {src["file"] for src in result["sources"]}
        if kind == "Cross document":
            verdict = "both documents" if len(files_hit) > 1 else "ONE DOCUMENT ONLY — check top_k"
            lines.append(f"**Retrieval spread:** {verdict}")
            lines.append("")

        if show_chunks:
            lines.append("<details><summary>Retrieved chunks</summary>")
            lines.append("")
            for i, chunk in enumerate(result["chunks"], start=1):
                lines.append(
                    f"**Chunk {i}** — {chunk['file']} p.{chunk['page']} "
                    f"(similarity {chunk['similarity']})"
                )
                lines.append("")
                lines.append("```")
                lines.append(chunk["text"])
                lines.append("```")
                lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWritten to {target}")


if __name__ == "__main__":
    main()
