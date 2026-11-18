import sys
from pathlib import Path
import unittest
from patterngoblin import PatternGoblin

SCRIPT_DIR = Path.cwd().resolve().parent.parent
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

class TestPatternGoblin(unittest.TestCase):
    def test_template_recognition(self):
        """Test that standard templates are recognized."""
        g = PatternGoblin()
        g.feed("The art of war.")
        templates = g.get_templates()
        self.assertIn("the art of war", templates)
        self.assertEqual(templates["the art of war"], 1)
        print("[PASS] test_template_recognition: Standard templates are recognized")

    def test_no_relation_duplication(self):
        """
        Test that relation clauses are NOT matched as templates.
        This is the core of the specialization to avoid duplication with SemanticGoblin.
        """
        g = PatternGoblin()
        # "the capital of France is Paris" is a relation clause.
        # PatternGoblin should skip it to avoid duplicating SemanticGoblin's of_is.
        g.feed("The capital of France is Paris.")
        templates = g.get_templates()
        self.assertNotIn("the capital of france", templates)
        print("[PASS] test_no_relation_duplication: Relation clauses are not matched as templates")

    def test_multiple_occurrences(self):
        """Test that multiple occurrences are counted correctly."""
        g = PatternGoblin()
        g.feed("The art of war. The art of war!")
        templates = g.get_templates()
        self.assertEqual(templates["the art of war"], 2)
        print("[PASS] test_multiple_occurrences: Multiple occurrences are counted correctly")

    def test_noise_filtering(self):
        """Test that very short words are filtered out."""
        g = PatternGoblin()
        # _MIN_WORD_LEN is 2. "a" and "b" are too short.
        g.feed("The a of b.")
        self.assertEqual(len(g), 0)
        print("[PASS] test_noise_filtering: Very short words are filtered out")

    def test_empty_input(self):
        """Test empty input."""
        g = PatternGoblin()
        g.feed("")
        self.assertEqual(len(g), 0)
        print("[PASS] test_empty_input: Empty input is handled correctly")

if __name__ == "__main__":
    unittest.main()
