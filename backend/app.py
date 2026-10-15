"""PuneBite Analyzer - Flask REST API.

Run from the project root:   python backend/app.py
Then open:                   http://127.0.0.1:5000/api/health

Every restaurant, locality, hidden gem, statistic and chatbot answer is read from MongoDB
(local or Atlas) through this API. Only the Opening Advisor also uses the saved ML models.
"""
import json
import re
import sys
import time
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(HERE), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import stats  # noqa: E402
from chatbot import chat_reply, load_vocab  # noqa: E402
from db import database_label, get_db  # noqa: E402
from ml.features import make_features  # noqa: E402

MODEL_DIR = ROOT / "ml" / "models"
DIST = ROOT / "frontend" / "dist"
app = Flask(__name__)
CORS(app)

HIDE_ID = {"_id": 0}
SORT_FIELDS = {"rating": "rating", "trust": "trust_rating", "votes": "votes",
               "cost": "cost_capped", "name": "name"}

# Results from notebooks 04 and 05 for the model that is allowed to see vote counts
# (the saved API models are the "no votes" versions, so only those metrics live in the *_meta.json files).
MODEL_NOTES = {"auc_with_votes": 0.94, "r2_with_votes": 0.55}


# ----------------------------------------------------------------- helpers
def col():
    return get_db().restaurants


def to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def to_int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def as_list(v):
    """Accept ["a", "b"], "a" or nothing, and always return a list of strings."""
    if v is None or v == "":
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def exact_ci(text):
    """Case-insensitive exact-match regex (works on strings and on arrays)."""
    return {"$regex": f"^{re.escape(text.strip())}$", "$options": "i"}


def r2(x):
    return None if x is None else round(x, 2)


_cache = {}
CACHE_SECONDS = 300


def cached(key, build, ttl=CACHE_SECONDS):
    """Keep slow whole-collection statistics for a few minutes so every page view does not
    re-read the database (matters on the free Atlas tier). Restart the server or wait
    five minutes after reloading the data."""
    hit = _cache.get(key)
    now = time.time()
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = build()
    _cache[key] = (now, value)
    return value


# ------------------------------------------------------------------ errors
@app.errorhandler(Exception)
def on_error(e):
    """Always answer /api/* requests with JSON, never an HTML error page."""
    api_call = request.path.startswith("/api/")
    if isinstance(e, HTTPException):
        return (jsonify(error=e.description), e.code) if api_call else e
    app.logger.exception("Unhandled error")
    if type(e).__module__.startswith("pymongo"):
        return jsonify(error="Database unavailable. Check MONGO_URI and the Atlas network access list.",
                       detail=type(e).__name__), 503
    return jsonify(error="Server error", detail=type(e).__name__), 500


# ------------------------------------------------------------------ health
@app.get("/api/health")
def health():
    try:
        return jsonify(status="ok", restaurants=col().count_documents({}), database=database_label())
    except Exception as e:  # noqa: BLE001
        app.logger.exception("Health check failed")
        return jsonify(status="error", detail=f"{type(e).__name__}: database unreachable"), 503


# ------------------------------------------------------------- restaurants
@app.get("/api/restaurants")
def restaurants():
    a = request.args
    q = {}
    if a.get("locality"):
        q["locality"] = exact_ci(a["locality"])
    if a.get("cuisine"):
        q["cuisines"] = exact_ci(a["cuisine"])
    if a.get("type"):
        q["establishment_type"] = exact_ci(a["type"])
    if a.get("q"):
        q["name"] = {"$regex": re.escape(a["q"].strip()), "$options": "i"}
    if str(a.get("gem", "")).lower() in ("1", "true", "yes"):
        q["hidden_gem"] = True

    min_rating = to_float(a.get("min_rating"))
    if min_rating is not None:
        q["rating"] = {"$gte": min_rating}
    max_cost = to_float(a.get("max_cost"))
    if max_cost is not None:
        q["cost_capped"] = {"$lte": max_cost}
    min_votes = to_int(a.get("min_votes"), None)
    if min_votes is not None:
        q["votes"] = {"$gte": min_votes}

    sort_field = SORT_FIELDS.get(a.get("sort", "rating"), "rating")
    direction = 1 if a.get("order", "desc").lower() == "asc" else -1
    sort = [(sort_field, direction)]
    if sort_field != "votes":
        sort.append(("votes", -1))

    page = max(to_int(a.get("page"), 1), 1)
    per_page = min(max(to_int(a.get("per_page"), 20), 1), 100)

    total = col().count_documents(q)
    cur = col().find(q, HIDE_ID).sort(sort).skip((page - 1) * per_page).limit(per_page)
    return jsonify(
        items=list(cur),
        page=page,
        per_page=per_page,
        total=total,
        pages=(total + per_page - 1) // per_page,
    )


