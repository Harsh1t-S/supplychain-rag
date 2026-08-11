"""
Streamlit interface for the Meridian supply chain assistant.

    streamlit run app.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from config import DEFAULT_TOP_K, LLM_MODEL
from ingest import ingest_files, stats
from rag import answer_question

st.set_page_config(
    page_title="Meridian Supply Chain Assistant",
    page_icon="🔩",
    layout="wide",
)

SAMPLE_QUESTIONS = [
    "Which supplier had the highest spend in Q1, and what was its on-time delivery percentage?",
    "How many line stoppages happened in Q1, what was the total downtime, and what caused them?",
    "What is the approval authority for a purchase order worth ₹1.4 crore?",
    "What are the four supplier classification categories, and what qualifies a supplier as Critical?",
    "Kaveri Metals recorded 88.1% on-time delivery and 1,150 defects per million in Q1. Which policy clauses does this trigger, and what exactly must the buyer do?",
    "The microcontroller supplier is single-source. What does the sourcing policy require in this situation, and what is the company already doing about it?",
    "Microcontrollers are imported with a 46-day lead time. Using the safety-stock policy, how many days of stock should be held for this part?",
    "Trident Circuit Boards had a defect rate of 640 parts per million. What is the cost consequence under the policy?",
    "Which suppliers would fall below the B rating band on on-time delivery alone, and what is the escalation path for them?",
    "What is the annual salary of the Head of Procurement?",
]


# --- sidebar ---------------------------------------------------------------

with st.sidebar:
    st.header("Index status")
    try:
        s = stats()
        if s["total_chunks"]:
            st.metric("Chunks in store", s["total_chunks"])
            st.caption("Indexed documents")
            for name, count in s["documents"].items():
                st.write(f"• {name} — {count} chunks")
        else:
            st.info("Nothing indexed yet.")
        st.divider()
        st.caption(
            f"Embeddings: `{s['embedding_model']}`  \n"
            f"LLM: `{LLM_MODEL}`  \n"
            f"Chunk size: {s['chunk_size']} / overlap {s['chunk_overlap']}  \n"
            f"Store: `{s['persist_directory']}`"
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read the collection: {exc}")

    st.divider()
    top_k = st.slider(
        "Chunks to retrieve (top_k)",
        min_value=2,
        max_value=12,
        value=DEFAULT_TOP_K,
        help=(
            "Cross-document questions need enough chunks to pull from both the "
            "review and the handbook. Below 5 they tend to come from one file."
        ),
    )
    show_chunks = st.checkbox("Show retrieved chunks", value=False)


# --- header ----------------------------------------------------------------

st.title("Meridian Supply Chain Assistant")
st.caption(
    "Ask about supplier performance or procurement policy. Answers come only "
    "from the indexed documents, with the source page cited."
)


# --- upload and index ------------------------------------------------------

with st.expander("Upload and index documents", expanded=not stats()["total_chunks"]):
    uploaded = st.file_uploader(
        "PDF files",
        type="pdf",
        accept_multiple_files=True,
        help="Both Meridian PDFs go into the same collection.",
    )

    col_a, col_b = st.columns([1, 3])

    with col_a:
        index_clicked = st.button("Index uploaded files", type="primary")
    with col_b:
        default_clicked = st.button("Index the two files in data/")

    if index_clicked:
        if not uploaded:
            st.warning("Choose at least one PDF first.")
        else:
            with st.spinner("Reading, chunking, embedding..."):
                tmpdir = Path(tempfile.mkdtemp())
                paths = []
                for f in uploaded:
                    p = tmpdir / f.name
                    p.write_bytes(f.getbuffer())
                    paths.append(p)
                try:
                    result = ingest_files(paths)
                    st.success(
                        f"{result['files']} files processed, "
                        f"{result['chunks']} chunks stored."
                    )
                    for row in result["detail"]:
                        st.write(
                            f"• {row['file']} — {row['pages']} pages, "
                            f"{row['chunks']} chunks"
                        )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Indexing failed: {exc}")

    if default_clicked:
        pdfs = sorted(Path("data").glob("*.pdf"))
        if not pdfs:
            st.warning("No PDFs found in data/.")
        else:
            with st.spinner("Reading, chunking, embedding..."):
                try:
                    result = ingest_files(pdfs)
                    st.success(
                        f"{result['files']} files processed, "
                        f"{result['chunks']} chunks stored."
                    )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Indexing failed: {exc}")


# --- ask -------------------------------------------------------------------


def render_answer(entry: dict, *, latest: bool, show_chunks: bool) -> None:
    """
    Render one question and its answer.

    Sources are grouped by document rather than listed flat, because on a
    cross-document question the thing a buyer needs to see at a glance is that
    the answer drew on the review *and* the handbook. A flat list of six rows
    hides that; two headed groups make it obvious.
    """
    result = entry["result"]

    if latest:
        st.markdown("### Answer")
    else:
        st.divider()
        st.markdown(f"**Earlier question:** {entry['question']}")

    st.markdown(result["answer"])

    if result["sources"]:
        by_document: dict[str, list[dict]] = {}
        for src in result["sources"]:
            by_document.setdefault(src["file"], []).append(src)

        st.markdown("**Sources**")
        for filename, rows in by_document.items():
            pages = ", ".join(
                f"p.{r['page']} (similarity {r['similarity']})" for r in rows
            )
            st.write(f"• **{filename}** — {pages}")

        if len(by_document) > 1:
            st.caption(
                f"Retrieved from {len(by_document)} documents — this answer "
                f"combines both sources."
            )
        else:
            st.caption(
                "Retrieved from one document only. For a question that needs a "
                "figure and the rule it triggers, check whether that is right."
            )

    if show_chunks and result["chunks"]:
        st.markdown("**Retrieved chunks**")
        st.caption(
            "What the model actually saw. If an answer is wrong, check here "
            "before blaming GPT-4o."
        )
        for i, chunk in enumerate(result["chunks"], start=1):
            with st.expander(
                f"Chunk {i} — {chunk['file']} p.{chunk['page']} "
                f"(similarity {chunk['similarity']})"
            ):
                st.text(chunk["text"])


st.subheader("Ask a question")

# Answers accumulate rather than replacing each other, so a buyer can compare
# what the system said across several questions instead of losing the previous
# answer on every submission.
if "history" not in st.session_state:
    st.session_state.history = []

picked = st.selectbox(
    "Sample questions from the assignment (optional)",
    ["—"] + SAMPLE_QUESTIONS,
    index=0,
)

default_text = "" if picked == "—" else picked
question = st.text_area("Question", value=default_text, height=90)

indexed = stats()["total_chunks"] > 0

ask_clicked = st.button("Ask", type="primary", disabled=not indexed)

if not indexed:
    st.info(
        "Nothing is indexed yet, so there is nothing to answer from. Use "
        "**Index the files in data/** above — the Ask button unlocks once the "
        "collection has chunks in it."
    )

if ask_clicked:
    if not question.strip():
        st.warning("Type a question first.")
    else:
        with st.spinner("Retrieving and answering..."):
            try:
                result = answer_question(question.strip(), top_k=top_k)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed: {exc}")
                result = None

        if result:
            st.session_state.history.insert(
                0, {"question": question.strip(), "result": result}
            )

for n, entry in enumerate(st.session_state.history):
    render_answer(entry, latest=(n == 0), show_chunks=show_chunks)

# Rendered after the answers so it appears on the same run that produces one,
# rather than only after the next interaction.
if st.session_state.history:
    st.divider()
    if st.button("Clear answers"):
        st.session_state.history = []
        st.rerun()
