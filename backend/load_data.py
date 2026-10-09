"""Load data/processed/restaurants_clean.csv into MongoDB.
 
Run from the project root:   python backend/load_data.py
Safe to re-run: it drops and rebuilds the 'restaurants' collection.
"""
import math
import sys
from pathlib import Path
 
import pandas as pd
 
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import get_db, ROOT  # noqa: E402
from ml.scoring import add_trust_scores  # noqa: E402
 
CSV_PATH = ROOT / "data" / "processed" / "restaurants_clean.csv"
CLUSTERS_PATH = ROOT / "data" / "processed" / "restaurants_clusters.csv"
 
 
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
    return v
 
 
def split_pipe(s):
    if s is None or (isinstance(s, float) and math.isnan(s)):
        return []
    return [x.strip() for x in str(s).split("|") if x.strip()]
 
 
def build_doc(row):
    r = {k: clean_value(v) for k, v in row.items()}
    doc = {
        "name": r.get("name"),
        "url": r.get("url"),
        "locality": r.get("locality"),
        "establishment_type": r.get("establishment_type"),
        "rating": r.get("rating"),
        "votes": r.get("votes"),
        "trust_rating": r.get("trust_rating"),
        "hidden_gem": bool(r.get("hidden_gem")) if r.get("hidden_gem") is not None else False,
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
 
 
def main():
    if not CSV_PATH.exists():
        sys.exit(f"CSV not found: {CSV_PATH}")
 
    df = pd.read_csv(CSV_PATH)
    print(f"Read {len(df):,} rows x {df.shape[1]} columns")

    df = add_trust_scores(df)
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

    docs = [build_doc(row) for row in df.to_dict("records")]
 
    db = get_db()
    db.restaurants.drop()
    db.restaurants.insert_many(docs)
 
    for field in (
        "locality",
        "rating",
        "cuisines",
        "establishment_type",
        "cost_capped",
        "votes",
        "trust_rating",
        "hidden_gem",
    ):
        db.restaurants.create_index(field)
 
    print(f"Inserted {db.restaurants.count_documents({}):,} documents into "
          f"'{db.name}.restaurants'")
    print("Sample:", db.restaurants.find_one({}, {"_id": 0, "name": 1, "locality": 1,
                                                  "rating": 1, "cuisines": 1}))
 
 
if __name__ == "__main__":
    main()
 
