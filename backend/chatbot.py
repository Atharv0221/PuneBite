"""Keyword-based restaurant chatbot for PuneBite Analyzer (no AI model involved).

How it works, step by step (easy to explain in a viva):
  1. parse_message()  - reads the sentence with fixed rules (word lists + regular
                        expressions) and fills a "filters" dictionary: locality,
                        cuisine, price, rating, veg, amenities, type, ...
  2. build_query()    - turns the filters into a MongoDB query.
  3. chat_reply()     - runs the query, ranks results by trust-adjusted rating
                        (Phase 8), relaxes filters if nothing matches, and writes
                        a reply from templates.

The locality / cuisine / amenity names come from the database itself (load_vocab),
so the bot can only ever name restaurants that really exist.
"""
import re
import unicodedata
from difflib import get_close_matches

DEFAULT_RESULTS = 5
MAX_RESULTS = 10
CHEAP_MAX = 300          # 25th percentile of cost for two in our data
PREMIUM_MIN = 600        # roughly the top 15%
MID_RANGE = (300, 600)
GOOD_RATING = 3.5
HIGH_RATING = 4.0
POPULAR_MIN_VOTES = 100

PROJECTION = {
    "_id": 0, "name": 1, "url": 1, "locality": 1, "establishment_type": 1,
    "rating": 1, "trust_rating": 1, "votes": 1, "cost_for_two": 1,
    "cuisines": 1, "hidden_gem": 1, "cluster_name": 1,
}

# ----------------------------------------------------------------- word lists
# phrase typed by the user -> cuisine name (used only if that cuisine exists in the DB)
CUISINE_ALIASES = {
    "biriyani": "Biryani", "briyani": "Biryani", "dosa": "South Indian",
    "idli": "South Indian", "uttapam": "South Indian", "vada pav": "Street Food",
    "pav bhaji": "Street Food", "chaat": "Street Food", "icecream": "Ice Cream",
    "gelato": "Ice Cream", "dessert": "Desserts", "sweets": "Mithai",
    "barbecue": "BBQ", "barbeque": "BBQ", "bbq": "BBQ", "coffee shop": "Coffee",
    "juice": "Juices", "momo": "Momos", "punjabi": "North Indian",
    "chinese food": "Chinese", "italian food": "Italian", "healthy": "Healthy Food",
    "cafes": "Cafe", "coffee": "Coffee", "pastry": "Bakery", "cake": "Bakery",
    "cakes": "Bakery", "wrap": "Wraps", "shawarma": "Arabian", "sushi": "Sushi",
    "pasta": "Italian", "risotto": "Italian", "lasagna": "Italian", "noodle": "Chinese",
    "manchurian": "Chinese", "fried rice": "Chinese", "misal": "Maharashtrian",
    "paneer": "North Indian", "tandoori": "North Indian", "ramen": "Japanese",
    "waffle": "Desserts", "brownie": "Desserts", "kebab": "Kebab", "thali": "North Indian",
}

