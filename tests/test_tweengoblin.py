"""Unit tests for the TweenGoblin inbetween lookup (tweengoblin.py).

tween_search(a, c) recovers the word b in training text "...a b c...".
"""

import sys
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent.parent
if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wordgoblins import WordGoblin
from tweengoblin import TweenGoblin


class TestTweenGoblin(unittest.TestCase):
    def setUp(self):
        # "Tomorrow sees undone what happens not today"
        self.text = (
            "Tomorrow sees undone what happens not today; "
            "indecision brings delays, days lost lamenting lost days"
        )
        self.goblin = TweenGoblin(WordGoblin(self.text))

    def test_tween_recovers_inbetween(self):
        # Consecutive a b c -> tween_search(a, c) == b
        res = self.goblin.tween_search("Tomorrow", "undone")
        self.assertIn("sees", [x[0] for x in res])

        res = self.goblin.tween_search("sees", "what")
        self.assertIn("undone", [x[0] for x in res])

        res = self.goblin.tween_search("undone", "happens")
        self.assertIn("what", [x[0] for x in res])

        res = self.goblin.tween_search("what", "not")
        self.assertIn("happens", [x[0] for x in res])

    def test_tween_returns_word_and_weight(self):
        res = self.goblin.tween_search("sees", "what")
        self.assertTrue(res)
        # Candidate is a (word, weight) tuple.
        self.assertEqual(len(res[0]), 2)
        self.assertEqual(res[0][0], "undone")

    def test_tween_unknown_anchor(self):
        self.assertEqual(self.goblin.tween_search("zzz", "qqq"), [])

    def test_tween_never_bracketed(self):
        # c never appears after a -> no gap.
        self.assertEqual(self.goblin.tween_search("zzz", "today"), [])

    def test_tween_is_fast(self):
        words = [f"w{i}" for i in range(2000)]
        import time

        g = TweenGoblin(WordGoblin(" ".join(words)))
        start = time.perf_counter()
        g.tween_search(words[0], words[2])
        self.assertLess(time.perf_counter() - start, 0.05)


if __name__ == "__main__":
    unittest.main()
