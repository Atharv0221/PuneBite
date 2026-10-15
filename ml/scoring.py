"""
scoring.py - trust-adjusted rating and Hidden Gems for PuneBite Analyzer (Phase 8).

Two scores are produced:

1. trust_rating  - the displayed rating, lightly smoothed towards the Pune average
                   by the amount of evidence (votes).  Good for default sorting.
                   trust = v/(v+m) * R + m/(v+m) * C

2. peer_z        - how far a restaurant's rating is above restaurants with SIMILAR
                   numbers of votes (z-score inside a fixed vote band).
                   This is the core of the Hidden Gems idea, because Zomato's
                   displayed rating is already pulled down for low-vote
                   restaurants (see notebook 09). A high rating with few votes is
                   therefore *more* impressive, not less.

A restaurant is a HIDDEN GEM when it is
    - clearly good:        rating >= MIN_RATING
    - better than peers:   peer_z >= Z_MIN
    - low visibility:      MIN_VOTES <= votes <= MAX_VOTES
                           (enough votes to be credible, few enough to be unknown)
"""
import math

import numpy as np
import pandas as pd

# ---- parameters (documented and justified in notebooks/09_hidden_gems.ipynb) ----
M_DEFAULT = 20          # smoothing strength for trust_rating (votes)
MIN_VOTES = 20          # below this the rating is too thin to trust
MAX_VOTES = 300         # above this the restaurant is already well known
Z_MIN = 1.5             # at least 1.5 standard deviations above its vote band
MIN_RATING = 3.8        # and a genuinely good absolute rating
VOTE_BINS = [-1, 4, 9, 19, 29, 49, 99, 199, 499, 999, np.inf]
VOTE_LABELS = ["0-4", "5-9", "10-19", "20-29", "30-49", "50-99", "100-199", "200-499", "500-999", "1000+"]


def trust_rating(rating, votes, m=M_DEFAULT, c=None):
    """Smooth a rating towards c (default: mean rating of the rated restaurants)."""
    rating = pd.Series(rating, dtype="float64")
    votes = pd.Series(votes, index=rating.index, dtype="float64")
    if c is None:
        c = rating.mean()
    return (votes / (votes + m)) * rating + (m / (votes + m)) * c


def vote_band(votes):
    return pd.cut(pd.Series(votes), bins=VOTE_BINS, labels=VOTE_LABELS)


def add_scores(df, m=M_DEFAULT, min_votes=MIN_VOTES, max_votes=MAX_VOTES,
               z_min=Z_MIN, min_rating=MIN_RATING):
    """Return a copy of the cleaned dataframe with scoring columns added:
    trust_rating, vote_band, peer_z, hidden_gem, gem_score, gem_rank_locality.
    Unrated restaurants get NaN / False."""
    d = df.copy()
    rated = d["has_rating"]

    d["trust_rating"] = np.nan
    d.loc[rated, "trust_rating"] = trust_rating(d.loc[rated, "rating"], d.loc[rated, "votes"], m=m).values

    d["vote_band"] = vote_band(d["votes"]).astype(object)
    stats = d[rated].groupby("vote_band")["rating"].agg(["mean", "std"])
    mu = d["vote_band"].map(stats["mean"])
    sd = d["vote_band"].map(stats["std"])
    d["peer_z"] = np.where(rated, (d["rating"] - mu) / sd, np.nan)

    d["hidden_gem"] = (rated & (d["rating"] >= min_rating) & (d["peer_z"] >= z_min)
                       & d["votes"].between(min_votes, max_votes))
    d["gem_score"] = np.where(d["hidden_gem"], d["peer_z"], np.nan)
    d["gem_rank_locality"] = (d.groupby("locality")["gem_score"]
                                .rank(ascending=False, method="first"))
    return d


def beats_percent(z):
    """Friendly version of peer_z for the UI: the % of restaurants with a similar number
    of votes that this restaurant outperforms (normal CDF of the z-score, capped at 99)."""
    return min(99, int(round(0.5 * (1 + math.erf(float(z) / math.sqrt(2))) * 100)))