# phrase -> list of amenity tokens (any one of them is enough). Tokens that do not
# exist in the database are dropped automatically.
AMENITY_ALIASES = {
    "parking": ["free_parking", "mall_parking", "valet_parking_available"],
    "valet": ["valet_parking_available"],
    "wifi": ["wifi", "free_wifi"], "wi fi": ["wifi", "free_wifi"],
    "outdoor": ["outdoor_seating"], "open air": ["outdoor_seating"],
    "roof top": ["rooftop"], "rooftop": ["rooftop"],
    "live music": ["live_music"], "live band": ["live_music"],
    "drinks": ["full_bar_available", "serves_cocktails"],
    "alcohol": ["full_bar_available"], "beer": ["full_bar_available"],
    "liquor": ["full_bar_available"], "cocktail": ["serves_cocktails"],
    "full bar": ["full_bar_available"],
    "kids": ["kid_friendly"], "kid friendly": ["kid_friendly"],
    "children": ["kid_friendly"], "pet friendly": ["pet_friendly"],
    "pets": ["pet_friendly"], "dog": ["pet_friendly"],
    "delivery": ["home_delivery"], "home delivery": ["home_delivery"],
    "table booking": ["table_booking_recommended"],
    "reservation": ["table_booking_recommended"],
    "reserve": ["table_booking_recommended"],
    "buffet": ["buffet"], "brunch": ["brunch"],
    "breakfast": ["breakfast", "all_day_breakfast"],
    "nightlife": ["nightlife"], "night life": ["nightlife"], "party": ["nightlife"],
    "jain": ["serves_jain_food"], "wheelchair": ["wheelchair_accessible"],
    "sports": ["live_sports_screening"], "smoking": ["smoking_are"],
}
AMENITY_LABELS = {  # friendlier words for the "I understood" line
    "free_parking": "parking", "wifi": "wifi", "outdoor_seating": "outdoor seating",
    "rooftop": "rooftop", "live_music": "live music", "full_bar_available": "bar",
    "kid_friendly": "kid friendly", "pet_friendly": "pet friendly",
    "home_delivery": "home delivery", "table_booking_recommended": "table booking",
    "buffet": "buffet", "brunch": "brunch", "breakfast": "breakfast",
    "nightlife": "nightlife", "serves_jain_food": "jain food",
    "wheelchair_accessible": "wheelchair access", "live_sports_screening": "sports screening",
    "smoking_are": "smoking area", "vegan_options": "vegan options",
    "vegetarian_only": "pure veg",
}
# phrase -> regular expression matched against establishment_type
TYPE_WORDS = {
    "pub": "Pub", "bar": "Bar", "lounge": "Lounge", "dhaba": "Dhaba",
    "food court": "Food Court",
    "microbrewery": "Microbrewery", "brewery": "Microbrewery",
    "food truck": "Food Truck", "dessert parlor": "Dessert Parlor",
    "dessert parlour": "Dessert Parlor", "sweet shop": "Sweet Shop",
    "mess": "Mess", "casual dining": "Casual Dining", "quick bites": "Quick Bites",
}
CHEAP_WORDS = ["cheap", "budget", "affordable", "inexpensive", "economical",
               "pocket friendly", "low cost", "low price", "low budget"]
PREMIUM_WORDS = ["expensive", "premium", "fancy", "luxury", "luxurious", "high end",
                 "upscale", "costly", "pricey", "posh", "fine dining"]
MID_WORDS = ["mid range", "midrange", "moderate", "moderately priced", "medium budget"]
GEM_WORDS = ["hidden gem", "hidden gems", "gem", "gems", "underrated", "offbeat",
             "lesser known", "undiscovered", "hidden"]
POPULAR_WORDS = ["popular", "famous", "crowded", "most reviewed", "busy", "trending"]
GOOD_WORDS = ["good", "nice", "decent"]
HIGH_WORDS = ["highly rated", "top rated", "excellent", "amazing", "great", "best rated"]
WORST_WORDS = ["worst", "lowest rated", "poorly rated", "bad"]
CHEAPEST_WORDS = ["cheapest", "lowest price"]
GREETINGS = ["hi", "hello", "hey", "namaste", "good morning", "good evening",
             "thanks", "thank you", "bye"]
HELP_WORDS = ["help", "what can you do", "how to use", "how do i use", "examples"]
COUNT_WORDS = ["how many", "number of", "count of", "count"]
SEARCH_HINTS = ["best", "top", "restaurant", "restaurants", "place", "places", "food",
                "eat", "eating", "recommend", "suggest", "show", "find", "list",
                "hungry", "cafe", "dinner", "lunch"]
UNSUPPORTED = [
    (["open now", "open late", "late night", "dinner", "lunch", "timing", "timings"],
     "I can't filter by opening hours yet."),
    (["near me", "nearby", "close to me", "around me"],
     "I don't know where you are, so please name a locality."),
]
STOP = set("""the a an in at near around for of to and or with me my some any is are
best top good great nice cheap budget place places restaurant restaurants food
show find give list suggest recommend want need looking please under above over
below rated rating stars star than less more under at least
""".split())


