"""
cleaning.py - reusable cleaning functions for the PuneBite Analyzer project.

Each function does ONE cleaning step and returns a new DataFrame, so the
notebook can show the effect of every step (good for the viva).
"""
import re
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- constants
RENAME_MAP = {
    "Restaurant_Name": "name",
    "Web_Link": "url",
    "Locality": "locality",
    "Sponsored": "establishment_type",      # misleading original name
    "Ratings_out_of_5": "rating",
    "Number of votes": "votes",
    "Phone_number": "phone",
    "Cuisines": "cuisines",
    "Charges_for_two": "cost_for_two",
    "payment_modes": "payment_modes",
    "Rest_timming": "timings",
    "Detail_address": "address",
    "5_star_review_percentage": "star5_pct",
    "4_star_review_percentage": "star4_pct",
    "3_star_review_percentage": "star3_pct",
    "2_star_review_percentage": "star2_pct",
    "1_star_review_percentage": "star1_pct",
    "spam_review": "spam_review_count",
}
STAR_COLS = ["star5_pct", "star4_pct", "star3_pct", "star2_pct", "star1_pct"]


def _snake(text: str) -> str:
    """'Wine and Beer' -> 'wine_and_beer', '4/5 Star' -> 'star_4_5'"""
    text = text.strip().lower().replace("4/5 star", "star_4_5")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


# ---------------------------------------------------------------- steps
def load_raw(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def rename_columns(df: pd.DataFrame):
    """Rename the known columns; turn every amenity column into snake_case.
    Returns (df, list_of_amenity_columns)."""
    df = df.copy()
    cols = list(df.columns)
    first = cols.index("1_star_review_percentage") + 1
    last = cols.index("spam_review")
    amenity_original = cols[first:last]                 # the yes/no columns
    amenity_map = {c: _snake(c) for c in amenity_original}
    df = df.rename(columns={**RENAME_MAP, **amenity_map})
    return df, list(amenity_map.values())


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Same restaurant page (url) listed twice -> keep the first."""
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset="url", keep="first")
    return df.reset_index(drop=True)


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in ["name", "locality", "establishment_type", "cuisines", "address"]:
        df[c] = df[c].astype(str).str.strip()
    return df


def clean_votes(df: pd.DataFrame) -> pd.DataFrame:
    """'7029  votes' -> 7029 (int). Missing -> 0."""
    df = df.copy()
    nums = df["votes"].astype(str).str.extract(r"(\d+)")[0]
    df["votes"] = pd.to_numeric(nums, errors="coerce").fillna(0).astype(int)
    return df


def clean_rating(df: pd.DataFrame) -> pd.DataFrame:
    """'-' means unrated. 0.0 rows ALL have 0 votes, so 0 is a placeholder
    for 'no reviews yet', not a real score. Both become NaN."""
    df = df.copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df.loc[df["rating"] == 0, "rating"] = np.nan
    df["has_rating"] = df["rating"].notna()
    return df


def clean_cost(df: pd.DataFrame, cap_quantile: float = 0.99) -> pd.DataFrame:
    """'₹1,400' -> 1400. 'Not Present' -> NaN, then imputed with the median
    of the same locality + establishment type (fallback: type, then global).
    Extreme values are capped at the 99th percentile (cost_for_two keeps raw)."""
    df = df.copy()
    digits = df["cost_for_two"].astype(str).str.replace(r"[^\d]", "", regex=True)
    df["cost_for_two"] = pd.to_numeric(digits, errors="coerce")
    df["cost_missing"] = df["cost_for_two"].isna()

    cap = df["cost_for_two"].quantile(cap_quantile)
    df["cost_capped"] = df["cost_for_two"].clip(upper=cap)

    g_loc = df.groupby(["locality", "establishment_type"])["cost_capped"].transform("median")
    g_type = df.groupby("establishment_type")["cost_capped"].transform("median")
    df["cost_capped"] = (df["cost_capped"].fillna(g_loc)
                                          .fillna(g_type)
                                          .fillna(df["cost_capped"].median()))
    return df


def clean_star_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """'79%' -> 79.0. If all five are 0 the restaurant has no reviews -> NaN.
    Adds helpers: positive_pct, extreme_pct, polarization_pct."""
    df = df.copy()
    for c in STAR_COLS:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace("%", "", regex=False),
                              errors="coerce")
    no_reviews = df[STAR_COLS].fillna(0).sum(axis=1) == 0
    df.loc[no_reviews, STAR_COLS] = np.nan
    df["positive_pct"] = df["star5_pct"] + df["star4_pct"]
    df["extreme_pct"] = df["star5_pct"] + df["star1_pct"]
    # polarization: high only when BOTH 5-star and 1-star shares are large
    # (people either love it or hate it). 0 when reviews lean one way.
    df["polarization_pct"] = 2 * df[["star5_pct", "star1_pct"]].min(axis=1)
    return df


def parse_list_columns(df: pd.DataFrame, amenity_cols) -> pd.DataFrame:
    """cuisines / establishment_type -> counts + primary value;
    amenities -> one pipe-separated string + count."""
    df = df.copy()
    cuisine_lists = df["cuisines"].str.split(",").apply(lambda xs: [x.strip() for x in xs if x.strip()])
    df["n_cuisines"] = cuisine_lists.str.len()
    df["primary_cuisine"] = cuisine_lists.str[0]
    df["cuisines"] = cuisine_lists.str.join("|")

    types = df["establishment_type"].str.split(",").apply(lambda xs: [x.strip() for x in xs if x.strip()])
    df["primary_type"] = types.str[0]

    am = df[amenity_cols].astype(int)
    df["n_amenities"] = am.sum(axis=1)
    names = np.array(amenity_cols)
    df["amenities"] = [ "|".join(names[row.astype(bool)]) for row in am.values ]
    return df


def add_payment_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    p = df["payment_modes"].astype(str).str.lower()
    df["accepts_cards"] = p.str.contains("card").astype(int)
    df["accepts_digital"] = p.str.contains("digital").astype(int)
    return df


def drop_constant_amenities(df: pd.DataFrame, amenity_cols):
    """Remove yes/no columns that are all zero (carry no information)."""
    constant = [c for c in amenity_cols if df[c].nunique() <= 1]
    keep = [c for c in amenity_cols if c not in constant]
    return df.drop(columns=constant), keep, constant


# ---------------------------------------------------------------- pipeline
def run_pipeline(path: str):
    """Run every step. Returns (clean_df, amenity_cols)."""
    df = load_raw(path)
    df, amenity_cols = rename_columns(df)
    df = drop_duplicates(df)
    df = clean_text_columns(df)
    df = clean_votes(df)
    df = clean_rating(df)
    df = clean_cost(df)
    df = clean_star_percentages(df)
    df = parse_list_columns(df, amenity_cols)
    df = add_payment_flags(df)
    df, amenity_cols, _ = drop_constant_amenities(df, amenity_cols)
    df = df.drop(columns=["phone"])     # not useful for analysis
    return df, amenity_cols
