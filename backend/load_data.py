"""Load data/processed/restaurants_clean.csv into MongoDB (local or Atlas).

Run from the project root:
    python backend/load_data.py             # drops and rebuilds the 'restaurants' collection
    python backend/load_data.py --dry-run   # builds every document but does NOT touch the database

Safe to re-run. Each restaurant becomes one document that already contains the
scores computed in ml/scoring.py (trust_rating, peer_z, hidden_gem, beats ...),
so the API and the chatbot never have to recompute them.
"""
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import ROOT, describe_target  # noqa: E402
from ml.scoring import add_scores, beats_percent  # noqa: E402

CSV_PATH = ROOT / "data" / "processed" / "restaurants_clean.csv"
CLUSTERS_PATH = ROOT / "data" / "processed" / "restaurants_clusters.csv"
INDEXED_FIELDS = (
    "locality", "rating", "cuisines", "establishment_type",
    "cost_capped", "votes", "trust_rating", "hidden_gem", "gem_score",
)


def clean_value(v):
    """Turn NaN / numpy types into plain Python values MongoDB accepts."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):          # numpy scalar -> python scalar
        v = v.item()
        if isinstance(v, float) and math.isnan(v):
            return None
    if v is pd.NA or v is pd.NaT:
        return None
    return v


def split_pipe(s):
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return []
    return [x.strip() for x in str(s).split("|") if x.strip()]


def build_doc(row):
    r = {k: clean_value(v) for k, v in row.items()}
    is_gem = bool(r.get("hidden_gem")) if r.get("hidden_gem") is not None else False
    peer_z = r.get("peer_z")
    doc = {
        "name": r.get("name"),
        "url": r.get("url"),
        "locality": r.get("locality"),
        "establishment_type": r.get("establishment_type"),
        "rating": r.get("rating"),
        "votes": r.get("votes"),
        "trust_rating": r.get("trust_rating"),
        "vote_band": r.get("vote_band"),
        "peer_z": peer_z,
        "hidden_gem": is_gem,
        "gem_score": r.get("gem_score"),
        "gem_rank_locality": r.get("gem_rank_locality") if is_gem else None,
        # "beats X% of restaurants with a similar number of reviews" (shown on the gem cards)
        "beats": beats_percent(peer_z) if is_gem and peer_z is not None else None,
        "cluster": r.get("cluster"),
        "cluster_name": r.get("cluster_name"),
        "cost_for_two": r.get("cost_for_two"),
        "cost_capped": r.get("cost_capped"),
        "cuisines": split_pipe(r.get("cuisines")),
        "primary_cuisine": r.get("primary_cuisine"),
        "amenities": split_pipe(r.get("amenities")),
        "n_cuisines": r.get("n_cuisines"),
        "n_amenities": r.get("n_amenities"),
        "accepts_cards": r.get("accepts_cards"),
        "star_pct": {str(i): r.get(f"star{i}_pct") for i in (5, 4, 3, 2, 1)},
        "positive_pct": r.get("positive_pct"),
        "polarization_pct": r.get("polarization_pct"),
        "timings": r.get("timings"),
        "address": r.get("address"),
        "payment_modes": r.get("payment_modes"),
        "has_rating": bool(r.get("has_rating")) if r.get("has_rating") is not None else r.get("rating") is not None,
    }
    return doc


def build_documents():
    """CSV -> scored dataframe -> list of MongoDB documents."""
    if not CSV_PATH.exists():
        sys.exit(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print(f"Read {len(df):,} rows x {df.shape[1]} columns")

    df = add_scores(df)
    print(f"Scored: {int(df['has_rating'].sum()):,} rated restaurants, {int(df['hidden_gem'].sum())} hidden gems")

    if CLUSTERS_PATH.exists():
        clusters = pd.read_csv(CLUSTERS_PATH)
        df = df.merge(
            clusters[["url", "cluster", "cluster_name"]],
            on="url",
            how="left",
            validate="one_to_one",
        )
        print(f"Matched cluster labels for {df['cluster'].notna().sum():,} restaurants")
    else:
        df["cluster"] = pd.NA
        df["cluster_name"] = pd.NA

    return [build_doc(row) for row in df.to_dict("records")]


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    docs = build_documents()
    if dry_run:
        print(f"Dry run OK: {len(docs):,} documents built, database untouched.")
        print("Sample:", {k: docs[0][k] for k in ("name", "locality", "rating", "trust_rating", "hidden_gem")})
        return

    from db import get_db  # imported late so --dry-run works without pymongo

    db = get_db()
    print("Loading into:", describe_target())
    db.restaurants.drop()
    for i in range(0, len(docs), 2000):          # batches: friendlier to a remote (Atlas) connection
        db.restaurants.insert_many(docs[i:i + 2000])

    for field in INDEXED_FIELDS:
        db.restaurants.create_index(field)

    print(f"Inserted {db.restaurants.count_documents({}):,} documents into '{db.name}.restaurants' "
          f"({db.restaurants.count_documents({'hidden_gem': True})} hidden gems)")
    print("Sample:", db.restaurants.find_one({}, {"_id": 0, "name": 1, "locality": 1,
                                                  "rating": 1, "cuisines": 1}))


if __name__ == "__main__":
    main()