# ------------------------------------------------------------------ text tools
def normalise(text):
    """Lower-case, strip accents and currency words, keep letters/digits/decimals."""
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    t = t.lower().replace("&", " ")
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)               # 1,000 -> 1000
    t = re.sub(r"(?<=\d)\s*-\s*(?=\d)", " to ", t)       # 300-500 -> 300 to 500
    t = re.sub(r"\b(?:rs|inr|rupees?)\b\.?", " ", t)       # currency words
    t = re.sub(r"[^a-z0-9.+\s]", " ", t)
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _phrase_re(phrase, plural=True):
    tail = r"(?:e?s)?" if plural else ""
    return re.compile(rf"(?<![a-z0-9]){re.escape(phrase)}{tail}(?![a-z0-9])")


def _find(text, phrase, plural=True):
    """Return (start, end) of the phrase in text, or None."""
    m = _phrase_re(phrase, plural).search(text)
    return m.span() if m else None


def _blank(text, span):
    return text[:span[0]] + " " * (span[1] - span[0]) + text[span[1]:]


def _any(text, words):
    return any(_find(text, w) for w in words)


def _number(s):
    s = s.replace(",", "")
    return float(s)


# ------------------------------------------------------------------- vocabulary
def build_vocab(localities, cuisines, amenities):
    """Prepare lookup tables from the real names stored in the database."""
    locs = {}
    for name in localities:
        if not name or name == "Around Pune":      # 'around pune' is also a normal phrase
            continue
        locs[normalise(name)] = name
    cuis = {normalise(c): c for c in cuisines if c}
    ams = {a for a in amenities if a}
    amenity_phrases = {}
    for a in ams:                                   # auto-phrase: free_parking -> "free parking"
        phrase = a.replace("_", " ")
        if len(phrase) >= 6 and a not in ("indoor_seating", "seating_not_available",
                                           "no_alcohol_available", "home_baker"):
            amenity_phrases[phrase] = [a]
    for phrase, tokens in AMENITY_ALIASES.items():
        keep = [t for t in tokens if t in ams]
        if keep:
            amenity_phrases[phrase] = keep
    group_alias = {  # a few shortcuts that mean several localities
        "kp": ["Koregaon Park", "KP and Kalyani"], "deccan": ["Deccan Gymkhana", "Deccan & Peths"],
        "pcmc": ["Pimpri", "Chinchwad", "Pimpri Chinchwad Area"],
        "shivajinagar": ["Shivaji Nagar"], "hinjewadi": ["Hinjawadi"],
    }
    loc_alias = {k: [x for x in v if x in set(localities)] for k, v in group_alias.items()}
    return {
        "localities": locs, "cuisines": cuis, "amenities": ams,
        "amenity_phrases": amenity_phrases,
        "locality_alias": {k: v for k, v in loc_alias.items() if v},
        "cuisine_alias": {k: v for k, v in CUISINE_ALIASES.items() if normalise(v) in cuis},
    }


def load_vocab(coll):
    """Read the real locality / cuisine / amenity names from MongoDB."""
    return build_vocab(coll.distinct("locality"), coll.distinct("cuisines"),
                       coll.distinct("amenities"))


# ----------------------------------------------------------------------- parser
def _extract_locality(text, vocab):
    names = sorted(vocab["locality_alias"], key=len, reverse=True)
    for alias in names:
        span = _find(text, alias, plural=False)
        if span:
            return vocab["locality_alias"][alias], _blank(text, span)
    for norm in sorted(vocab["localities"], key=len, reverse=True):
        span = _find(text, norm, plural=False)
        if span:
            name = vocab["localities"][norm]
            group = [name] + [v for k, v in vocab["localities"].items() if k == norm + " area"]
            return group, _blank(text, span)
    return [], text


def _fuzzy(text, table):
    """Typo tolerance: compare leftover 1-2 word chunks with the vocabulary."""
    tokens = [(m.group(), m.span()) for m in re.finditer(r"[a-z]+", text)]
    keys = list(table)
    hits = []
    for size in (2, 1):
        for i in range(len(tokens) - size + 1):
            chunk = tokens[i:i + size]
            words = [w for w, _ in chunk]
            if any(w in STOP for w in words) or len(" ".join(words)) < 5:
                continue
            same_len = [k for k in keys if len(k.split()) == size]
            near = get_close_matches(" ".join(words), same_len, n=1, cutoff=0.84)
            if near:
                hits.append((table[near[0]], (chunk[0][1][0], chunk[-1][1][1])))
    return hits


