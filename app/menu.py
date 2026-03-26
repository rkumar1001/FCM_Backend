"""
Menu registry for The Masala Twist.

Provides a canonical set of menu item names and a fuzzy-match lookup so that
slight AI transcription variations (e.g. "Lamb Sherry Korma" → "Lamb Shahi Korma")
still resolve to real menu items.
"""

from difflib import SequenceMatcher

# ── Canonical menu items (lowercase for matching) ──────────────────────────
MENU_ITEMS: set[str] = {
    # Appetizers
    "alu samosa",
    "samosa chaat",
    "aloo tikki chaat",
    "lamb samosa",
    "chicken samosa",
    "onion bhaji",
    "fish pakora",
    "chicken pakora",
    "assorted appetizers",
    "mixed vegetable pakora",
    "paneer pakora",
    "gobhi pakora",
    "wings",
    "paneer tikka",

    # Soup, Salad, Condiments
    "chicken soup",
    "mulgatani soup",
    "salad",
    "chicken salad",
    "raita",
    "papadum",
    "mango chutney",
    "mango pickle",

    # Chicken Curries
    "chicken tikka masala",
    "chicken korma",
    "butter chicken",
    "chicken coconut curry",
    "chicken chili",
    "chicken vindloo korma",
    "chicken curry",
    "chicken vindaloo",
    "karhai chicken",
    "chicken saag wala",
    "tofu tikka masala",

    # Lamb Curries
    "lamb tikka masala",
    "lamb shahi korma",
    "lamb coconut curry",
    "lamb vindloo korma",
    "saag lela",
    "lamb dopiaza",
    "karahi gosht",
    "rogan josh",
    "lamb vindaloo",
    "lamb curry",

    # Goat Curries
    "goat tikka masala",
    "goat korma",
    "goat makhni",
    "goat curry",
    "mint mutton",
    "goat coconut curry",

    # Tandoori Sizzlers
    "tandoori chicken",
    "chicken tikka",
    "vegan tandoori tikka",
    "lamb sheesh kabab",
    "mixed tandoori",
    "rack of lamb",
    "shrimp tandoori",
    "fish tandoori",

    # Seafood
    "shrimp saag",
    "shrimp masala",
    "fish tikka masala",
    "seafood curry",
    "seafood masala",
    "shrimp curry",
    "shrimp korma",
    "shrimp coconut curry",

    # Vegetarian Specialties
    "mushroom masala",
    "navratan korma",
    "shahi paneer",
    "paneer masala",
    "paneer makhni",
    "paneer karahi",
    "saag paneer",
    "malai kofta",
    "daal makhni",
    "mirch ka salan",
    "kadi pakora",
    "mix vegetable coconut curry",
    "saag alu",
    "alu gobhi",
    "bengan bhartha",
    "chana saag",
    "channa masala",
    "daal tudka",
    "alu bengan",
    "bhindi bhaji",

    # Breads
    "chapati tandoori",
    "naan",
    "paratha",
    "onion kulcha",
    "keema naan",
    "garlic naan",
    "garlic cheese naan",
    "alu paratha",
    "gobhi paratha",
    "spinach & cheese naan",
    "spinach and cheese naan",
    "puri",
    "cheese naan",
    "vegan garlic cheese naan",
    "basil naan",
    "peshwari naan",
    "indian cheese naan",

    # Desserts
    "rasmalai",
    "gulab jamun",
    "mango ice cream",
    "rice pudding",
    "kulfi",
    "carrot pudding",
    "mango malai",
    "almond ice cream",

    # Biryanis / Rice
    "shrimp biryani",
    "lamb biryani",
    "goat biryani",
    "chicken biryani",
    "plain rice",
    "rice pellow",
    "vegetables biryani",
    "brown rice",

    # Kids Menu
    "chicken popcorn",
    "chicken nuggets",
}

# Pre-built lookup: lowercased name → canonical display name
_LOOKUP: dict[str, str] = {name: name for name in MENU_ITEMS}


def _similarity(a: str, b: str) -> float:
    """Return SequenceMatcher ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


# Threshold for fuzzy match (0.0–1.0). 0.75 catches common AI transcription
# errors like "sherry" vs "shahi", "vindloo" vs "vindaloo", etc.
FUZZY_THRESHOLD = 0.75


def match_menu_item(item_name: str) -> tuple[str | None, float]:
    """
    Try to match an item name against the menu.

    Returns (matched_canonical_name, confidence).
    If no match meets the threshold, returns (None, best_score).
    """
    normalised = item_name.strip().lower()

    # Exact match
    if normalised in _LOOKUP:
        return normalised, 1.0

    # Fuzzy match — find the closest menu item
    best_name: str | None = None
    best_score: float = 0.0

    for menu_name in MENU_ITEMS:
        score = _similarity(normalised, menu_name)
        if score > best_score:
            best_score = score
            best_name = menu_name

    if best_score >= FUZZY_THRESHOLD:
        return best_name, best_score

    return None, best_score
