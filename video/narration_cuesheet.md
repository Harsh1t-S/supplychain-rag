# Narration cue sheet

Total: **179.4s** (under the 3:00 limit).

Play `narration_full.mp3` in one ear while recording and follow these cues.
Or record silent, then place each `segments/*.wav` at the listed start time.

| Start | Len | Segment | What to do on screen |
|---|---|---|---|
| **0:00.00** | 19.7s | `01_intro` | App open in browser, sidebar shows 'Nothing indexed yet.' Do nothing — just let it sit. |
| **0:20.26** | 20.6s | `02_index` | Open 'Upload and index documents'. Select BOTH PDFs. Click 'Index uploaded files' as narration mentions ChromaDB. |
| **0:44.38** | 6.7s | `03_confirm` | Hover the '2 files processed, 22 chunks stored' message. Glance at sidebar updating. |
| **0:52.53** | 7.8s | `04_persistence` | Cut to terminal. Ctrl+C. Re-run `streamlit run app.py`. Reload browser. Point at sidebar still showing 22. |
| **1:04.85** | 12.2s | `05_q1_setup` | Pick the safety-stock question from the dropdown. Do NOT click Ask yet. |
| **1:18.04** | 16.7s | `06_q1_answer` | Click Ask at the START of this segment. Answer appears. Scroll to Sources, hover both citations. |
| **1:36.70** | 9.1s | `07_q2_setup` | Pick the Kaveri Metals question from the dropdown. |
| **1:46.76** | 23.2s | `08_q2_answer` | Click Ask at the START. Let the answer render. Highlight '6.1' and '6.3' with the cursor. |
| **2:11.99** | 12.6s | `09_chunks` | Tick 'Show retrieved chunks'. Expand two chunks — one from each PDF. |
| **2:27.12** | 14.2s | `10_trap` | Type the salary question. Click Ask. Let the refusal render. |
| **2:43.33** | 9.5s | `11_api` | Cut to http://localhost:8000/docs. Expand /ask, Try it out, Execute, show JSON. |
| **2:53.85** | 5.5s | `12_outro` | Stay on the JSON response or cut back to an answered question. Hold still. |

---

## Narration text

**0:00.00 — 01_intro**

> This is a retrieval augmented generation assistant over two internal documents from Meridian Components. One is a quarterly supply chain review, full of numbers. The other is a procurement policy handbook, full of rules. Today a buyer reads one to find the figure, then hunts through the other to find which clause it triggers. This answers both from a single question.

**0:20.26 — 02_index**

> I'll index both PDFs. Text is extracted page by page, split at twelve hundred characters with two hundred overlap, embedded with text embedding three small, and stored in ChromaDB. Twelve hundred is deliberate. Both documents are dominated by tables, and at eight hundred the supplier scorecard splits across a boundary, so the retriever returns half a table.

**0:44.38 — 03_confirm**

> Two files, twenty two chunks. Both go into the same collection, which is what makes cross document questions possible.

**0:52.53 — 04_persistence**

> Now I stop the app and restart it. Chroma persists to disk, so the index survives with no re-uploading. Still twenty two chunks.

**1:04.85 — 05_q1_setup**

> First cross document question. Microcontrollers are imported with a forty six day lead time. How many days of safety stock? The lead time is in the review. The formula is in the handbook. Neither answers it alone.

**1:18.04 — 06_q1_answer**

> Forty six times nought point two five is eleven and a half days. But the part is imported from a Critical supplier, which carries a thirty day floor, and the policy says the higher value wins. So thirty days, not eleven and a half. Underneath, one citation from each document, with page numbers.

**1:36.70 — 07_q2_setup**

> Second one. Kaveri Metals recorded eighty eight point one percent on time delivery and eleven hundred and fifty defects per million. Which clauses does that trigger?

**1:46.76 — 08_q2_answer**

> Clause six point one for delivery below ninety percent: written warning and a weekly review call. Clause six point three for defects above five hundred: the supplier bears rework at one hundred and twenty rupees per unit, plus full incoming inspection at their cost. And it correctly does not fire clause six point two, which needs two consecutive quarters below eighty five percent. It is reading the boundary, not pattern matching.

**2:11.99 — 09_chunks**

> The retrieved chunks view confirms the context came from both PDFs. With a top k of three, all three chunks come from one document and these questions fail. Six is the smallest value that reliably spans both.

**2:27.12 — 10_trap**

> Finally, the refusal test. What is the annual salary of the Head of Procurement? Neither document contains salary data. Ungrounded, a model invents a confident, plausible, fictional number. This one says the information is not available.

**2:43.33 — 11_api**

> The same logic is exposed as a FastAPI service with ingest, ask and stats endpoints. Ask returns the answer with the file and page behind every source.

**2:53.85 — 12_outro**

> Every answer is traceable to a page, and when the answer isn't there, the system says so.
