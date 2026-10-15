"""Tests for backend/stats.py. Run from the project root:
    python -m unittest tests.test_stats -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import stats  # noqa: E402
from ml.scoring import VOTE_LABELS  # noqa: E402


class VoteBandTests(unittest.TestCase):
    def test_band_edges(self):
        cases = {0: "0-4", 4: "0-4", 5: "5-9", 19: "10-19", 20: "20-29", 99: "50-99",
                 100: "100-199", 999: "500-999", 1000: "1000+", 50000: "1000+"}
        for votes, label in cases.items():
            self.assertEqual(stats.vote_band(votes), label, votes)

    def test_missing_votes_count_as_zero(self):
        self.assertEqual(stats.vote_band(None), "0-4")

    def test_same_bands_as_the_scoring_module(self):
        self.assertEqual([label for _, _, label in stats.VOTE_BANDS], list(VOTE_LABELS))


class HistogramTests(unittest.TestCase):
    def test_fifteen_bands_from_two_to_five(self):
        h = stats.rating_histogram([])
        self.assertEqual(len(h), 15)
        self.assertEqual((h[0]["lo"], h[0]["hi"], h[-1]["lo"], h[-1]["hi"]), (2.0, 2.2, 4.8, 5.0))

    def test_boundaries_go_to_the_upper_band(self):
        h = {x["lo"]: x["count"] for x in stats.rating_histogram([4.0, 4.1, 4.2, 3.9])}
        self.assertEqual((h[3.8], h[4.0], h[4.2]), (1, 2, 1))

    def test_out_of_range_ratings_are_clamped(self):
        h = stats.rating_histogram([1.0, 5.0])
        self.assertEqual((h[0]["count"], h[-1]["count"]), (1, 1))

    def test_nothing_is_lost(self):
        ratings = [2.5, 3.1, 3.1, 4.9, 5.0, 1.5]
        self.assertEqual(sum(x["count"] for x in stats.rating_histogram(ratings)), len(ratings))


class CurveAndGapTests(unittest.TestCase):
    ROWS = [
        {"rating": 3.0, "votes": 2, "amenities": ["outdoor_seating"], "locality": "A"},
        {"rating": 3.2, "votes": 3, "amenities": [], "locality": "A"},
        {"rating": 4.0, "votes": 60, "amenities": ["outdoor_seating"], "locality": "B"},
        {"rating": 4.2, "votes": 70, "amenities": [], "locality": "B"},
        {"rating": None, "votes": 0, "amenities": ["outdoor_seating"], "locality": "B"},
    ]

    def test_votes_curve_skips_unrated_and_empty_bands(self):
        self.assertEqual(stats.votes_curve(self.ROWS),
                         [{"band": "0-4", "avg": 3.1}, {"band": "50-99", "avg": 4.1}])

    def test_amenity_gap_overall_and_popular(self):
        self.assertEqual(stats.amenity_gap(self.ROWS, "outdoor_seating"), [3.5, 3.7])
        self.assertEqual(stats.amenity_gap(self.ROWS, "outdoor_seating", min_votes=50), [4.0, 4.2])

    def test_amenity_gap_with_an_empty_group(self):
        self.assertEqual(stats.amenity_gap(self.ROWS, "rooftop"), [None, 3.6])

    def test_median_by(self):
        rows = [{"k": "a", "v": 1}, {"k": "a", "v": 5}, {"k": "a", "v": 3}, {"k": "b", "v": None}, {"k": "b", "v": 7}]
        self.assertEqual(stats.median_by(rows, "k", "v"), {"a": 3, "b": 7})


class LocalityRankingTests(unittest.TestCase):
    def test_small_localities_are_ignored_and_worst_starts_with_the_weakest(self):
        rows = ([{"locality": "Top", "rating": 4.0}] * 5 + [{"locality": "Mid", "rating": 3.5}] * 5
                + [{"locality": "Low", "rating": 3.0}] * 5 + [{"locality": "Tiny", "rating": 5.0}] * 2)
        best, worst = stats.locality_ranking(rows, min_rated=5, n=2)
        self.assertEqual([x["name"] for x in best], ["Top", "Mid"])
        self.assertEqual([x["name"] for x in worst], ["Low", "Mid"])


if __name__ == "__main__":
    unittest.main()