def parse_message(message, vocab):
    """Turn a sentence into a dictionary of filters (the heart of the chatbot)."""
    text = normalise(message)
    f = {
        "text": text, "intent": "search", "localities": [], "cuisines": [],
        "veg": False, "amenity_groups": [], "types": [], "min_cost": None,
        "max_cost": None, "min_rating": None, "min_votes": None, "gem": False,
        "sort": "trust", "limit": DEFAULT_RESULTS, "notes": [], "typo_fixed": [],
    }
    if _any(text, COUNT_WORDS):
        f["intent"] = "count"
    for words, note in UNSUPPORTED:
        if _any(text, words):
            f["notes"].append(note)

    for greeting in ("good morning", "good afternoon", "good evening", "good night"):
        text = text.replace(greeting, " " * len(greeting))      # not a rating request

    # 1. locality
    f["localities"], text = _extract_locality(text, vocab)

    # 2. rating written as a number (numbers 1-5) - before prices so "above 4" is a rating
    rating_patterns = [
        r"(?:above|over|atleast|at least|minimum|min|more than|greater than|better than)\s+(\d(?:\.\d)?)(?!\d|k\b)\s*(?:star|stars|rating|rated)?",
        r"(?<![\d.])(\d(?:\.\d)?)\s*\+",
        r"(?<![\d.])(\d(?:\.\d)?)\s*(?:star|stars)\b",
        r"(?:rated|rating(?: of| is)?)\s*(\d(?:\.\d)?)(?!\d)",
    ]
    for pat in rating_patterns:
        m = re.search(pat, text)
        if m and 1 <= float(m.group(1)) <= 5:
            f["min_rating"] = float(m.group(1))
            text = _blank(text, m.span())
            break

    # 3. price written as a number (50 and above)
    amt = r"(\d+(?:\.\d+)?)\s*(k\b)?"
    def val(m, i=1):
        return _number(m.group(i)) * (1000 if m.group(i + 1) else 1)
    m = re.search(rf"(?:between|from)?\s*{amt}\s*(?:to|and|-)\s*{amt}", text)
    if m and val(m) >= 50 and val(m, 3) >= 50 and ("between" in m.group() or "from" in m.group() or "to" in m.group()):
        lo, hi = sorted((val(m), val(m, 3)))
        f["min_cost"], f["max_cost"] = lo, hi
        text = _blank(text, m.span())
    else:
        for pat, key in [
            (rf"(?:under|below|less than|within|upto|up to|max|maximum|at most|not more than|budget of|budget is|lower than)\s*{amt}", "max_cost"),
            (rf"(?:above|over|more than|at least|atleast|minimum|min|greater than)\s*{amt}", "min_cost"),
        ]:
            m = re.search(pat, text)
            if m and val(m) >= 50:
                f[key] = val(m)
                text = _blank(text, m.span())
        m = re.search(rf"(?:around|about|approx|approximately|roughly|nearly)\s*{amt}|{amt}\s*for two|for two\s*{amt}", text)
        if m and f["min_cost"] is None and f["max_cost"] is None:
            groups = [(1, 2), (3, 4), (5, 6)]
            for a, b in groups:
                if m.group(a):
                    n = _number(m.group(a)) * (1000 if m.group(b) else 1)
                    if n >= 50:
                        f["min_cost"], f["max_cost"] = round(n * 0.75), round(n * 1.25)
                        text = _blank(text, m.span())
                    break

    # 4. how many results ("top 3", "5 places")
    m = re.search(r"\btop\s+(\d{1,2})\b", text) or re.search(
        r"\b(\d{1,2})\s+(?:\w+\s+){0,2}(?:restaurants?|places|options|spots|cafes|joints|suggestions)\b", text)
    if m and 1 <= int(m.group(1)) <= MAX_RESULTS:
        f["limit"] = int(m.group(1))
        text = _blank(text, m.span(1))

    # 5. cuisines (exact name, alias, then typo-tolerant)
    for alias, target in sorted(vocab["cuisine_alias"].items(), key=lambda kv: -len(kv[0])):
        span = _find(text, alias)
        if span:
            if target not in f["cuisines"]:
                f["cuisines"].append(target)
            text = _blank(text, span)
    for norm in sorted(vocab["cuisines"], key=len, reverse=True):
        span = _find(text, norm)
        if span:
            if vocab["cuisines"][norm] not in f["cuisines"]:
                f["cuisines"].append(vocab["cuisines"][norm])
            text = _blank(text, span)

    # 6. vegetarian
    m = re.search(r"(?<![a-z])non\s*veg(?:etarian)?\b", text)
    if m:
        text = _blank(text, m.span())
    m = re.search(r"(?<![a-z])(?:pure\s+)?veg(?:etarian|gie|gies|an)?(?![a-z])", text)
    if m and m.group().strip().endswith("vegan") and "vegan_options" in vocab["amenities"]:
        f["amenity_groups"].append(["vegan_options"])
        text = _blank(text, m.span())
    elif m and "vegetarian_only" in vocab["amenities"]:
        f["veg"] = True
        text = _blank(text, m.span())

    # 7. amenities
    for phrase in sorted(vocab["amenity_phrases"], key=len, reverse=True):
        span = _find(text, phrase)
        if span:
            group = vocab["amenity_phrases"][phrase]
            if group not in f["amenity_groups"]:
                f["amenity_groups"].append(group)
            text = _blank(text, span)

    # 8. restaurant type
    for phrase in sorted(TYPE_WORDS, key=len, reverse=True):
        span = _find(text, phrase)
        if span:
            if TYPE_WORDS[phrase] not in f["types"]:
                f["types"].append(TYPE_WORDS[phrase])
            text = _blank(text, span)

    # 9. descriptive words
    def has(words):
        nonlocal text
        for w in sorted(words, key=len, reverse=True):
            span = _find(text, w, plural=False)
            if span:
                text = _blank(text, span)
                return True
        return False
    if has(CHEAPEST_WORDS):
        f["sort"] = "cheapest"
    if has(CHEAP_WORDS) and f["max_cost"] is None and f["min_cost"] is None:
        f["max_cost"] = CHEAP_MAX
    if has(PREMIUM_WORDS) and f["max_cost"] is None and f["min_cost"] is None:
        f["min_cost"] = PREMIUM_MIN
    if has(MID_WORDS) and f["max_cost"] is None and f["min_cost"] is None:
        f["min_cost"], f["max_cost"] = MID_RANGE
    if has(GEM_WORDS):
        f["gem"] = True
    if has(POPULAR_WORDS):
        f["sort"], f["min_votes"] = "popular", POPULAR_MIN_VOTES
    if has(HIGH_WORDS) and f["min_rating"] is None:
        f["min_rating"] = HIGH_RATING
    if has(GOOD_WORDS) and f["min_rating"] is None:
        f["min_rating"] = GOOD_RATING
    if has(WORST_WORDS):
        f["sort"] = "worst"

    # 10. typo tolerance on whatever is left over
    if not f["localities"]:
        hits = _fuzzy(text, vocab["localities"])
        if hits:
            name, span = hits[0]
            f["localities"] = [name] + [v for k, v in vocab["localities"].items() if k == normalise(name) + " area"]
            f["typo_fixed"].append(name)
            text = _blank(text, span)
    for name, span in _fuzzy(text, vocab["cuisines"]):
        if name not in f["cuisines"]:
            f["cuisines"].append(name)
            f["typo_fixed"].append(name)
            text = _blank(text, span)

    # 11. is this a greeting / help request, or a search?
    original = normalise(message)
    has_filters = bool(f["localities"] or f["cuisines"] or f["veg"] or f["amenity_groups"]
                       or f["types"] or f["min_cost"] or f["max_cost"] or f["min_rating"]
                       or f["gem"] or f["min_votes"])
    f["has_filters"] = has_filters
    if not has_filters:
        if _any(original, HELP_WORDS):
            f["intent"] = "help"
        elif _any(original, GREETINGS) and len(original.split()) <= 4:
            f["intent"] = "greeting"
        elif not _any(original, SEARCH_HINTS):
            f["intent"] = "unknown"
    f["text"] = original
    return f


