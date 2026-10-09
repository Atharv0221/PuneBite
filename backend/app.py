"""PuneBite Analyzer - Flask REST API.

Run from the project root:   python backend/app.py
Then open:                   http://127.0.0.1:5000/api/health
"""
import re
import sys
from collections import Counter
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(HERE), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from db import get_db  # noqa: E402
from ml.features import make_features  # noqa: E402

MODEL_DIR = ROOT / "ml" / "models"
app = Flask(__name__)
CORS(app)

HIDE_ID = {"_id": 0}
SORT_FIELDS = {"rating": "rating", "trust": "trust_rating", "votes": "votes", "cost": "cost_capped", "name": "name"}


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


def exact_ci(text):
    """Case-insensitive exact-match regex (works on strings and on arrays)."""
    return {"$regex": f"^{re.escape(text.strip())}$", "$options": "i"}


def r2(x):
    return None if x is None else round(x, 2)


def with_trust(doc):
    """trust_rating is stored by backend/load_data.py (ml/scoring.py); keep the key present."""
    doc.setdefault("trust_rating", None)
    return doc


# ------------------------------------------------------------------ health
@app.get("/api/health")
def health():
    try:
        n = col().count_documents({})
        return jsonify(status="ok", restaurants=n)
    except Exception as e:  # noqa: BLE001
        return jsonify(status="error", detail=str(e)), 503


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
        items=[with_trust(d) for d in cur],
        page=page,
        per_page=per_page,
        total=total,
        pages=(total + per_page - 1) // per_page,
    )


