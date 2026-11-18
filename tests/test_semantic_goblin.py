"""Tests for semantic goblin — pattern extraction from text."""
import sys
from pathlib import Path

import pytest

SOURCE_DIR = Path(__file__).resolve().parent.parent
if SOURCE_DIR not in sys.path:
    sys.path.append(str(SOURCE_DIR))

from semantic_goblin import SemanticGoblin


# ── helpers ──────────────────────────────────────────────────────────────────

def _fact_keys(facts):
    """Return a set of (pattern_type, subject, predicate, object) tuples."""
    return {(f.pattern, f.subject, f.predicate, f.object) for f in facts}


# ── 1. Definitional patterns ─────────────────────────────────────────────────

class TestDefinitionalPatterns:
    """X is a/an Y  —  identity / category."""

    def test_simple_is_a(self):
        sg = SemanticGoblin("A bat is a mammal.")
        facts = sg.extract()
        assert ("is_a", "bat", "is_a", "mammal") in _fact_keys(facts)

    def test_is_a_with_article(self):
        sg = SemanticGoblin("The red fox is a carnivore.")
        facts = sg.extract()
        assert ("is_a", "red fox", "is_a", "carnivore") in _fact_keys(facts)

    def test_is_known_as(self):
        sg = SemanticGoblin("The red fox is known as Vulpes vulpes.")
        facts = sg.extract()
        assert ("known_as", "red fox", "known_as", "vulpes vulpes") in _fact_keys(facts)

    def test_refers_to(self):
        sg = SemanticGoblin("The word quantum refers to a discrete quantity.")
        facts = sg.extract()
        assert ("refers_to", "the word quantum", "refers_to", "discrete quantity") in _fact_keys(facts)


# ── 2. Relational patterns ───────────────────────────────────────────────────

class TestRelationalPatterns:
    """The X of Y  —  ownership / composition / association."""

    def test_capital_of(self):
        sg = SemanticGoblin("The capital of France is Paris.")
        facts = sg.extract()
        assert ("capital_of", "france", "has_capital", "paris") in _fact_keys(facts)

    def test_has_pattern(self):
        sg = SemanticGoblin("The car has four wheels.")
        facts = sg.extract()
        assert ("has", "car", "has", "four wheels") in _fact_keys(facts)

    def test_belongs_to(self):
        sg = SemanticGoblin("This book belongs to the library.")
        facts = sg.extract()
        assert ("belongs_to", "this book", "belongs_to", "library") in _fact_keys(facts)


# ── 3. Causal and temporal patterns ──────────────────────────────────────────

class TestCausalTemporalPatterns:
    def test_because(self):
        sg = SemanticGoblin("Because it rained, the match was canceled.")
        facts = sg.extract()
        assert ("because", "it rained", "caused", "match was canceled") in _fact_keys(facts)

    def test_leads_to(self):
        sg = SemanticGoblin("Poor diet leads to health issues.")
        facts = sg.extract()
        assert ("leads_to", "poor diet", "leads_to", "health issues") in _fact_keys(facts)

    def test_after(self):
        sg = SemanticGoblin("After the war, peace was declared.")
        facts = sg.extract()
        assert ("after", "war", "precedes", "peace was declared") in _fact_keys(facts)


# ── 4. Attribute patterns ────────────────────────────────────────────────────

class TestAttributePatterns:
    def test_is_adjective(self):
        sg = SemanticGoblin("The sky is blue.")
        facts = sg.extract()
        assert ("attribute", "sky", "has_property", "blue") in _fact_keys(facts)

    def test_has_property(self):
        sg = SemanticGoblin("The diamond has high hardness.")
        facts = sg.extract()
        assert ("has", "diamond", "has", "high hardness") in _fact_keys(facts)


# ── 5. Action patterns ───────────────────────────────────────────────────────

class TestActionPatterns:
    def test_agent_action_patient(self):
        sg = SemanticGoblin("The chef cooked the meal.")
        facts = sg.extract()
        assert ("action", "chef", "action", "cooked meal") in _fact_keys(facts)


# ── 6. Comparative patterns ──────────────────────────────────────────────────

class TestComparativePatterns:
    def test_more_than(self):
        sg = SemanticGoblin("The elephant is larger than the mouse.")
        facts = sg.extract()
        assert ("action", "elephant is larger", "action", "than mouse") in _fact_keys(facts)

    def test_superlative(self):
        sg = SemanticGoblin("The cheetah is the fastest land animal.")
        facts = sg.extract()
        assert ("superlative", "cheetah", "fastest", "land animal") in _fact_keys(facts)


# ── 7. Conditional patterns ──────────────────────────────────────────────────

class TestConditionalPatterns:
    def test_if_then(self):
        sg = SemanticGoblin("If it rains, the ground gets wet.")
        facts = sg.extract()
        assert ("conditional", "it rains", "implies", "ground gets wet") in _fact_keys(facts)


# ── 8. Multi-sentence extraction ─────────────────────────────────────────────

class TestMultiSentence:
    def test_multiple_sentences(self):
        text = (
            "A bat is a mammal. Bats can fly. "
            "The capital of France is Paris. "
            "Poor diet leads to health issues."
        )
        sg = SemanticGoblin(text)
        facts = sg.extract()
        keys = _fact_keys(facts)
        assert ("is_a", "bat", "is_a", "mammal") in keys
        assert ("can", "bats", "can", "fly") in keys
        assert ("capital_of", "france", "has_capital", "paris") in keys
        assert ("leads_to", "poor diet", "leads_to", "health issues") in keys


# ── 9. Empty / edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_text(self):
        sg = SemanticGoblin("")
        assert sg.extract() == []

    def test_no_patterns(self):
        sg = SemanticGoblin("The cat sat on the mat and slept.")
        facts = sg.extract()
        # Should return empty or minimal — no semantic pattern matched
        assert all(f.pattern not in ("is_a", "capital_of", "because") for f in facts)