# ------------------------------------------------------------------ query builder
def build_query(f, rated_only=True):
    """Filters -> MongoDB query (plain dictionary)."""
    q, ands = {}, []
    if rated_only:
        q["trust_rating"] = {"$ne": None}
    if f["localities"]:
        q["locality"] = {"$in": f["localities"]} if len(f["localities"]) > 1 else f["localities"][0]
    if f["cuisines"]:
        q["cuisines"] = {"$in": f["cuisines"]} if len(f["cuisines"]) > 1 else f["cuisines"][0]
    cost = {}
    if f["min_cost"] is not None:
        cost["$gte"] = f["min_cost"]
    if f["max_cost"] is not None:
        cost["$lte"] = f["max_cost"]
    if f["sort"] == "cheapest":
        cost.setdefault("$gt", 0)          # leave out restaurants with no known price
    if cost:
        q["cost_for_two"] = cost           # real price, not the filled-in one
    if f["min_rating"] is not None:
        q["rating"] = {"$gte": f["min_rating"]}
    if f["min_votes"] is not None:
        q["votes"] = {"$gte": f["min_votes"]}
    if f["sort"] == "worst" and "votes" not in q:
        q["votes"] = {"$gte": 20}          # a 1.0 from 2 votes is not "the worst"
    if f["gem"]:
        q["hidden_gem"] = True
    if f["veg"]:
        ands.append({"amenities": "vegetarian_only"})
    for group in f["amenity_groups"]:
        ands.append({"amenities": {"$in": group}})
    for t in f["types"]:
        ands.append({"establishment_type": {"$regex": rf"\b{t}\b", "$options": "i"}})
    if ands:
        q["$and"] = ands
    return q


