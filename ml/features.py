"""
features.py - builds the model input table from the cleaned restaurant data.

Used by notebook 04 (training) AND by the backend API (prediction), so both
always create exactly the same columns.
"""
import numpy as np
import pandas as pd

NUMERIC = ["cost_capped", "n_cuisines", "n_amenities", "accepts_cards", "accepts_digital"]
CATEGORICAL = ["type_grp", "locality_grp"]


def _cuisine_col(name: str) -> str:
    return "cuis_" + name.lower().replace(" ", "_")


def fit_feature_spec(clean_df, amenity_cols, n_localities=30, n_cuisines=15,
                     min_type_count=40, min_amenity_share=0.01):
    """Learn WHICH columns/groups to use (from the data). Returns a plain dict
    that can be saved as JSON."""
    rated = clean_df[clean_df["has_rating"]]
    type_counts = rated["primary_type"].value_counts()
    return {
        "amenity_keep": [a for a in amenity_cols if rated[a].mean() >= min_amenity_share],
        "top_cuisines": clean_df["cuisines"].str.split("|").explode().value_counts().head(n_cuisines).index.tolist(),
        "top_localities": rated["locality"].value_counts().head(n_localities).index.tolist(),
        "valid_types": type_counts[type_counts >= min_type_count].index.tolist(),
    }


def make_features(df, spec, with_votes=False):
    """Return (X, feature_info). Missing amenity columns are filled with 0,
    so the API can send only the amenities that are present."""
    d = df.copy()
    for a in spec["amenity_keep"]:
        if a not in d.columns:
            d[a] = 0
    for c in spec["top_cuisines"]:
        d[_cuisine_col(c)] = d["cuisines"].str.split("|").apply(lambda xs, c=c: int(c in xs))
    d["locality_grp"] = d["locality"].where(d["locality"].isin(spec["top_localities"]), "Other")
    d["type_grp"] = d["primary_type"].where(d["primary_type"].isin(spec["valid_types"]), "Other")
    if with_votes:
        d["log_votes"] = np.log1p(d["votes"])

    numeric = NUMERIC + (["log_votes"] if with_votes else [])
    binary = spec["amenity_keep"] + [_cuisine_col(c) for c in spec["top_cuisines"]]
    X = d[numeric + CATEGORICAL + binary]
    return X, {"numeric": numeric, "categorical": CATEGORICAL, "binary": binary}
