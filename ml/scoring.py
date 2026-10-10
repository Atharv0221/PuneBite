"""Trust-adjusted restaurant scores and Hidden Gems flags."""

import numpy as np
import pandas as pd


DEFAULT_PRIOR_WEIGHT = 50
DEFAULT_GEM_VOTE_MIN = 20
DEFAULT_GEM_VOTE_MAX = 200
DEFAULT_GEM_TOP_FRACTION = 0.15


def trust_adjusted_rating(rating, votes, prior_mean, prior_weight=DEFAULT_PRIOR_WEIGHT):
    """Shrink low-vote ratings toward the mean of all rated restaurants."""
    if pd.isna(rating):
        return np.nan
    vote_count = max(float(votes), 0.0) if pd.notna(votes) else 0.0
    if prior_weight <= 0:
        raise ValueError("prior_weight must be greater than zero")
    return (vote_count / (vote_count + prior_weight)) * float(rating) + (
        prior_weight / (vote_count + prior_weight)
    ) * float(prior_mean)


def add_trust_scores(
    restaurants,
    prior_weight=DEFAULT_PRIOR_WEIGHT,
    gem_vote_min=DEFAULT_GEM_VOTE_MIN,
    gem_vote_max=DEFAULT_GEM_VOTE_MAX,
    gem_top_fraction=DEFAULT_GEM_TOP_FRACTION,
):
    """Return a copy with trust ratings and within-locality Hidden Gems flags.

    Gems must have 20-200 votes and rank in the top 15% of rated restaurants
    in their locality by trust-adjusted rating.
    """
    if prior_weight <= 0:
        raise ValueError("prior_weight must be greater than zero")
    if not 0 <= gem_top_fraction <= 1:
        raise ValueError("gem_top_fraction must be between 0 and 1")
    if gem_vote_min < 0 or gem_vote_max < gem_vote_min:
        raise ValueError("gem vote bounds must satisfy 0 <= min <= max")

    result = restaurants.copy()
    ratings = pd.to_numeric(result["rating"], errors="coerce")
    votes = pd.to_numeric(result["votes"], errors="coerce").fillna(0).clip(lower=0)
    rated = ratings.notna()
    prior_mean = ratings[rated].mean()

    result["trust_rating"] = np.nan
    result.loc[rated, "trust_rating"] = (
        votes[rated] * ratings[rated] + prior_weight * prior_mean
    ) / (votes[rated] + prior_weight)
    result["hidden_gem"] = False

    rated_in_locality = rated & result["locality"].notna()
    locality_percentile = result.loc[rated_in_locality].groupby("locality")[
        "trust_rating"
    ].rank(method="min", pct=True)
    eligible = rated & votes.between(gem_vote_min, gem_vote_max)
    result.loc[locality_percentile.index, "hidden_gem"] = (
        eligible.loc[locality_percentile.index]
        & (locality_percentile >= 1 - gem_top_fraction)
    )
    return result
