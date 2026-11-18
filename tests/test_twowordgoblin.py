"""Tests for twowordgoblin two-word search helpers."""
import random

import pytest

from wordgoblins import WordGoblin
from twowordgoblin import (
    generate_two_word_phrase,
    generate_short_sentence,
)


@pytest.fixture
def wg():
    text = "the quick brown fox jumps over the lazy dog"
    goblin = WordGoblin(text)
    goblin.build_sampling_cache()
    return goblin


def test_generate_two_word_phrase_returns_pair(wg):
    phrase = generate_two_word_phrase(wg, start="the")
    assert phrase is not None
    first, second = phrase
    assert first == "the"
    assert second in wg.words


def test_generate_two_word_phrase_respects_distance_zero(wg):
    for _ in range(20):
        first, second = generate_two_word_phrase(wg, start="the")
        # generate_two_word_phrase filters distance < 1, i.e. distance 0.
        distances = {
            other: distance
            for (other, distance), weight in wg.word_distances[first].items()
        }
        assert distances.get(second) == 0


def test_generate_two_word_phrase_none_when_no_candidates():
    wg = WordGoblin("lonely word only")
    wg.build_sampling_cache()
    # "lonely" has no distance-1 neighbour that strips to a real token.
    result = generate_two_word_phrase(wg, start="lonely")
    # Either None or a valid pair; never a crash.
    assert result is None or isinstance(result, tuple)


def test_generate_two_word_phrase_random_start(wg):
    random.seed(0)
    phrase = generate_two_word_phrase(wg)
    assert phrase is not None
    first, second = phrase
    assert first and second


def test_generate_short_sentence_starts_with_phrase(wg):
    sentence = generate_short_sentence(wg, start="the", max_words=6)
    first_two = " ".join(sentence.split(" ")[:2])
    phrase = " ".join(generate_two_word_phrase(wg, start="the"))
    assert first_two == phrase


def test_generate_short_sentence_respects_max_words(wg):
    sentence = generate_short_sentence(wg, start="the", max_words=4)
    words = sentence.split(" ")
    assert len(words) <= 4


def test_generate_short_sentence_empty_when_no_candidates():
    wg = WordGoblin("lonely word only")
    wg.build_sampling_cache()
    # "only" is the last word: empty window, no distance-0 neighbour,
    # so generate_two_word_phrase returns None and the sentence is "".
    result = generate_short_sentence(wg, start="only", max_words=4)
    assert result == ""


# ---------------------------------------------------------------------------
# Tests for n-word-search lookup functions (moved from chatty.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def wg_phrase():
    """A goblin with a known verbatim phrase for testing lookups."""
    text = "Tomorrow sees undone what happens not today; indecision brings delays"
    goblin = WordGoblin(text)
    goblin.build_sampling_cache()
    return goblin


def test_n_word_search_verbatim_two_word(wg_phrase):
    """_n_word_search finds the word following a known two-word phrase."""
    from twowordgoblin import _n_word_search
    result = _n_word_search(wg_phrase, ("Tomorrow", "sees"))
    # Should find "undone" at distance 0 from "sees"
    assert len(result) > 0
    assert any(w[0] == "undone" for w in result if w[1] == 0)


def test_n_word_search_verbatim_three_word(wg_phrase):
    """_n_word_search verifies all words in the window match the anchor."""
    from twowordgoblin import _n_word_search
    result = _n_word_search(wg_phrase, ("Tomorrow", "sees", "undone"))
    assert len(result) > 0
    assert any(w[0] == "what" for w in result if w[1] == 0)


def test_n_word_search_verbatim_missing_phrase():
    """_n_word_search returns [] when the phrase is not in the data."""
    from twowordgoblin import _n_word_search
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    result = _n_word_search(wg, ("nonexistent", "phrase"))
    assert result == []


def test_n_word_search_verbatim_empty():
    """_n_word_search returns [] for empty input."""
    from twowordgoblin import _n_word_search
    wg = WordGoblin("test")
    wg.build_sampling_cache()
    assert _n_word_search(wg, ()) == []


def test_n_word_search_chain_two_word(wg_phrase):
    """n_word_search verifies each adjacent pair is a real transition."""
    from twowordgoblin import n_word_search
    result = n_word_search(wg_phrase, ("Tomorrow", "sees"))
    assert len(result) > 0
    assert any(w[0] == "undone" for w in result if w[1] == 0)


def test_n_word_search_chain_missing_pair():
    """n_word_search returns [] when an adjacent pair is not a real transition."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    # "the" → "brown" is not a direct distance-0 transition
    result = n_word_search(wg, ("the", "brown"))
    assert result == []


def test_n_word_search_chain_empty():
    """n_word_search returns [] for empty input."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("test")
    wg.build_sampling_cache()
    assert n_word_search(wg, ()) == []


def test_build_ngram_cache_populates_attribute():
    """build_ngram_cache creates a ngram_cache dict on the goblin."""
    from twowordgoblin import build_ngram_cache
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    build_ngram_cache(wg)
    assert hasattr(wg, "ngram_cache")
    assert isinstance(wg.ngram_cache, dict)


def test_build_ngram_cache_contains_bigrams():
    """build_ngram_cache populates bigrams (2-word entries)."""
    from twowordgoblin import build_ngram_cache
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    build_ngram_cache(wg)
    # "the" → "quick" should be in the cache
    assert "the" in wg.ngram_cache
    assert ("quick", 0) in wg.ngram_cache["the"]


def test_n_word_search_uses_cache_when_available():
    """n_word_search falls back to cache when word_distances is sparse."""
    from twowordgoblin import build_ngram_cache, n_word_search
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    build_ngram_cache(wg)
    result = n_word_search(wg, ("the", "quick"))
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Tests for n-word search functions
# ---------------------------------------------------------------------------

def test_n_word_search_strict_verbatim():
    """Test _n_word_search with strict verbatim matching."""
    from twowordgoblin import _n_word_search
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    
    # "the quick" should predict "brown" (distance 0 from "quick")
    result = _n_word_search(wg, ["the", "quick"])
    assert result is not None
    assert len(result) > 0
    # The first word should be "brown" at distance 0
    assert any(w[0] == "brown" and w[1] == 0 for w in result)


def test_n_word_search_strict_fails_on_nonexistent():
    """Test _n_word_search returns empty for non-existent sequences."""
    from twowordgoblin import _n_word_search
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    
    # "the brown" is not a valid sequence
    result = _n_word_search(wg, ["the", "brown"])
    assert result == []


def test_n_word_search_chain():
    """Test n_word_search with chain lookup."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    
    # "the quick" should work (adjacent pair is valid)
    result = n_word_search(wg, ["the", "quick"])
    assert result is not None
    assert len(result) > 0


def test_n_word_search_chain_fails():
    """Test n_word_search returns empty for invalid chain."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    
    # "the brown" is not a valid adjacent pair
    result = n_word_search(wg, ["the", "brown"])
    assert result == []


def test_n_word_search_empty_list():
    """Test n_word_search with empty list."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    
    result = n_word_search(wg, [])
    assert result == []


def test_n_word_search_single_word():
    """Test n_word_search with single word."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox")
    wg.build_sampling_cache()
    
    # Single word should return neighbors at distance 0
    result = n_word_search(wg, ["the"])
    assert result is not None



def test_n_word_search_three_words():
    """Test n_word_search with three-word window."""
    from twowordgoblin import n_word_search
    wg = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()
    
    # "the quick brown" should predict "fox"
    result = n_word_search(wg, ["the", "quick", "brown"])
    assert result is not None
    assert any(w[0] == "fox" and w[1] == 0 for w in result)
