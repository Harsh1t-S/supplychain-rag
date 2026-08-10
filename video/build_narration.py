"""
Build the demo-video narration track with Piper TTS.

Generates one WAV per segment so they can be dropped onto a timeline
individually, plus a single continuous narration track with silence gaps
sized to match the on-screen action.

    python build_narration.py
"""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

VOICE = "en_US-lessac-medium.onnx"
OUT = Path("segments")
OUT.mkdir(exist_ok=True)

# (id, gap_after_seconds, text)
# gap_after is dead air for on-screen action: clicking, waiting for a response,
# restarting the app. Tuned so the whole thing lands just under three minutes.
SEGMENTS: list[tuple[str, float, str]] = [
    (
        "01_intro",
        0.6,
        "This is a retrieval augmented generation assistant over two internal "
        "documents from Meridian Components. One is a quarterly supply chain "
        "review, full of numbers. The other is a procurement policy handbook, "
        "full of rules. Today a buyer reads one to find the figure, then hunts "
        "through the other to find which clause it triggers. This answers both "
        "from a single question.",
    ),
    (
        "02_index",
        3.5,
        "I'll index both PDFs. Text is extracted page by page, split at twelve "
        "hundred characters with two hundred overlap, embedded with text "
        "embedding three small, and stored in ChromaDB. Twelve hundred is "
        "deliberate. Both documents are dominated by tables, and at eight "
        "hundred the supplier scorecard splits across a boundary, so the "
        "retriever returns half a table.",
    ),
    (
        "03_confirm",
        1.5,
        "Two files, twenty two chunks. Both go into the same collection, which "
        "is what makes cross document questions possible.",
    ),
    (
        "04_persistence",
        4.5,
        "Now I stop the app and restart it. Chroma persists to disk, so the "
        "index survives with no re-uploading. Still twenty two chunks.",
    ),
    (
        "05_q1_setup",
        1.0,
        "First cross document question. Microcontrollers are imported with a "
        "forty six day lead time. How many days of safety stock? The lead time "
        "is in the review. The formula is in the handbook. Neither answers it "
        "alone.",
    ),
    (
        "06_q1_answer",
        2.0,
        "Forty six times nought point two five is eleven and a half days. But "
        "the part is imported from a Critical supplier, which carries a thirty "
        "day floor, and the policy says the higher value wins. So thirty days, "
        "not eleven and a half. Underneath, one citation from each document, "
        "with page numbers.",
    ),
    (
        "07_q2_setup",
        1.0,
        "Second one. Kaveri Metals recorded eighty eight point one percent on "
        "time delivery and eleven hundred and fifty defects per million. Which "
        "clauses does that trigger?",
    ),
    (
        "08_q2_answer",
        2.0,
        "Clause six point one for delivery below ninety percent: written warning "
        "and a weekly review call. Clause six point three for defects above five "
        "hundred: the supplier bears rework at one hundred and twenty rupees per "
        "unit, plus full incoming inspection at their cost. And it correctly "
        "does not fire clause six point two, which needs two consecutive "
        "quarters below eighty five percent. It is reading the boundary, not "
        "pattern matching.",
    ),
    (
        "09_chunks",
        2.5,
        "The retrieved chunks view confirms the context came from both PDFs. "
        "With a top k of three, all three chunks come from one document and "
        "these questions fail. Six is the smallest value that reliably spans "
        "both.",
    ),
    (
        "10_trap",
        2.0,
        "Finally, the refusal test. What is the annual salary of the Head of "
        "Procurement? Neither document contains salary data. Ungrounded, a model "
        "invents a confident, plausible, fictional number. This one says the "
        "information is not available.",
    ),
    (
        "11_api",
        1.0,
        "The same logic is exposed as a FastAPI service with ingest, ask and "
        "stats endpoints. Ask returns the answer with the file and page behind "
        "every source.",
    ),
    (
        "12_outro",
        0.0,
        "Every answer is traceable to a page, and when the answer isn't there, "
        "the system says so.",
    ),
]


def synth(seg_id: str, text: str) -> Path:
    path = OUT / f"{seg_id}.wav"
    subprocess.run(
        ["piper", "-m", VOICE, "-f", str(path)],
        input=text.encode("utf-8"),
        check=True,
        capture_output=True,
    )
    return path


def duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def main() -> None:
    manifest = []
    cursor = 0.0
    concat_parts: list[str] = []

    for seg_id, gap, text in SEGMENTS:
        path = synth(seg_id, text)
        dur = duration(path)
        manifest.append(
            {
                "id": seg_id,
                "start": round(cursor, 2),
                "duration": round(dur, 2),
                "gap_after": gap,
                "text": text,
            }
        )
        print(f"{seg_id:<16} start {cursor:6.2f}s  len {dur:5.2f}s  gap {gap:.1f}s")
        concat_parts.append(str(path))
        cursor += dur + gap

    print(f"\nTotal narration timeline: {cursor:.1f}s ({cursor/60:.2f} min)")

    # Build one continuous track with the gaps baked in.
    filter_parts = []
    inputs = []
    for i, (seg_id, gap, _) in enumerate(SEGMENTS):
        inputs.extend(["-i", str(OUT / f"{seg_id}.wav")])
        pad_ms = int(gap * 1000)
        filter_parts.append(f"[{i}:a]apad=pad_dur={gap}[a{i}]" if pad_ms else f"[{i}:a]anull[a{i}]")
    concat_inputs = "".join(f"[a{i}]" for i in range(len(SEGMENTS)))
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_inputs}concat=n={len(SEGMENTS)}:v=0:a=1[out]"
    )

    subprocess.run(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-ar", "44100", "-b:a", "192k",
            "narration_full.mp3",
        ],
        check=True,
        capture_output=True,
    )

    Path("narration_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Wrote narration_full.mp3 and narration_manifest.json")


if __name__ == "__main__":
    main()
