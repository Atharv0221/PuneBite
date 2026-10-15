"""Tests for ml/scoring.py (trust-adjusted rating and hidden gems). Run from the project root:
    python -m unittest tests.test_scoring -v
"""
import unittest

import numpy as np
import pandas as pd

from ml.scoring import MAX_VOTES, MIN_RATING, MIN_VOTES, add_scores, beats_percent, trust_rating


def sample_restaurants():
    """40 ordinary restaurants (ratings 3.3-3.5, 20-29 votes) plus a few special cases."""
    ordinary = pd.DataFrame({
        "locality": "A",
        "rating": ([3.3, 3.4, 3.5] * 14)[:40],
        "votes": [20 + i % 10 for i in range(40)],
    })
    special = pd.DataFrame([
        {"locality": "A", "rating": 4.7, "votes": 25},      # far above peers, few votes -> GEM
        {"locality": "A", "rating": 3.6, "votes": 25},      # above peers but below the 3.8 floor -> no gem
        {"locality": "A", "rating": 4.8, "votes": 1500},    # excellent but already famous -> no gem
        {"locality": "B", "rating": np.nan, "votes": 0},    # unrated -> no scores at all
    ])
    df = pd.concat([ordinary, special], ignore_index=True)
    df["has_rating"] = df["rating"].notna()
    return df


class TrustRatingTests(unittest.TestCase):
    def test_no_votes_means_the_pune_average(self):
        self.assertAlmostEqual(float(trust_rating([5.0], [0], m=20, c=3.4)[0]), 3.4)

    def test_many_votes_keep_the_rating(self):
        score = float(trust_rating([3.0], [1000], m=20, c=3.4)[0])
        self.assertAlmostEqual(score, 3.0, delta=0.02)

    def test_few_votes_pull_towards_the_average_but_not_past_it(self):
        score = float(trust_rating([5.0], [50], m=20, c=3.4)[0])
        self.assertGreater(score, 3.4)
        self.assertLess(score, 5.0)

    def test_default_average_is_the_mean_rating(self):
        s = trust_rating([4.0, 3.0], [0, 0])
        self.assertAlmostEqual(float(s[0]), 3.5)


class HiddenGemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = sample_restaurants()
        cls.scored = add_scores(cls.df)

    def flag(self, i):
        return bool(self.scored.loc[i, "hidden_gem"])

    def test_the_outlier_with_few_votes_is_a_gem(self):
        self.assertTrue(self.flag(40))

    def test_good_but_below_the_rating_floor_is_not_a_gem(self):
        self.assertLess(3.6, MIN_RATING)
        self.assertFalse(self.flag(41))

    def test_famous_restaurants_are_not_gems(self):
        self.assertGreater(1500, MAX_VOTES)
        self.assertFalse(self.flag(42))

    def test_unrated_restaurants_get_no_scores(self):
        self.assertFalse(self.flag(43))
        self.assertTrue(np.isnan(self.scored.loc[43, "trust_rating"]))
        self.assertTrue(np.isnan(self.scored.loc[43, "peer_z"]))

    def test_gems_always_respect_the_vote_window(self):
        gems = self.scored[self.scored["hidden_gem"]]
        self.assertTrue(gems["votes"].between(MIN_VOTES, MAX_VOTES).all())

    def test_gem_rank_in_locality(self):
        self.assertEqual(self.scored.loc[40, "gem_rank_locality"], 1.0)

    def test_input_is_not_modified(self):
        self.assertNotIn("hidden_gem", self.df.columns)


class BeatsPercentTests(unittest.TestCase):
    def test_average_restaurant_beats_half(self):
        self.assertEqual(beats_percent(0), 50)

    def test_is_capped_at_99(self):
        self.assertEqual(beats_percent(10), 99)

    def test_is_increasing(self):
        self.assertLess(beats_percent(1.0), beats_percent(2.0))


if __name__ == "__main__":
    unittest.main()
