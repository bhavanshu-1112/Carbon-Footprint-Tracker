"""Gemini AI micro-insight service with graceful local fallback.

Generates witty, personalized 2-sentence carbon reduction tips by calling
the Gemini API via an async HTTPX client.  Falls back to a curated set of
local tips when the API key is missing or the request fails.
"""

import os
import random
import logging

import httpx

logger = logging.getLogger(__name__)

_async_client: httpx.AsyncClient | None = None


def get_async_client() -> httpx.AsyncClient:
    """Return a module-level singleton HTTPX async client.

    Creates the client on first access with a 6-second timeout
    and conservative connection pool limits.
    """
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            timeout=6.0,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
    return _async_client


async def close_async_client() -> None:
    """Close and discard the singleton HTTPX async client.

    Safe to call even if no client was ever created.
    """
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None


# Curated local fallbacks for witty environmental tips
LOCAL_WITTY_FALLBACKS: dict[str, list[str]] = {
    "transport": [
        "Your transportation footprint suggests you're practically drag racing a bulldozer to the corner store. Maybe it's time to hop on a subway, train, or bike unless you're trying to melt the polar ice caps single-handedly.",
        "Driving gasoline/diesel vehicles puts a serious dent in our atmosphere. Consider carpooling, transit, or walking if you want to leave some clean air for the rest of us.",
        "Your air travel is sky-high. Try taking high-speed rail, or consider planting a small forest to offset that frequent flyer status.",
    ],
    "diet": [
        "Your diet is so carbon-heavy that the cows are thanking you for their short lives. Try swapping that beef for a plant-based meal, unless you're trying to set a new greenhouse gas record.",
        "Meat-heavy diets produce a mountain of CO2. Incorporating a few vegan days will lighten your food footprint and give the planet a breather.",
        "Eating this much meat might make you a top predator, but it's making the planet prey to global warming. Switch to vegetarian meals occasionally to balance the scale.",
    ],
    "energy": [
        "Your home energy consumption is bright enough to be seen from Mars. Flip the switch on empty rooms or convert to renewable energy tariffs before the grid decides to quit.",
        "Heating and electricity are sucking major juice. Unplug your phantom loads and optimize heating to keep both your wallet and the planet green.",
        "Running high grid electricity is like fueling your house with ancient coal locomotives. It's time to request a green energy tariff from your provider.",
    ],
    "waste": [
        "You're accumulating unsorted waste faster than a digital hoarder collects unread emails. Time to embrace the recycling bin, unless you plan on building a trash castle in your backyard.",
        "Unsorted trash is landfill food. Separate your recyclables to drop waste emissions and support a circular economy.",
        "Throwing everything in the trash is so last century. Composting and recycling will make your waste footprint look elegant and optimized.",
    ],
}


async def generate_witty_tip(category: str, category_co2: float, total_co2: float) -> str:
    """Generate a witty, personalized 2-sentence carbon reduction tip.

    Attempts to call the Gemini API via HTTPX; falls back to a curated
    local list on network failure or missing API key.

    Args:
        category: The highest-emitting category name (e.g. ``"transport"``).
        category_co2: CO2 emissions for the highest category in kg.
        total_co2: Total CO2 emissions across all categories in kg.

    Returns:
        A witty tip string, either from Gemini or a local fallback.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    category = category.lower()

    # Prompt formulation
    prompt = (
        f"You are a witty, slightly sarcastic, but helpful environmental advisor. "
        f"Write a personalized, witty 2-sentence tip for a user whose daily carbon footprint category "
        f"with the highest emission is '{category}' (emitting {category_co2:.1f} kg CO2 out of a total of {total_co2:.1f} kg). "
        f"Keep the message exactly two sentences, punchy, and engaging."
    )

    if not api_key:
        logger.info("GEMINI_API_KEY environment variable not set. Falling back to local witty tip.")
        return random.choice(LOCAL_WITTY_FALLBACKS.get(category, LOCAL_WITTY_FALLBACKS["diet"]))

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 120,
            "temperature": 0.85,
        },
    }

    try:
        client = get_async_client()
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            res_data = response.json()
            text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text:
                return text
        logger.warning("Gemini API returned status code %d. Falling back to local tips.", response.status_code)
    except Exception as exc:
        logger.error("Error calling Gemini API: %s. Falling back to local tips.", exc)

    # Graceful fallback on network/API failure
    return random.choice(LOCAL_WITTY_FALLBACKS.get(category, LOCAL_WITTY_FALLBACKS["diet"]))
