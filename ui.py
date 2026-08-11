"""
Presentation layer for the Streamlit app.

Kept apart from app.py so the interface logic stays readable: app.py reads as a
sequence of what happens, and the styling and HTML fragments live here.

Nothing in this module touches retrieval, the model, or the store. It renders.
"""

from __future__ import annotations

import html

ACCENT = "#F5A524"

# The similarity scores this system produces sit roughly between 0.30 and 0.70.
# Drawing a bar as a raw percentage of 1.0 would make every result look weak and
# nearly identical, so the range is stretched across the bar's full width.
SIM_FLOOR = 0.25
SIM_CEIL = 0.75


CSS = f"""
<style>
  /* Hide the Streamlit toolbar so the app reads as a product rather than a
     notebook -- it also keeps the Deploy button out of submitted screenshots. */
  [data-testid="stToolbar"], #MainMenu, footer {{ visibility: hidden; height: 0; }}

  /* Hiding the toolbar also buries the control that reopens a collapsed
     sidebar, which strands the user with no way to get it back. Put it
     explicitly back on top. */
  [data-testid="stSidebarCollapsedControl"] {{
    visibility: visible !important; height: auto !important;
    opacity: 1 !important; z-index: 999999 !important;
  }}
  [data-testid="stSidebarCollapsedControl"] button {{
    background: #111A2B !important; border: 1px solid #1E2C44 !important;
    border-radius: 9px !important;
  }}

  .block-container {{ padding-top: 3.1rem; padding-bottom: 4rem; max-width: 1180px; }}

  html, body, [class*="css"] {{
    font-family: "Inter", "Segoe UI", -apple-system, sans-serif;
  }}

  /* --- hero ------------------------------------------------------------- */
  .hero {{ margin-bottom: 1.4rem; }}
  .hero-eyebrow {{
    font-size: .74rem; letter-spacing: .18em; text-transform: uppercase;
    color: #FCD34D; font-weight: 700; margin-bottom: .5rem;
  }}
  .hero-title {{
    font-size: 2.35rem; font-weight: 700; line-height: 1.12; margin: 0 0 .5rem;
    background: linear-gradient(92deg, #E6EDF6 15%, {ACCENT} 130%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }}
  .hero-sub {{ color: #94A7BD; font-size: .97rem; max-width: 62ch; line-height: 1.55; }}

  /* --- stat strip ------------------------------------------------------- */
  .stats {{ display: flex; gap: .7rem; flex-wrap: wrap; margin: 1.2rem 0 .4rem; }}
  .stat {{
    flex: 1 1 150px; background: #111A2B; border: 1px solid #1E2C44;
    border-radius: 12px; padding: .8rem .95rem;
  }}
  .stat-label {{
    font-size: .68rem; letter-spacing: .1em; text-transform: uppercase;
    color: #7D93AC; font-weight: 600;
  }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #E6EDF6; line-height: 1.5; }}
  .stat-sub {{ font-size: .74rem; color: #6B819B; font-family: ui-monospace, monospace; }}

  .pill {{
    display: inline-flex; align-items: center; gap: .4rem; font-size: .74rem;
    font-weight: 600; padding: .25rem .7rem; border-radius: 999px;
  }}
  .pill-on  {{ background: rgba(245,165,36,.13); color: {ACCENT}; border: 1px solid rgba(245,165,36,.32); }}
  .pill-off {{ background: rgba(248,113,113,.11); color: #F87171; border: 1px solid rgba(248,113,113,.28); }}
  .dot {{ width: 6px; height: 6px; border-radius: 50%; background: currentColor; }}

  /* --- answer card ------------------------------------------------------ */
  [data-testid="stVerticalBlockBorderWrapper"] {{
    background: #0E1626; border: 1px solid #1E2C44 !important;
    border-radius: 14px; padding: .3rem .2rem;
  }}
  .ans-head {{
    display: flex; align-items: center; gap: .55rem; font-size: .72rem;
    letter-spacing: .14em; text-transform: uppercase; color: {ACCENT};
    font-weight: 700; margin-bottom: .1rem;
  }}
  .ask-echo {{
    color: #9FB3C8; font-size: .92rem; font-style: italic;
    border-left: 2px solid #2A3B57; padding-left: .8rem; margin: .1rem 0 .9rem;
  }}

  /* --- sources ---------------------------------------------------------- */
  .src-head {{
    font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
    color: #7D93AC; font-weight: 700; margin-top: 1.1rem;
  }}
  .src-doc {{
    display: flex; align-items: center; gap: .45rem; font-size: .86rem;
    font-weight: 650; color: #D3E0EF; margin: .75rem 0 .35rem;
  }}
  .src-row {{
    display: flex; align-items: center; gap: .7rem; padding: .3rem 0 .3rem 1.35rem;
  }}
  .src-page {{
    font-size: .78rem; color: #8FA5BE; font-family: ui-monospace, monospace;
    min-width: 3.1rem;
  }}
  .meter {{
    flex: 1; height: 5px; background: #17233A; border-radius: 999px; overflow: hidden;
    max-width: 320px;
  }}
  .meter-fill {{
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #8A5A12, {ACCENT});
  }}
  .src-sim {{
    font-size: .74rem; color: #7D93AC; font-family: ui-monospace, monospace;
    min-width: 3.2rem; text-align: right;
  }}
  .spread {{
    font-size: .78rem; color: #7D93AC; margin-top: .7rem;
    border-top: 1px dashed #23334C; padding-top: .6rem;
  }}
  .spread strong {{ color: #B9CBDE; }}

  /* --- sidebar ---------------------------------------------------------- */
  [data-testid="stSidebar"] {{ background: #080D16; border-right: 1px solid #16223A; }}
  /* Nothing sits flush against the panel edge, which also keeps labels intact
     when the app is captured for screenshots. */
  [data-testid="stSidebarUserContent"] {{ padding-left: .55rem; padding-right: .35rem; }}
  .side-h {{
    font-size: .68rem; letter-spacing: .14em; text-transform: uppercase;
    color: #6B819B; font-weight: 700; margin: 1.1rem 0 .5rem;
  }}
  .doc-item {{
    background: #0E1626; border: 1px solid #1B2740; border-radius: 9px;
    padding: .5rem .65rem; margin-bottom: .4rem;
  }}
  .doc-name {{ font-size: .76rem; color: #C7D6E6; word-break: break-word; line-height: 1.35; }}
  .doc-meta {{ font-size: .7rem; color: {ACCENT}; font-weight: 600; margin-top: .15rem; }}
  .kv {{ display: flex; justify-content: space-between; gap: .6rem; padding: .22rem 0; font-size: .76rem; }}
  .kv span:first-child {{ color: #6B819B; }}
  .kv span:last-child {{ color: #C7D6E6; font-family: ui-monospace, monospace; font-size: .72rem; }}

  /* --- controls --------------------------------------------------------- */
  .stButton > button {{ border-radius: 9px; font-weight: 600; letter-spacing: .01em; }}
  .stTextArea textarea {{
    background: #0E1626 !important; border: 1px solid #1E2C44 !important;
    border-radius: 11px !important; font-size: .93rem !important;
  }}
  .stTextArea textarea:focus {{ border-color: {ACCENT} !important; box-shadow: none !important; }}
  div[data-testid="stExpander"] details {{
    background: #0C1422; border: 1px solid #1B2740; border-radius: 10px;
  }}
</style>
"""


