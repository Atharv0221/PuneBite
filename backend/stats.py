"""Small statistics helpers used by the API.

They are plain Python functions that take lists of dictionaries (the documents read
from MongoDB), so they can be unit-tested without a database or a web server.
"""
from collections import defaultdict
from statistics import median

# Same vote bands as ml/scoring.py (VOTE_LABELS); a test keeps the two in sync.
VOTE_BANDS = [
    (0, 4, "0-4"), (5, 9, "5-9"), (10, 19, "10-19"), (20, 29, "20-29"), (30, 49, "30-49"),
    (50, 99, "50-99"), (100, 199, "100-199"), (200, 499, "200-499"), (500, 999, "500-999"),
    (1000, None, "1000+"),
]


def vote_band(votes):
    v = int(votes or 0)
    for lo, hi, label in VOTE_BANDS:
        if v >= lo and (hi is None or v <= hi):
            return label
    return VOTE_BANDS[0][2]


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def rating_histogram(ratings, floor=2.0, ceil=5.0, width=0.2):
    """Number of restaurants in each 0.2-star band between floor and ceil.

    Works in integer tenths of a star so that e.g. 4.2 can never land in the wrong
    band because of floating-point error. Ratings below `floor` join the first band
    and a perfect 5.0 joins the last one.
    """
    step = int(round(width * 10))
    lo_t, hi_t = int(round(floor * 10)), int(round(ceil * 10))
    counts = defaultdict(int)
    for r in ratings:
        t = min(max(int(round(float(r) * 10)), lo_t), hi_t - 1)
        counts[(t - lo_t) // step] += 1
    out = []
    for i in range((hi_t - lo_t) // step):
        lo = (lo_t + i * step) / 10
        hi = (lo_t + (i + 1) * step) / 10
        out.append({"bin": f"{lo:.1f}-{hi:.1f}", "lo": lo, "hi": hi, "count": counts.get(i, 0)})
    return out


def votes_curve(rows):
    """Average rating of rated restaurants in each vote band (shows that votes and rating go together)."""
    total, n = defaultdict(float), defaultdict(int)
    for row in rows:
        if row.get("rating") is None:
            continue
        band = vote_band(row.get("votes"))
        total[band] += float(row["rating"])
        n[band] += 1
    return [{"band": label, "avg": round(total[label] / n[label], 2)}
            for _, _, label in VOTE_BANDS if n[label]]


def median_by(rows, key, value):
    """{row[key]: median of row[value]} ignoring missing values."""
    groups = defaultdict(list)
    for row in rows:
        if row.get(key) is not None and row.get(value) is not None:
            groups[row[key]].append(float(row[value]))
    return {k: median(v) for k, v in groups.items()}


def amenity_gap(rows, amenity, min_votes=0):
    """[average rating WITH the amenity, average rating WITHOUT it] among rated restaurants
    that have at least `min_votes` votes. A value is None when a group is empty."""
    with_a, without_a = [], []
    for row in rows:
        if row.get("rating") is None or (row.get("votes") or 0) < min_votes:
            continue
        (with_a if amenity in (row.get("amenities") or []) else without_a).append(float(row["rating"]))
    return [_round(_mean(with_a)), _round(_mean(without_a))]


def _round(x, digits=2):
    return None if x is None else round(x, digits)


def locality_ranking(rows, min_rated=90, n=4):
    """(best, worst) localities by average rating, only counting localities with enough rated
    restaurants (90+ keeps roughly the 30 largest localities, so tiny areas cannot top the list).
    `worst` is ordered from the weakest upwards."""
    by_loc = defaultdict(list)
    for row in rows:
        if row.get("rating") is not None and row.get("locality"):
            by_loc[row["locality"]].append(float(row["rating"]))
    ranked = sorted(
        ((k, sum(v) / len(v)) for k, v in by_loc.items() if len(v) >= min_rated),
        key=lambda kv: (-kv[1], kv[0]),            # sort on the unrounded mean, then by name
    )
    as_row = lambda kv: {"name": kv[0], "avg": round(kv[1], 2)}
    return [as_row(x) for x in ranked[:n]], [as_row(x) for x in list(reversed(ranked))[:n]]


def insight_figures(rows, popular_votes=50, min_rated_locality=90, n=4):
    """The numbers behind the 'Four things we learned' cards, computed from the database."""
    best, worst = locality_ranking(rows, min_rated=min_rated_locality, n=n)
    return {
        "outdoor": {"overall": amenity_gap(rows, "outdoor_seating"),
                    "popular": amenity_gap(rows, "outdoor_seating", popular_votes)},
        "booking": {"overall": amenity_gap(rows, "table_booking_recommended"),
                    "popular": amenity_gap(rows, "table_booking_recommended", popular_votes)},
        "best": best,
        "worst": worst,
    }