# -------------------------------------------------------------- localities
@app.get("/api/localities")
def localities():
    min_count = to_int(request.args.get("min_count"), 1)
    stats = list(col().aggregate([
        {"$group": {
            "_id": "$locality",
            "count": {"$sum": 1},
            "rated_count": {"$sum": {"$cond": [{"$ne": ["$rating", None]}, 1, 0]}},
            "avg_rating": {"$avg": "$rating"},
            "avg_cost": {"$avg": "$cost_capped"},
        }},
        {"$match": {"count": {"$gte": min_count}}},
        {"$sort": {"count": -1}},
    ]))
    names = [s["_id"] for s in stats]

    top = {}
    for row in col().aggregate([
        {"$match": {"locality": {"$in": names}}},
        {"$unwind": "$cuisines"},
        {"$group": {"_id": {"l": "$locality", "c": "$cuisines"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]):
        lst = top.setdefault(row["_id"]["l"], [])
        if len(lst) < 3:
            lst.append(row["_id"]["c"])

    return jsonify([
        {
            "name": s["_id"],
            "count": s["count"],
            "rated_count": s["rated_count"],
            "avg_rating": r2(s["avg_rating"]),
            "avg_cost": None if s["avg_cost"] is None else round(s["avg_cost"]),
            "top_cuisines": top.get(s["_id"], []),
        }
        for s in stats if s["_id"]
    ])


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
    hist = Counter()
    for d in col().find({**q, "rating": {"$ne": None}}, {"rating": 1, "_id": 0}):
        hist[int(d["rating"] * 2) / 2] += 1

    best = list(col().find({**q, "trust_rating": {"$ne": None}, "votes": {"$gte": 20}}, HIDE_ID)
                .sort([("trust_rating", -1), ("votes", -1)]).limit(5))

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
        rating_distribution=[{"bin": f"{k:.1f}-{k + 0.5:.1f}", "count": v} for k, v in sorted(hist.items())],
        best_restaurants=[with_trust(d) for d in best],
    )


# ------------------------------------------------------------- hidden gems
@app.get("/api/hidden-gems")
def hidden_gems():
    """Restaurants flagged by ml/scoring.py: top 15% trust-adjusted rating in their
    locality, 20-200 votes, trust rating >= 3.7. Optional: ?locality=&limit="""
    q = {"is_hidden_gem": True}
    if request.args.get("locality"):
        q["locality"] = exact_ci(request.args["locality"])
    limit = min(max(to_int(request.args.get("limit"), 20), 1), 100)
    docs = col().find(q, HIDE_ID).sort([("trust_rating", -1), ("votes", -1)]).limit(limit)
    return jsonify(rule="top 15% trust rating in locality, 20-200 votes, trust >= 3.7",
                   items=[with_trust(d) for d in docs])


# ---------------------------------------------------------------- clusters
@app.get("/api/clusters")
def clusters():
    """Restaurant segments from notebook 07 (K-Means, k=5)."""
    rows = col().aggregate([
        {"$match": {"cluster_name": {"$ne": None}}},
        {"$group": {"_id": "$cluster_name", "count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"},
                    "avg_votes": {"$avg": "$votes"}, "avg_cost": {"$avg": "$cost_capped"}}},
        {"$sort": {"count": -1}},
    ])
    return jsonify([{"name": r["_id"], "count": r["count"], "avg_rating": r2(r["avg_rating"]),
                     "avg_votes": None if r["avg_votes"] is None else round(r["avg_votes"]),
                     "avg_cost": None if r["avg_cost"] is None else round(r["avg_cost"])} for r in rows])


# ---------------------------------------------------------------- overview
@app.get("/api/stats/overview")
def overview():
    total = col().count_documents({})
    rated = col().count_documents({"rating": {"$ne": None}})
    high = col().count_documents({"rating": {"$gte": 4.0}})
    mean = list(col().aggregate([
        {"$group": {"_id": None, "r": {"$avg": "$rating"}, "c": {"$avg": "$cost_capped"}}}]))[0]

    hist = Counter()
    for d in col().find({"rating": {"$ne": None}}, {"rating": 1, "_id": 0}):
        hist[int(d["rating"] * 2) / 2] += 1

    bands = list(col().aggregate([
        {"$match": {"rating": {"$ne": None}, "cost_capped": {"$ne": None}}},
        {"$bucket": {"groupBy": "$cost_capped", "boundaries": [0, 200, 400, 700, 1000, 10**9],
                     "default": "other",
                     "output": {"count": {"$sum": 1}, "avg_rating": {"$avg": "$rating"}}}},
    ]))
    labels = {0: "Under 200", 200: "200-399", 400: "400-699", 700: "700-999", 1000: "1000+"}

    return jsonify(
        total_restaurants=total,
        rated_restaurants=rated,
        high_rated_restaurants=high,
        high_rated_share=r2(high / rated) if rated else None,
        avg_rating=r2(mean["r"]),
        avg_cost=None if mean["c"] is None else round(mean["c"]),
        localities=len([x for x in col().distinct("locality") if x]),
        rating_distribution=[{"bin": f"{k:.1f}-{k + 0.5:.1f}", "count": v} for k, v in sorted(hist.items())],
        top_cuisines=[
            {"cuisine": r["_id"], "count": r["n"], "avg_rating": r2(r["avg"])}
            for r in col().aggregate([
                {"$unwind": "$cuisines"},
                {"$group": {"_id": "$cuisines", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
                {"$sort": {"n": -1}}, {"$limit": 10}])
        ],
        types=[
            {"type": r["_id"], "count": r["n"], "avg_rating": r2(r["avg"])}
            for r in col().aggregate([
                {"$group": {"_id": "$establishment_type", "n": {"$sum": 1}, "avg": {"$avg": "$rating"}}},
                {"$sort": {"n": -1}}])
        ],
        price_bands=[
            {"band": labels.get(b["_id"], "Other"), "count": b["count"], "avg_rating": r2(b["avg_rating"])}
            for b in bands if b["_id"] != "other"
        ],
    )


# ----------------------------------------------------------------- predict
_models = {}


def get_models():
    if not _models:
        _models["clf"] = joblib.load(MODEL_DIR / "high_rating_classifier.joblib")
        _models["reg"] = joblib.load(MODEL_DIR / "rating_regressor.joblib")
        import json
        _models["clf_meta"] = json.loads((MODEL_DIR / "high_rating_classifier_meta.json").read_text(encoding="utf-8"))
        _models["reg_meta"] = json.loads((MODEL_DIR / "rating_regressor_meta.json").read_text(encoding="utf-8"))
    return _models


def norm(name):
    """'Outdoor Seating' -> 'outdoor_seating' (the model's column style)."""
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


@app.get("/api/meta/options")
def options():
    """Valid values for the prediction form dropdowns."""
    spec = get_models()["clf_meta"]["feature_spec"]
    return jsonify(
        amenities=spec["amenity_keep"],
        cuisines=spec["top_cuisines"],
        localities=spec["top_localities"],
        types=spec["valid_types"],
    )


@app.post("/api/predict")
def predict():
    """Body (JSON): cost (required), type, locality, cuisines[], amenities[],
    accepts_cards (bool), accepts_digital (bool).
    Uses the 'no votes' models, because a new restaurant has no votes yet."""
    body = request.get_json(silent=True) or {}
    cost = to_float(body.get("cost"))
    if cost is None or cost <= 0:
        return jsonify(error="'cost' (cost for two, a positive number) is required"), 400

    try:
        m = get_models()
    except Exception as e:  # noqa: BLE001
        return jsonify(error=f"Could not load models: {e}"), 503

    spec = m["clf_meta"]["feature_spec"]
    cuisines = body.get("cuisines") or []
    if isinstance(cuisines, str):
        cuisines = [cuisines]
    amenities = {norm(a) for a in (body.get("amenities") or [])}

    row = {
        "cost_capped": cost,
        "n_cuisines": len(cuisines),
        "n_amenities": len(amenities),
        "accepts_cards": int(bool(body.get("accepts_cards", False))),
        "accepts_digital": int(bool(body.get("accepts_digital", False))),
        "cuisines": "|".join(cuisines),
        "locality": body.get("locality") or "Other",
        "primary_type": body.get("type") or "Other",
    }
    for a in spec["amenity_keep"]:
        row[a] = int(a in amenities)

    X, _ = make_features(pd.DataFrame([row]), spec, with_votes=False)

    proba = float(m["clf"].predict_proba(X)[0, 1])
    threshold = m["clf_meta"]["threshold"]
    rating = float(m["reg"].predict(X)[0])

    return jsonify(
        high_rated_probability=round(proba, 3),
        predicted_high_rated=proba >= threshold,
        decision_threshold=round(threshold, 3),
        predicted_rating=round(min(max(rating, 0), 5), 2),
        unrecognised_amenities=sorted(a for a in amenities if a not in spec["amenity_keep"]),
        note="Model uses no vote information (new-restaurant scenario). "
             f"Test ROC-AUC {m['clf_meta']['test_roc_auc']:.2f}, rating RMSE {m['reg_meta']['test_rmse']:.2f}.",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