def sort_spec(f):
    return {
        "trust": [("trust_rating", -1), ("votes", -1)],
        "popular": [("votes", -1), ("trust_rating", -1)],
        "worst": [("trust_rating", 1), ("votes", -1)],
        "cheapest": [("cost_for_two", 1), ("trust_rating", -1)],
    }[f["sort"]]


# ----------------------------------------------------------------------- replies
def _money(n):
    return f"₹{int(n):,}"


def understood(f):
    """The filters the bot read from the sentence, as short labels."""
    out = []
    if f["localities"]:
        out.append(f"Locality: {f['localities'][0]}")
    if f["cuisines"]:
        out.append("Cuisine: " + ", ".join(f["cuisines"]))
    if f["types"]:
        out.append("Type: " + ", ".join(f["types"]))
    if f["veg"]:
        out.append("Pure veg")
    for g in f["amenity_groups"]:
        out.append("Has: " + AMENITY_LABELS.get(g[0], g[0].replace("_", " ")))
    if f["min_cost"] is not None and f["max_cost"] is not None:
        out.append(f"Cost for two: {_money(f['min_cost'])} to {_money(f['max_cost'])}")
    elif f["max_cost"] is not None:
        out.append(f"Cost for two: up to {_money(f['max_cost'])}")
    elif f["min_cost"] is not None:
        out.append(f"Cost for two: {_money(f['min_cost'])} or more")
    if f["min_rating"] is not None:
        out.append(f"Rating: {f['min_rating']:g}+")
    if f["min_votes"] is not None:
        out.append(f"Votes: {f['min_votes']}+")
    if f["gem"]:
        out.append("Hidden gems only")
    return out


def describe(f, singular=False):
    """A short phrase such as 'veg biryani places in Baner under ₹500'."""
    kind = " / ".join(f["cuisines"]) if f["cuisines"] else ""
    if f["types"]:
        kind = (kind + " " + "/".join(t.lower() for t in f["types"])).strip()
    if f["veg"]:
        kind = ("veg " + kind).strip()
    if f["gem"]:
        kind = ("hidden-gem " + kind).strip()
    noun = ("place" if singular else "places") if kind else ("restaurant" if singular else "restaurants")
    phrase = (kind + " " + noun).strip() if kind else noun
    if f["localities"]:
        phrase += f" in {f['localities'][0]}"
    if f["min_cost"] is not None and f["max_cost"] is not None:
        phrase += f" costing {_money(f['min_cost'])}-{_money(f['max_cost'])} for two"
    elif f["max_cost"] is not None:
        phrase += f" under {_money(f['max_cost'])} for two"
    elif f["min_cost"] is not None:
        phrase += f" above {_money(f['min_cost'])} for two"
    if f["min_rating"] is not None:
        phrase += f" rated {f['min_rating']:g}+"
    return phrase


