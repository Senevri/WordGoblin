#!/usr/bin/env python3
"""
Test cases for IdiomGoblin.
"""

import unittest
import re
from idiomgoblins import IdiomGoblin


class TestIdiomGoblin(unittest.TestCase):

    def setUp(self):
        self.idiom_goblin = IdiomGoblin()
        self.idiom_goblin.train("idioms.md")
        
        # Add specific patterns for testing
        self.idiom_goblin.add_idiom_pattern("kick the bucket", re.compile(r"kick the bucket", re.IGNORECASE))
        self.idiom_goblin.add_idiom_pattern("kick the bucket!", re.compile(r"kick the bucket!", re.IGNORECASE))
        self.idiom_goblin.add_idiom_pattern("think about it", re.compile(r"think about it", re.IGNORECASE))
        self.idiom_goblin.add_idiom_pattern("break a leg", re.compile(r"break a leg", re.IGNORECASE))

    def test_exact_idiom_match(self):
        """Test exact idiom match."""
        result = self.idiom_goblin.preprocess_text("He kicked the bucket last year.")
        self.assertIn("idiom", result)
        self.assertIn("meaning", result)
        self.assertIn("processed_text", result)
        self.assertEqual(result["idiom"], "kick the bucket")

    def test_variable_parts(self):
        """Test idioms with variable parts."""
        result = self.idiom_goblin.preprocess_text("She thinks about it often.")
        self.assertEqual(result["processed_text"], "She thinks about it often.")

        # Test a specific pattern
        self.idiom_goblin.add_idiom_pattern("think_about_it", re.compile(r"think about it", re.IGNORECASE))
        result = self.idiom_goblin.preprocess_text("She thinks about it.")
        self.assertEqual(result["idiom"], "think_about_it")

    def test_punctuation_handling(self):
        """Test handling of idioms with punctuation."""
        result = self.idiom_goblin.preprocess_text("He kicked the bucket!")
        self.assertEqual(result["idiom"], "kick the bucket!")

    def test_no_match(self):
        """Test text with no idiom match."""
        result = self.idiom_goblin.preprocess_text("This text has no idioms.")
        self.assertEqual(result, {"processed_text": "This text has no idioms."})

    def test_break_a_leg(self):
        """Test the 'break a leg' idiom."""
        result = self.idiom_goblin.preprocess_text("Break a leg!")
        self.assertEqual(result["idiom"], "break a leg")

    def test_meaning_lookup(self):
        """Test if the meaning is correctly retrieved."""
        result = self.idiom_goblin.preprocess_text("He kicked the bucket last year.")
        self.assertIsNotNone(result["meaning"])


if __name__ == "__main__":
    unittest.main()