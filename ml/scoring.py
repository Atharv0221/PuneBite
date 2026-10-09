"""
scoring.py - trust-adjusted rating and "hidden gems" (Phase 8).

Why: a 4.8 from 12 votes is much less reliable than a 4.5 from 1,500 votes.
The trust-adjusted rating pulls restaurants with few votes towards the overall
average (a Bayesian / IMDb-style weighted rating):

    trust = v / (v + m) * R  +  m / (v + m) * C

    R = the restaurant's own rating     v = its number of votes
    C = mean rating of all rated restaurants (about 3.44)
    m = votes needed before we trust the restaurant's own rating as much as
        the prior (we use m = 50, the "popular" threshold from notebooks 02/03)

With many votes trust -> R; with no votes trust -> C.

Used by notebook 09, backend/load_data.py (stored in MongoDB) and the API.
"""
import numpy as np
import pandas as pd

DEFAULT_M = 50                   # prior strength, in votes
GEM_MIN_VOTES = 20               # below this even a shrunk score is mostly noise
GEM_MAX_VOTES = 200              # above this the place is already well known
GEM_TOP_SHARE = 0.15             # must be in the top 15% of its locality ...
GEM_MIN_LOCALITY = 10            # ... and the locality needs >= 10 rated places for that to mean anything
GEM_MIN_TRUST = 3.7              # ... and be good in absolute terms (not just "best of a weak locality")


def global_mean(df):
    """C: mean rating over rated restaurants."""
    return float(df["rating"].dropna().mean())


def trust_rating(rating, votes, m=DEFAULT_M, c=None):
    """Vectorised trust-adjusted rating. NaN where there is no rating."""
    rating = pd.to_numeric(pd.Series(rating), errors="coerce")
    votes = pd.to_numeric(pd.Series(votes), errors="coerce").fillna(0).clip(lower=0)
    if c is None:
        c = float(rating.dropna().mean())
    out = votes / (votes + m) * rating + m / (votes + m) * c
    return out.where(rating.notna())


def add_trust(df, m=DEFAULT_M):
    """Return a copy of df with `trust_rating` and `is_hidden_gem` columns."""
    d = df.copy()
    c = global_mean(d)
    d["trust_rating"] = trust_rating(d["rating"], d["votes"], m=m, c=c).values
    d["is_hidden_gem"] = flag_hidden_gems(d)
    return d


def flag_hidden_gems(df, min_votes=GEM_MIN_VOTES, max_votes=GEM_MAX_VOTES,
                     top_share=GEM_TOP_SHARE, min_locality=GEM_MIN_LOCALITY,
                     min_trust=GEM_MIN_TRUST):
    """Boolean Series (aligned with df): high trust within its locality, but few votes.

    Needs a `trust_rating` column (call add_trust first, or add it yourself)."""
    rated = df["trust_rating"].notna()
    n_in_loc = df[rated].groupby("locality")["trust_rating"].transform("size")
    pct = df[rated].groupby("locality")["trust_rating"].rank(pct=True, method="average")
    gem = pd.Series(False, index=df.index)
    ok = (
        df.loc[rated, "votes"].between(min_votes, max_votes)
        & (pct >= 1 - top_share)
        & (n_in_loc >= min_locality)
        & (df.loc[rated, "trust_rating"] >= min_trust)
    )
    gem.loc[ok.index] = ok
    return gem
