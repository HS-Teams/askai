"""Search presentation shared by the search service and session refiner."""

from datetime import date
from pathlib import Path

CATEGORY_ICONS = {
    "Weather": "",
    "Sports": "醴",
    "News": "",
    "Celebrities": "",
    "People": "",
    "Programming": "",
    "Travel": "",
    "General": "",
    "Maps": "",
}


def search_refinement_instructions(locale: str) -> str:
    template = (Path(__file__).resolve().parents[2] / "resources/prompts/refine-search.txt").read_text(encoding="utf-8")
    instructions = template.format(idiom=locale, datetime=date.today().isoformat()).format(
        context="Use the web results and inspected pages from the most recent execution turn in this session.",
        question="Use the original user question from that execution turn.",
    )
    categories = "\n".join(f"- {name}: {icon}" for name, icon in CATEGORY_ICONS.items())
    return f"""Apply only when the task used web search, never to greetings, local actions or RAG-only answers.
Do not search again. Apply the following refinement to that execution turn:

{instructions}

Restore the original AskAI search presentation, translating all labels to the user's language:
- A short synthesis, then numbered results with **bold linked titles**, concise descriptions and real source URLs.
- A horizontal rule and one compact footer:
  `ICON Category`  **Sources:** linked source names  **Access:** verified access date
- A separate blockquote: >  Terms: actual search terms

Choose exactly one category by classifying the search topic. This is a presentation
classification, not metadata that the search engine must supply. Translate its label
and use the corresponding original AskAI icon:
{categories}

Use only consulted sources. Distinguish snippets from inspected pages and preserve
blocked-page or uncertain-evidence limitations. Omit access date, location or search
terms when unavailable in the session. Never invent links, dates, terms or location.
Do not call the search Google unless the evidence identifies that engine.
Keep this layout and source links even with accessibility enabled; keep prose concise.
This layout is an exception to avoiding decorative sections. Return it entirely
inside final_answer, without a refinement report or additional JSON fields.
"""