HELP_TEXT = (
    "I can find Pune restaurants using the data in this project. Tell me what you want, "
    "for example: 'best cheap biryani in Kothrud', 'veg restaurants in Baner under 500', "
    "'hidden gems in Koregaon Park', 'top 3 cafes with wifi in Viman Nagar' or "
    "'how many Chinese places in Hadapsar'. I understand locality, cuisine, price, "
    "rating, veg, amenities (parking, wifi, live music...) and type (bar, pub, dhaba...)."
)

# order in which filters are dropped when nothing matches: (label, keys to reset)
RELAX_STEPS = [
    ("the minimum votes", {"min_votes": None}),
    ("the rating requirement", {"min_rating": None}),
    ("the price limit", {"min_cost": None, "max_cost": None}),
    ("the amenity requirement", {"amenity_groups": []}),
    ("the restaurant type", {"types": []}),
]


def _card(doc):
    """Make a database row JSON-friendly for the frontend."""
    return {k: doc.get(k) for k in PROJECTION if k != "_id"}


def chat_reply(message, coll, vocab):
    """Main entry point: message in, reply dictionary out."""
    f = parse_message(message, vocab)
    base = {"intent": f["intent"], "understood": understood(f), "restaurants": [],
            "total": 0, "relaxed": [], "notes": f["notes"]}

    if f["intent"] == "help":
        return {**base, "reply": HELP_TEXT}
    if f["intent"] == "greeting":
        return {**base, "reply": "Hello! " + HELP_TEXT}
    if f["intent"] == "unknown":
        return {**base, "reply": "Sorry, I didn't catch what you are looking for. " + HELP_TEXT}

    notes = (" " + " ".join(f["notes"])) if f["notes"] else ""
    typo = (f" (I read that as {', '.join(f['typo_fixed'])}.)") if f["typo_fixed"] else ""

    if f["intent"] == "count":
        total = coll.count_documents(build_query(f, rated_only=False))
        top = list(coll.find(build_query(f), PROJECTION).sort(sort_spec(f)).limit(3))
        reply = f"There are {total:,} {describe(f)} in the dataset.{typo}"
        if top:
            reply += " The three best by trust-adjusted rating are listed below."
        return {**base, "reply": reply + notes, "total": total,
                "restaurants": [_card(d) for d in top]}

    work = dict(f)
    query = build_query(work)
    total = coll.count_documents(query)
    relaxed = []
    for label, reset in RELAX_STEPS:
        if total:
            break
        if any(work[k] not in (None, [], False) for k in reset):
            work.update(reset)
            relaxed.append(label)
            query = build_query(work)
            total = coll.count_documents(query)

    if not total:
        hint = ("Hidden gems are the top 15% of a locality with 20-200 votes, so some areas have none. "
                if f["gem"] else "")
        return {**base, "reply": f"I couldn't find any {describe(f)}.{typo} {hint}Try a different "
                                 "locality or cuisine, or ask for something broader." + notes}

    docs = list(coll.find(query, PROJECTION).sort(sort_spec(work)).limit(f["limit"]))
    shown = len(docs)
    ranking = {"trust": "ranked by trust-adjusted rating",
               "popular": "ranked by number of votes",
               "worst": "lowest trust-adjusted rating first (20+ votes)",
               "cheapest": "cheapest first"}[f["sort"]]
    reply = f"Here {'is' if shown == 1 else 'are'} {shown} {describe(work, singular=shown == 1)}, {ranking}.{typo}"
    if not f["has_filters"]:
        reply = ("I didn't pick up a locality, cuisine or price in that, so these are the "
                 "top-rated restaurants overall. " + reply)
    if relaxed:
        reply = (f"I found nothing that matched everything, so I dropped {' and '.join(relaxed)}. "
                 + reply)
    if total > shown:
        reply += f" ({total:,} match in total.)"
    return {**base, "reply": reply + notes, "restaurants": [_card(d) for d in docs],
            "total": total, "relaxed": relaxed}