# -------------------------------------------------------------- localities
def build_locality_table(min_count, min_rated):
    c = col()
    groups = list(c.aggregate([
        {"$group": {
            "_id": "$locality",
            "count": {"$sum": 1},
            "rated_count": {"$sum": {"$cond": [{"$ne": ["$rating", None]}, 1, 0]}},
            "high_rated": {"$sum": {"$cond": [{"$gte": ["$rating", 4.0]}, 1, 0]}},
            "gems": {"$sum": {"$cond": ["$hidden_gem", 1, 0]}},
            "avg_rating": {"$avg": "$rating"},
            "avg_cost": {"$avg": "$cost_capped"},
        }},
        {"$match": {"count": {"$gte": min_count}, "rated_count": {"$gte": min_rated}}},
        {"$sort": {"count": -1}},
    ]))
    groups = [g for g in groups if g["_id"]]
    names = [g["_id"] for g in groups]

    top_cuisines = {}
    for row in c.aggregate([
        {"$match": {"locality": {"$in": names}}},
        {"$unwind": "$cuisines"},
        {"$group": {"_id": {"l": "$locality", "c": "$cuisines"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]):
        lst = top_cuisines.setdefault(row["_id"]["l"], [])
        if len(lst) < 3:
            lst.append(row["_id"]["c"])

    top_type = {}
    for row in c.aggregate([
        {"$match": {"locality": {"$in": names}, "establishment_type": {"$ne": None}}},
        {"$group": {"_id": {"l": "$locality", "t": "$establishment_type"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]):
        top_type.setdefault(row["_id"]["l"], row["_id"]["t"])

    medians = stats.median_by(
        c.find({"locality": {"$in": names}}, {"locality": 1, "cost_capped": 1, "_id": 0}),
        "locality", "cost_capped")

    return [
        {
            "name": g["_id"],
            "count": g["count"],
            "rated_count": g["rated_count"],
            "avg_rating": r2(g["avg_rating"]),
            "avg_cost": None if g["avg_cost"] is None else round(g["avg_cost"]),
            "median_cost": None if g["_id"] not in medians else round(medians[g["_id"]]),
            "high_rated_count": g["high_rated"],
            "pct_high": round(g["high_rated"] / g["rated_count"] * 100, 1) if g["rated_count"] else None,
            "gems": g["gems"],
            "top_cuisines": top_cuisines.get(g["_id"], []),
            "top_type": top_type.get(g["_id"]),
        }
        for g in groups
    ]


@app.get("/api/localities")
def localities():
    min_count = to_int(request.args.get("min_count"), 1)
    min_rated = to_int(request.args.get("min_rated"), 1)
    return jsonify(cached(("localities", min_count, min_rated),
                          lambda: build_locality_table(min_count, min_rated)))


@app.get("/api/localities/<path:name>")
def locality_report(name):
    q = {"locality": exact_ci(name)}
    total = col().count_documents(q)
    if total == 0:
        return jsonify(error=f"Locality '{name}' not found"), 404

    summary = list(col().aggregate([
        {"$match": q},
        {"$group": {
            "_id": "$locality",
            "avg_rating": {"$avg": "$rating"},
            "avg_cost": {"$avg": "$cost_capped"},
            "rated_count": {"$sum": {"$cond": [{"$ne": ["$rating", None]}, 1, 0]}},
            "high_rated": {"$sum": {"$cond": [{"$gte": ["$rating", 4.0]}, 1, 0]}},
        }},
    ]))[0]

    cuisines = [
        {"cuisine": r["_id"], "count": r["n"], "avg_rating": r2(r["avg"])}
        for r in col().aggregate([
            {"$match": q}, {"$unwind": "$cuisines"},
            {"$group": {"_id": "$cuisines", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
            {"$sort": {"n": -1}}, {"$limit": 8},
        ])
    ]
    types = [
        {"type": r["_id"], "count": r["n"], "avg_rating": r2(r["avg"])}
        for r in col().aggregate([
            {"$match": q},
            {"$group": {"_id": "$establishment_type", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
            {"$sort": {"n": -1}},
        ])
    ]
    rated = [d["rating"] for d in col().find({**q, "rating": {"$ne": None}}, {"rating": 1, "_id": 0})]
    best = list(col().find({**q, "rating": {"$ne": None}, "votes": {"$gte": 20}}, HIDE_ID)
                .sort([("rating", -1), ("votes", -1)]).limit(5))

    return jsonify(
        name=name,
        count=total,
        rated_count=summary["rated_count"],
        avg_rating=r2(summary["avg_rating"]),
        avg_cost=None if summary["avg_cost"] is None else round(summary["avg_cost"]),
        high_rated_count=summary["high_rated"],
        high_rated_share=r2(summary["high_rated"] / summary["rated_count"]) if summary["rated_count"] else None,
        top_cuisines=cuisines,
        types=types,
        rating_distribution=stats.rating_histogram(rated),
        best_restaurants=best,
    )


# ------------------------------------------------------------- hidden gems
@app.get("/api/hidden-gems")
def hidden_gems():
    """Hidden gems as defined in ml/scoring.py: rated 3.8+, clearly better than restaurants with
    a similar number of reviews (peer_z >= 1.5) and between 20 and 300 reviews.
    The flag, score and 'beats X%' value were computed once by load_data.py."""
    q = {"hidden_gem": True}
    if request.args.get("locality"):
        q["locality"] = exact_ci(request.args["locality"])
    limit = min(max(to_int(request.args.get("limit"), 20), 1), 500)
    docs = list(col().find(q, HIDE_ID).sort([("gem_score", -1), ("votes", 1)]).limit(limit))
    return jsonify(items=docs, total=col().count_documents(q))


# ---------------------------------------------------------------- overview
def build_overview():
    c = col()
    total = c.count_documents({})
    if total == 0:
        return {"total_restaurants": 0, "rated_restaurants": 0, "localities": 0, "gems": 0,
                "rating_distribution": [], "votes_curve": [], "top_cuisines": [], "types": [], "price_bands": []}

    rated = c.count_documents({"rating": {"$ne": None}})
    high = c.count_documents({"rating": {"$gte": 4.0}})
    mean = next(iter(c.aggregate([
        {"$group": {"_id": None, "r": {"$avg": "$rating"}, "c": {"$avg": "$cost_capped"}}}])), {})

    rated_rows = list(c.find({"rating": {"$ne": None}}, {"rating": 1, "votes": 1, "_id": 0}))

    bands = list(c.aggregate([
        {"$match": {"rating": {"$ne": None}, "cost_capped": {"$ne": None}}},
        {"$bucket": {"groupBy": "$cost_capped", "boundaries": [0, 200, 400, 700, 1000, 10**9],
                     "default": "other",
                     "output": {"count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"}}}},
    ]))
    labels = {0: "Under 200", 200: "200-399", 400: "400-699", 700: "700-999", 1000: "1000+"}

    return {
        "total_restaurants": total,
        "rated_restaurants": rated,
        "high_rated_restaurants": high,
        "high_rated_share": r2(high / rated) if rated else None,
        "avg_rating": r2(mean.get("r")),
        "avg_cost": None if mean.get("c") is None else round(mean["c"]),
        "localities": len([x for x in c.distinct("locality") if x]),
        "gems": c.count_documents({"hidden_gem": True}),
        "rating_distribution": stats.rating_histogram(r["rating"] for r in rated_rows),
        "votes_curve": stats.votes_curve(rated_rows),
        "top_cuisines": [
            {"cuisine": r["_id"], "count": r["n"], "avg_rating": r2(r["avg"])}
            for r in c.aggregate([
                {"$unwind": "$cuisines"},
                {"$group": {"_id": "$cuisines", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
                {"$sort": {"n": -1}}, {"$limit": 14}])
        ],
        "types": [
            {"type": r["_id"] or "Other", "count": r["n"], "avg_rating": r2(r["avg"])}
            for r in c.aggregate([
                {"$group": {"_id": "$establishment_type", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
                {"$sort": {"n": -1}}])
        ],
        "price_bands": [
            {"band": labels.get(b["_id"], "Other"), "count": b["count"], "avg_rating": r2(b["avg_rating"])}
            for b in bands if b["_id"] != "other"
        ],
    }


@app.get("/api/stats/overview")
def overview():
    return jsonify(cached("overview", build_overview))


# ---------------------------------------------------------------- insights
def build_insights():
    rows = list(col().find({"rating": {"$ne": None}},
                           {"rating": 1, "votes": 1, "amenities": 1, "locality": 1, "_id": 0}))
    out = stats.insight_figures(rows)
    try:
        meta = get_meta()
        auc_new, r2_new = meta["clf"]["test_roc_auc"], meta["reg"]["test_r2"]
    except (OSError, KeyError, ValueError):
        auc_new, r2_new = 0.82, 0.28
    out["auc"] = {"withVotes": MODEL_NOTES["auc_with_votes"], "noVotes": round(auc_new, 2)}
    out["r2"] = {"withVotes": MODEL_NOTES["r2_with_votes"], "noVotes": round(r2_new, 2)}
    return out


@app.get("/api/stats/insights")
def insights():
    """Numbers behind the 'Four things we learned' cards: computed live from MongoDB,
    plus the model scores that were saved next to the models."""
    return jsonify(cached("insights", build_insights))


# ----------------------------------------------------------------- predict
_models = {}
_meta = {}


def get_meta():
    """Model metadata (feature lists, scores). Small JSON files, so no need to load the models."""
    if not _meta:
        _meta["clf"] = json.loads((MODEL_DIR / "high_rating_classifier_meta.json").read_text(encoding="utf-8"))
        _meta["reg"] = json.loads((MODEL_DIR / "rating_regressor_meta.json").read_text(encoding="utf-8"))
    return _meta


def get_models():
    if not _models:
        _models["clf"] = joblib.load(MODEL_DIR / "high_rating_classifier.joblib")
        _models["reg"] = joblib.load(MODEL_DIR / "rating_regressor.joblib")
    return _models


def norm(name):
    """'Outdoor Seating' -> 'outdoor_seating' (the model's column style)."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


@app.get("/api/meta/options")
def options():
    """Valid values for the prediction form and the explorer dropdowns."""
    spec = get_meta()["clf"]["feature_spec"]
    return jsonify(
        amenities=spec["amenity_keep"],
        cuisines=spec["top_cuisines"],
        localities=spec["top_localities"],
        types=spec["valid_types"],
    )


def feature_row(spec, cost, cuisines, amenities, locality, ptype, cards, digital):
    """One restaurant described the way the models expect (before make_features)."""
    row = {
        "cost_capped": cost,
        "n_cuisines": len(cuisines),
        "n_amenities": len(amenities),
        "accepts_cards": int(cards),
        "accepts_digital": int(digital),
        "cuisines": "|".join(cuisines),
        "locality": locality or "Other",
        "primary_type": ptype or "Other",
    }
    for a in spec["amenity_keep"]:
        row[a] = int(a in amenities)
    return row


@app.post("/api/predict")
def predict():
    """Body (JSON): cost (required), type, locality, cuisines[], amenities[],
    accepts_cards (bool), accepts_digital (bool).
    Uses the 'no votes' models, because a new restaurant has no votes yet.

    The answer also lists `contributions`: for every choice the person made we re-run the
    real model without it. value = (probability with it) - (probability without it), so a
    positive number means that choice helps. This is a what-if explanation, not a stand-alone effect."""
    body = request.get_json(silent=True) or {}
    cost = to_float(body.get("cost", body.get("cost_capped")))
    if cost is None or cost <= 0:
        return jsonify(error="'cost' (cost for two, a positive number) is required"), 400

    try:
        m, meta = get_models(), get_meta()
    except Exception:  # noqa: BLE001
        app.logger.exception("Could not load the saved models")
        return jsonify(error="Could not load the saved models."), 503

    spec = meta["clf"]["feature_spec"]
    cuisines = list(dict.fromkeys(as_list(body.get("cuisines"))))
    amenities = {norm(a) for a in as_list(body.get("amenities"))}
    locality = body.get("locality") or "Other"
    ptype = body.get("type") or body.get("primary_type") or "Other"
    cards = bool(body.get("accepts_cards", False))
    digital = bool(body.get("accepts_digital", False))

    def row(**changes):
        args = {"cost": cost, "cuisines": cuisines, "amenities": amenities, "locality": locality,
                "ptype": ptype, "cards": cards, "digital": digital, **changes}
        return feature_row(spec, **args)

    variants = [(None, None, row())]                                  # first row = the real question
    for a in sorted(amenities & set(spec["amenity_keep"])):
        variants.append(("amenity", a, row(amenities=amenities - {a})))
    for c in cuisines:
        if c in spec["top_cuisines"]:
            variants.append(("cuisine", c, row(cuisines=[x for x in cuisines if x != c])))
    if ptype in spec["valid_types"]:
        variants.append(("type", ptype, row(ptype="Other")))
    if locality in spec["top_localities"]:
        variants.append(("locality", locality, row(locality="Other")))
    if cards or digital:
        variants.append(("cards", "cards", row(cards=False, digital=False)))

    X, _ = make_features(pd.DataFrame([v[2] for v in variants]), spec, with_votes=False)
    probas = m["clf"].predict_proba(X)[:, 1]
    proba = float(probas[0])
    rating = float(m["reg"].predict(X.iloc[[0]])[0])
    threshold = meta["clf"]["threshold"]

    contributions = sorted(
        ({"kind": kind, "name": name, "value": round(proba - float(p), 4)}
         for (kind, name, _), p in zip(variants[1:], probas[1:])),
        key=lambda x: -x["value"])

    return jsonify(
        high_rated_probability=round(proba, 3),
        predicted_high_rated=proba >= threshold,
        decision_threshold=round(threshold, 3),
        predicted_rating=round(min(max(rating, 0), 5), 2),
        contributions=contributions,
        unrecognised_amenities=sorted(a for a in amenities if a not in spec["amenity_keep"]),
        note="Model uses no vote information (new-restaurant scenario). "
             f"Test ROC-AUC {meta['clf']['test_roc_auc']:.2f}, rating RMSE {meta['reg']['test_rmse']:.2f}.",
    )


# ----------------------------------------------------------------- chatbot
_chat_cache = {}


@app.post("/api/chat")
def chat():
    """Keyword chatbot (no AI model).  Body (JSON): {"message": "best cheap biryani in Kothrud"}
    The locality / cuisine / amenity names are read from MongoDB once and cached; restart the
    server after reloading the data."""
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()[:300]
    if not message:
        return jsonify(error="'message' is required"), 400
    if "vocab" not in _chat_cache:
        _chat_cache["vocab"] = load_vocab(col())
    return jsonify(chat_reply(message, col(), _chat_cache["vocab"]))


# ------------------------------------------------- serve the React build
# One service serves both /api/* and the website (no CORS or second host needed).
# Build first:  cd frontend && npm install && npm run build   (creates frontend/dist)
@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def spa(path):
    if path.startswith("api/"):
        return jsonify(error="Not found"), 404
    if not DIST.exists():
        return jsonify(error="Frontend not built. Run 'npm run build' in frontend/, "
                             "or use the Vite dev server on port 5173."), 404
    if path and (DIST / path).is_file():
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, "index.html")   # every page route (/gems, /chat ...) is handled by React


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
