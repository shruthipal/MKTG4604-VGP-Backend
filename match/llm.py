"""
LLM personalization layer — Ollama llama3 at http://localhost:11434.

R-01 enforcement (nonprofit framing):
  The nonprofit prompt is structurally different from all others:
    • Persona: nonprofit procurement advisor
    • Framing: mission impact, resource stewardship, community benefit
    • Hard block: the words "profit", "revenue", "ROI", "margin", "markup",
      "financial return" are explicitly forbidden in the instructions.
  This ensures the model cannot inadvertently use profit-margin language
  for nonprofits regardless of the item description.

Non-nonprofit prompts are segment-aware:
  • reseller  → resale value, market demand, turnover
  • smb       → operational efficiency, cost savings, business fit
  • consumer  → personal value, everyday utility, quality

Timeout: 10 s per call (Ollama on local hardware).
Fallback: if Ollama is unavailable or times out, a deterministic template
          is returned so the pipeline always completes.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
LLM_TIMEOUT_SECONDS = 10.0

# ── Segment prompt configs ─────────────────────────────────────────────────────

_SEGMENT_CONFIG: dict[str, dict[str, str]] = {
    "nonprofit": {
        "persona": (
            "You are a procurement advisor helping a nonprofit organization "
            "source inventory for their programs and community services."
        ),
        "framing": (
            "Frame your recommendation around mission alignment, community benefit, "
            "and resource stewardship. Explain how this item can serve the "
            "organization's goals or the people it helps. "
            "You MUST NOT use any of the following words or concepts: "
            "profit, revenue, ROI, margin, markup, financial return, or resale value. "
            "Focus exclusively on impact, accessibility, and practical utility."
        ),
    },
    "reseller": {
        "persona": "You are a wholesale merchandise advisor for resellers and distributors.",
        "framing": (
            "Frame your recommendation around resale potential, market demand, "
            "inventory turnover speed, and profit margin opportunity. "
            "Be specific about why this category and condition level resells well."
        ),
    },
    "smb": {
        "persona": "You are a small business operations consultant.",
        "framing": (
            "Frame your recommendation around operational efficiency, cost savings, "
            "and how the item supports the business's day-to-day needs. "
            "Highlight practical fit and value relative to typical retail pricing."
        ),
    },
    "consumer": {
        "persona": "You are a personal shopping advisor.",
        "framing": (
            "Frame your recommendation around personal value, everyday utility, "
            "and quality for the price. Be warm and practical."
        ),
    },
}

_DEFAULT_CONFIG = _SEGMENT_CONFIG["consumer"]


def _build_prompt(item: dict, segment: str, composite_score: float) -> str:
    config = _SEGMENT_CONFIG.get(segment, _DEFAULT_CONFIG)
    description_line = (
        f"- Description: {item['description']}\n" if item.get("description") else ""
    )
    match_quality = (
        "strong" if composite_score >= 0.75
        else "good" if composite_score >= 0.50
        else "moderate"
    )
    return (
        f"{config['persona']}\n\n"
        f"{config['framing']}\n\n"
        f"This is a {match_quality} match. Here are the item details:\n"
        f"- Name: {item.get('title', 'N/A')}\n"
        f"- Category: {item.get('category', 'N/A')}\n"
        f"- Condition: {item.get('condition', 'N/A')}\n"
        f"- Price: ${float(item.get('price', 0)):.2f}\n"
        f"- Quantity available: {item.get('quantity', 0)}\n"
        f"{description_line}"
        f"\nWrite exactly 2 sentences recommending this item. "
        f"Be specific and helpful. Plain text only — no bullet points, "
        f"no asterisks, no special formatting."
    )


def _template_fallback(item: dict, segment: str) -> str:
    """
    Deterministic fallback used when Ollama is unreachable or times out.
    R-01: nonprofit fallback uses mission framing, never profit language.
    """
    title = item.get("title", "this item")
    category = item.get("category", "general")
    condition = item.get("condition", "used")
    price = float(item.get("price", 0))
    qty = item.get("quantity", 0)

    if segment == "nonprofit":
        # R-01: mission framing, no profit language
        return (
            f"This {condition} {category} item — \"{title}\" — may support your "
            f"organization's programs and the communities you serve. "
            f"{'Available at no cost' if price == 0 else f'Priced at ${price:.2f}'} "
            f"with {qty} unit(s) in stock, it offers a practical resource for your mission."
        )
    if segment == "reseller":
        return (
            f"\"{title}\" is a {condition}-condition {category} item at ${price:.2f} "
            f"with {qty} unit(s) available — strong resale potential in this category. "
            f"The price point and available quantity support healthy margin opportunity."
        )
    if segment == "smb":
        return (
            f"\"{title}\" is a {condition} {category} item priced at ${price:.2f} "
            f"with {qty} unit(s) available — a practical fit for operational needs. "
            f"Sourcing at this price delivers clear cost savings versus standard retail."
        )
    # consumer default
    return (
        f"\"{title}\" is a {condition}-condition {category} item at ${price:.2f} "
        f"— {qty} unit(s) in stock. "
        f"Great everyday value at this price point."
    )


async def generate_recommendation(
    item: dict,
    segment: str,
    composite_score: float,
) -> str:
    """
    Call Ollama llama3 to generate a segment-aware recommendation.
    R-01: nonprofit prompt structurally forbids profit/margin language.
    Falls back to template on timeout or connection error.
    """
    prompt = _build_prompt(item, segment, composite_score)

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.4, "num_predict": 120},
                },
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            if text:
                return text
            # Empty response — fall through to template
    except httpx.TimeoutException:
        logger.warning(
            "[LLM] Ollama request timed out (>%ds) for item %s — using template fallback.",
            LLM_TIMEOUT_SECONDS,
            item.get("id", "unknown"),
        )
    except httpx.ConnectError:
        logger.warning(
            "[LLM] Ollama not reachable at %s — using template fallback.", OLLAMA_URL
        )
    except Exception as exc:
        logger.warning("[LLM] Unexpected error: %s — using template fallback.", exc)

    return _template_fallback(item, segment)
