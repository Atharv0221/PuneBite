import unittest

import numpy as np
import pandas as pd

from ml.scoring import add_trust_scores, trust_adjusted_rating


class TrustScoringTests(unittest.TestCase):
    def test_trust_score_shrinks_low_vote_rating_toward_prior(self):
        score = trust_adjusted_rating(5.0, 0, 3.4)
        self.assertAlmostEqual(score, 3.4)
        self.assertGreater(trust_adjusted_rating(5.0, 50, 3.4), 3.4)
        self.assertLess(trust_adjusted_rating(5.0, 50, 3.4), 5.0)

    def test_hidden_gems_use_locality_rating_percentile_and_vote_window(self):
        restaurants = pd.DataFrame(
            {
                "locality": ["A"] * 8,
                "rating": [4.9, 4.8, 4.7, 4.6, 4.5, 4.4, 4.3, np.nan],
                "votes": [200, 25, 500, 700, 900, 1000, 1100, 50],
            }
        )

        scored = add_trust_scores(restaurants)

        self.assertTrue(scored.loc[0, "hidden_gem"])
        self.assertFalse(scored.loc[1, "hidden_gem"])
        self.assertFalse(scored.loc[2, "hidden_gem"])
        self.assertFalse(scored.loc[7, "hidden_gem"])
        self.assertTrue(np.isnan(scored.loc[7, "trust_rating"]))

    def test_missing_votes_are_treated_as_zero_votes(self):
        restaurants = pd.DataFrame(
            {"locality": ["A", "A"], "rating": [4.0, 3.0], "votes": [np.nan, 10]}
        )
        scored = add_trust_scores(restaurants)
        self.assertAlmostEqual(scored.loc[0, "trust_rating"], restaurants["rating"].mean())
        self.assertFalse(scored["hidden_gem"].any())


if __name__ == "__main__":
    unittest.main()