def hero(eyebrow: str, title: str, subtitle: str) -> str:
    return (
        f'<div class="hero">'
        f'<div class="hero-eyebrow">{html.escape(eyebrow)}</div>'
        f'<div class="hero-title">{html.escape(title)}</div>'
        f'<div class="hero-sub">{html.escape(subtitle)}</div>'
        f"</div>"
    )


def stat_strip(cards: list[tuple[str, str, str]]) -> str:
    cells = "".join(
        f'<div class="stat"><div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value">{html.escape(value)}</div>'
        f'<div class="stat-sub">{html.escape(sub)}</div></div>'
        for label, value, sub in cards
    )
    return f'<div class="stats">{cells}</div>'


def status_pill(indexed: bool, chunks: int) -> str:
    if indexed:
        return (
            f'<span class="pill pill-on"><span class="dot"></span>'
            f"Indexed &middot; {chunks} chunks ready</span>"
        )
    return (
        '<span class="pill pill-off"><span class="dot"></span>'
        "Nothing indexed yet</span>"
    )


def _bar_width(similarity: float) -> float:
    span = SIM_CEIL - SIM_FLOOR
    return max(4.0, min(100.0, (similarity - SIM_FLOOR) / span * 100.0))


def sources_block(sources: list[dict], *, unit_plural: str) -> str:
    """Sources grouped by document, each page with a similarity meter."""
    by_document: dict[str, list[dict]] = {}
    for src in sources:
        by_document.setdefault(src["file"], []).append(src)

    parts: list[str] = ["<div class=""src-head"">Sources</div>"]
    for filename, rows in by_document.items():
        parts.append(f'<div class="src-doc">&#128196; {html.escape(filename)}</div>')
        for row in rows:
            width = _bar_width(float(row["similarity"]))
            parts.append(
                f'<div class="src-row">'
                f'<span class="src-page">p. {row["page"]}</span>'
                f'<div class="meter"><div class="meter-fill" style="width:{width:.0f}%"></div></div>'
                f'<span class="src-sim">{row["similarity"]:.4f}</span>'
                f"</div>"
            )

    count = len(by_document)
    parts.append(
        f'<div class="spread">Retrieved from <strong>{count}</strong> '
        f"{unit_plural}. An answer built from fewer sources than it names reads "
        f"exactly like a complete one, so this count is worth checking.</div>"
    )
    return "".join(parts)
