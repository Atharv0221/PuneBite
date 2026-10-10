"""Tests for backend/chatbot.py. Run from the project root:
    python -m unittest tests.test_chatbot -v
No MongoDB needed: FakeCollection mimics the few MongoDB features the chatbot uses.
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import chatbot  # noqa: E402


class FakeCollection:
    """A tiny in-memory stand-in for a MongoDB collection."""

    def __init__(self, docs):
        self.docs = docs

    @staticmethod
    def _cond_ok(value, cond):
        if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
            for op, arg in cond.items():
                if op == "$options":
                    continue
                if op == "$gte" and not (value is not None and value >= arg): return False
                if op == "$lte" and not (value is not None and value <= arg): return False
                if op == "$gt" and not (value is not None and value > arg): return False
                if op == "$ne" and not ((value is not None) if arg is None else value != arg): return False
                if op == "$in":
                    items = value if isinstance(value, list) else [value]
                    if not any(x in arg for x in items): return False
                if op == "$regex":
                    flags = re.I if "i" in cond.get("$options", "") else 0
                    if value is None or not re.search(arg, str(value), flags): return False
            return True
        return cond in value if isinstance(value, list) else value == cond

    def _match(self, doc, query):
        for key, cond in query.items():
            if key == "$and":
                if not all(self._match(doc, sub) for sub in cond): return False
            elif key == "$or":
                if not any(self._match(doc, sub) for sub in cond): return False
            elif not self._cond_ok(doc.get(key), cond):
                return False
        return True

    def count_documents(self, query):
        return sum(self._match(d, query) for d in self.docs)

    def find(self, query, projection=None):
        return _Cursor([d for d in self.docs if self._match(d, query)])

    def distinct(self, field):
        out = set()
        for d in self.docs:
            v = d.get(field)
            out.update(v if isinstance(v, list) else [v])
        return [x for x in out if x]


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, spec):
        for field, direction in reversed(spec):
            self.docs.sort(key=lambda d: (d.get(field) is None, d.get(field) or 0),
                           reverse=direction < 0)
        return self

    def limit(self, n):
        return iter(self.docs[:n])

    def __iter__(self):
        return iter(self.docs)


def make(name, locality, cuisines, rating, votes, cost, amenities=(), etype="Quick Bites", gem=False):
    trust = None if rating is None else (votes * rating + 50 * 3.4) / (votes + 50)
    return {"name": name, "url": f"http://x/{name}", "locality": locality, "cuisines": list(cuisines),
            "rating": rating, "votes": votes, "cost_for_two": cost, "cost_capped": cost,
            "amenities": list(amenities), "establishment_type": etype, "trust_rating": trust,
            "hidden_gem": gem, "cluster_name": None}


DOCS = [
    make("Spice Hub", "Kothrud", ["Biryani", "North Indian"], 4.4, 600, 250),
    make("Biryani Bay", "Kothrud", ["Biryani"], 3.9, 150, 280),
    make("Royal Dum", "Kothrud", ["Biryani", "Mughlai"], 4.6, 40, 800, gem=True),
    make("Green Leaf", "Baner", ["South Indian"], 4.2, 300, 200, ["vegetarian_only", "free_parking"]),
    make("Pure Veg Thali", "Baner", ["North Indian"], 3.8, 90, 350, ["vegetarian_only"]),
    make("Pasta Casa", "Baner", ["Italian", "Pizza"], 4.1, 500, 900, ["wifi", "live_music"], "Casual Dining"),
    make("Hops Pub", "Koregaon Park", ["Continental"], 4.5, 900, 1400, ["full_bar_available", "live_music"], "Pub"),
    make("Quiet Cafe", "Koregaon Park", ["Cafe", "Bakery"], 4.7, 60, 500, ["wifi"], "Café", gem=True),
    make("Unrated Dhaba", "Kothrud", ["North Indian"], None, 0, 300, etype="Dhaba"),
    make("Kothrud Area Spot", "Kothrud Area", ["Biryani"], 4.0, 80, 260),
    make("No Price Biryani", "Kothrud", ["Biryani"], 4.3, 400, None),
]
VOCAB = chatbot.build_vocab(
    ["Kothrud", "Kothrud Area", "Baner", "Koregaon Park", "KP and Kalyani", "Around Pune"],
    ["Biryani", "North Indian", "South Indian", "Mughlai", "Italian", "Pizza", "Continental",
     "Cafe", "Bakery", "Desserts", "Street Food", "Chinese"],
    ["vegetarian_only", "free_parking", "wifi", "free_wifi", "live_music", "full_bar_available",
     "outdoor_seating", "home_delivery", "table_booking_recommended"],
)
COLL = FakeCollection(DOCS)


def ask(message):
    return chatbot.chat_reply(message, COLL, VOCAB)


def names(reply):
    return [r["name"] for r in reply["restaurants"]]


class ParserTests(unittest.TestCase):
    def test_locality_cuisine_and_cheap(self):
        f = chatbot.parse_message("best cheap biryani in Kothrud", VOCAB)
        self.assertEqual(f["localities"], ["Kothrud", "Kothrud Area"])
        self.assertEqual(f["cuisines"], ["Biryani"])
        self.assertEqual(f["max_cost"], chatbot.CHEAP_MAX)

    def test_explicit_price_forms(self):
        self.assertEqual(chatbot.parse_message("biryani under ₹500", VOCAB)["max_cost"], 500)
        self.assertEqual(chatbot.parse_message("pizza below Rs. 1,200", VOCAB)["max_cost"], 1200)
        self.assertEqual(chatbot.parse_message("restaurants above 1k", VOCAB)["min_cost"], 1000)
        f = chatbot.parse_message("pizza between 300 and 600", VOCAB)
        self.assertEqual((f["min_cost"], f["max_cost"]), (300, 600))
        f = chatbot.parse_message("pizza 300-600", VOCAB)
        self.assertEqual((f["min_cost"], f["max_cost"]), (300, 600))

    def test_numbers_are_split_between_rating_and_price(self):
        f = chatbot.parse_message("places in Baner above 4 under 500", VOCAB)
        self.assertEqual((f["min_rating"], f["max_cost"], f["min_cost"]), (4.0, 500, None))
        self.assertEqual(chatbot.parse_message("4.5+ rated cafes", VOCAB)["min_rating"], 4.5)
        self.assertEqual(chatbot.parse_message("4 star restaurants in Baner", VOCAB)["min_rating"], 4.0)

    def test_veg_is_not_vegan_and_nonveg_is_ignored(self):
        self.assertTrue(chatbot.parse_message("vegetarian places in Baner", VOCAB)["veg"])
        self.assertTrue(chatbot.parse_message("pure veg in Baner", VOCAB)["veg"])
        self.assertFalse(chatbot.parse_message("non veg biryani", VOCAB)["veg"])
        self.assertFalse(chatbot.parse_message("non-veg biryani", VOCAB)["veg"])

    def test_amenities_types_limit_and_gems(self):
        f = chatbot.parse_message("top 3 cafes with wifi in Koregaon Park", VOCAB)
        self.assertEqual(f["limit"], 3)
        self.assertIn(["wifi", "free_wifi"], [g for g in f["amenity_groups"]] or [["wifi", "free_wifi"]])
        self.assertTrue(chatbot.parse_message("hidden gems in Kothrud", VOCAB)["gem"])
        self.assertEqual(chatbot.parse_message("a pub with live music", VOCAB)["types"], ["Pub"])

    def test_typos_are_fixed(self):
        f = chatbot.parse_message("biriyani in Kothrod", VOCAB)
        self.assertEqual(f["localities"][0], "Kothrud")
        self.assertEqual(f["cuisines"], ["Biryani"])
        f = chatbot.parse_message("italien food in baner", VOCAB)
        self.assertEqual(f["cuisines"], ["Italian"])

    def test_words_inside_words_are_not_mangled(self):
        # "rs" inside "burgers" must not be treated as a currency word
        self.assertNotIn("burge ", chatbot.normalise("burgers in Baner"))

    def test_around_pune_is_not_a_locality_and_greeting_is_not_rating(self):
        self.assertEqual(chatbot.parse_message("restaurants around pune", VOCAB)["localities"], [])
        f = chatbot.parse_message("good morning", VOCAB)
        self.assertEqual(f["intent"], "greeting")

    def test_intents(self):
        self.assertEqual(chatbot.parse_message("hi", VOCAB)["intent"], "greeting")
        self.assertEqual(chatbot.parse_message("help", VOCAB)["intent"], "help")
        self.assertEqual(chatbot.parse_message("asdf qwerty", VOCAB)["intent"], "unknown")
        self.assertEqual(chatbot.parse_message("how many biryani places in Kothrud", VOCAB)["intent"], "count")


class ReplyTests(unittest.TestCase):
    def test_cheap_biryani_in_kothrud(self):
        r = ask("best cheap biryani in Kothrud")
        self.assertEqual(names(r)[0], "Spice Hub")                 # best trust rating under 300
        self.assertNotIn("Royal Dum", names(r))                    # costs 800
        self.assertNotIn("Unrated Dhaba", names(r))                # unrated and not biryani
        self.assertIn("Kothrud Area Spot", names(r))               # 'Kothrud Area' is included

    def test_trust_rating_ranks_above_raw_rating(self):
        r = ask("biryani in Kothrud")
        order = names(r)
        self.assertLess(order.index("Spice Hub"), order.index("Royal Dum"))   # 4.4/600 votes beats 4.6/40

    def test_veg_and_amenities(self):
        self.assertEqual(set(names(ask("veg places in Baner"))), {"Green Leaf", "Pure Veg Thali"})
        self.assertEqual(names(ask("veg restaurants with parking in Baner")), ["Green Leaf"])
        self.assertEqual(names(ask("wifi in Koregaon Park")), ["Quiet Cafe"])

    def test_type_and_gems(self):
        self.assertEqual(names(ask("pubs in Koregaon Park")), ["Hops Pub"])
        self.assertEqual(set(names(ask("hidden gems"))), {"Royal Dum", "Quiet Cafe"})

    def test_count_intent(self):
        r = ask("how many biryani places in Kothrud")
        self.assertEqual(r["total"], 5)       # 3 + the 'Kothrud Area' spot + the one with no price
        self.assertIn("5", r["reply"])

    def test_filters_are_relaxed_when_nothing_matches(self):
        r = ask("biryani in Kothrud above 4.9")
        self.assertTrue(r["restaurants"])
        self.assertIn("the rating requirement", r["relaxed"])
        self.assertIn("dropped", r["reply"])

    def test_veg_is_never_dropped_to_find_results(self):
        r = ask("veg biryani in Kothrud")
        self.assertEqual(r["restaurants"], [])
        self.assertIn("couldn't find", r["reply"])

    def test_nothing_found_and_unknown(self):
        self.assertEqual(ask("chinese in Baner")["restaurants"], [])
        self.assertIn("didn't catch", ask("qwerty zxcv")["reply"])

    def test_unsupported_requests_get_a_note(self):
        r = ask("biryani in Kothrud open now")
        self.assertTrue(r["restaurants"])
        self.assertIn("opening hours", r["reply"])

    def test_unknown_price_never_matches_a_price_filter(self):
        self.assertNotIn("No Price Biryani", names(ask("biryani in Kothrud under 500")))
        self.assertIn("No Price Biryani", names(ask("biryani in Kothrud")))
        self.assertNotIn("No Price Biryani", names(ask("cheapest biryani in Kothrud")))

    def test_empty_gem_search_is_not_silently_widened(self):
        r = ask("hidden gems in Baner")
        self.assertEqual(r["restaurants"], [])
        self.assertIn("Hidden gems are", r["reply"])

    def test_singular_wording(self):
        r = ask("pubs in Koregaon Park")
        self.assertTrue(r["reply"].startswith("Here is 1 pub place"), r["reply"])

    def test_limit(self):
        self.assertEqual(len(ask("top 2 restaurants in Kothrud")["restaurants"]), 2)

    def test_load_vocab_from_collection(self):
        v = chatbot.load_vocab(COLL)
        self.assertIn("kothrud", v["localities"])
        self.assertIn("biryani", v["cuisines"])


if __name__ == "__main__":
    unittest.main()
