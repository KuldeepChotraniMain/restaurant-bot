"""
services/ai_chat.py — Gemini-powered café assistant (Mia)
"""

import random

from google import genai

from config import Config

# Initialise Gemini client once at import time (None if no key is set)
_client = genai.Client(api_key=Config.GOOGLE_API_KEY) if Config.GOOGLE_API_KEY else None

_FALLBACKS = [
    "Great choice to explore the menu! What are you in the mood for — something to eat, or a great coffee?",
    "Happy to help you find the perfect thing! Are you feeling like something sweet, savoury, or a drink?",
    "Of course! Tell me what you're craving and I'll point you in the right direction.",
]

_SYSTEM_TEMPLATE = """\
You are Mia, the warm and knowledgeable café assistant at aosa Bakehouse & Roastery.

Your personality: warm, friendly, genuine, enthusiastic about the menu, helpful and \
specific, conversational. Never robotic — avoid lists when a natural sentence works better.

The customer's name is{name_part}.

Important menu knowledge:
- aosa is famous for its cold brews, croissants, and specialty pour-over coffees
- Signature items: Aosa Croissant, Cappuccino, Vietnamese Styled Iced Coffee, \
Cold Brew Classic, Chocolate Croissant, New York Cheesecake
- Must-try: Coffee Tonic, Salted Caramel Popcorn Latte, Korean Bun 2.0, Tiramisu Tub
- All prices are in Indian Rupees (₹)

Full menu:
{menu_context}

Guidelines:
- Keep replies conversational and under 4 sentences unless listing items
- When recommending, mention WHY — be specific and appetizing
- Highlight vegetarian/vegan options when asked
- Always address the customer by name when known
- End with a soft question or offer naturally
- Reference earlier messages naturally for continuity\
"""


def _build_prompt(
    messages_history: list[dict],
    customer_name: str,
    menu_context: str,
) -> str:
    name_part = (
        f" {customer_name}"
        if customer_name and customer_name.lower() not in ("guest", "")
        else " not provided yet"
    )

    system = _SYSTEM_TEMPLATE.format(name_part=name_part, menu_context=menu_context)

    history_lines = [
        f"{'Customer' if m['role'] == 'user' else 'Mia'}: {m['content']}"
        for m in messages_history[:-1]
    ]
    history = "\n".join(history_lines) if history_lines else "(Start of conversation)"

    context_note = (
        "\n\nIf the customer uses vague references like 'which one', 'that one', "
        "resolve them by looking at your previous replies.\n"
        if len(messages_history) > 1
        else ""
    )

    last_message = messages_history[-1]["content"]

    return (
        f"{system}{context_note}\n\n"
        f"Conversation so far:\n{history}\n\n"
        f"Customer: {last_message}\nMia:"
    )


def get_ai_response(
    messages_history: list[dict],
    customer_name: str,
    menu_context: str,
) -> str:
    """
    Call Gemini and return Mia's reply.
    Falls back to a canned response if the API key is missing or the call fails.
    """
    if not _client:
        return random.choice(_FALLBACKS)

    try:
        prompt   = _build_prompt(messages_history, customer_name, menu_context)
        response = _client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()

    except Exception as exc:
        print(f"[Gemini error] {exc}")
        return random.choice(_FALLBACKS)
