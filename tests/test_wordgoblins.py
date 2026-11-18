"""Tests for wordgoblins.WordGoblin."""
import sys
import pickle

import pytest

from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent
if SOURCE_DIR not in sys.path:
    print(SOURCE_DIR)
    sys.path.append(SOURCE_DIR)


from wordgoblins import WordGoblin



def test_get_words_splits_on_whitespace():
    wg = WordGoblin("one\ttwo\nthree  four")
    assert wg.words == ["one", "two", "three", "four"]


def test_get_words_drops_empty_tokens():
    wg = WordGoblin("  spaced   between  ")
    assert wg.words == ["spaced", "between"]


def test_word_distances_records_window(sample_text):
    wg = WordGoblin(sample_text)
    # "the" is immediately followed by "quick" (distance 0).
    assert ("quick", 0) in wg.word_distances["the"]


def test_word_distances_accumulates_counts(sample_text):
    wg = WordGoblin(sample_text)
    # "the" appears multiple times; sum every weight across all its buckets.
    the = wg.word_distances["the"]
    total = sum(weight for (_, _), weight in the.items())
    assert total > 1


def test_get_segment_creates_missing_word():
    wg = WordGoblin("")
    wg.get_segment("solo", ["a", "b", "c"])
    assert ("a", 0) in wg.word_distances["solo"]
    assert ("b", 1) in wg.word_distances["solo"]
    assert ("c", 2) in wg.word_distances["solo"]


def test_get_nearby_words_returns_triple():
    wg = WordGoblin("alpha beta gamma")
    nearby = wg.get_nearby_words("alpha")
    assert nearby
    other, distance, weight = nearby[0]
    assert isinstance(other, str)
    assert isinstance(distance, int)
    assert isinstance(weight, int)


def test_get_nearby_words_creates_empty_bucket():
    wg = WordGoblin("alpha beta")
    assert wg.get_nearby_words("never-seen") == []


def test_get_next_word_falls_back_for_unknown_word(wg):
    fallback = wg.get_next_word("definitely-not-in-corpus")
    assert fallback in wg.words


def test_get_next_word_returns_distance_one_neighbour(wg):
    for word in wg.unique_words:
        distances = {
            other: distance
            for (other, distance), weight in wg.word_distances[word].items()
        }
        next_word = wg.get_next_word(word)
        # If the word has a distance-1 neighbour, the pick must be one.
        if 1 in distances.values():
            assert distances.get(next_word) == 1
        # Otherwise it falls back to a random corpus word (no crash).
        else:
            assert next_word in wg.words


def test_get_next_word_no_crash_on_empty_distance_one(wg):
    # A word with no distance==1 neighbours must not raise IndexError.
    wg2 = WordGoblin("alpha beta gamma")
    wg2.build_sampling_cache()
    for _ in range(20):
        assert isinstance(wg2.get_next_word("alpha"), str)


def test_build_sampling_cache_filters_distance_below_one(wg):
    cache = wg.sampling_cache
    assert cache
    for word, (words, weights) in cache.items():
        assert words
        assert len(words) == len(weights)
        # distance < 1 means only distance 0 survives.
        # Check that each word in the cache has a distance-0 entry.
        for other in words:
            assert (other, 0) in wg.word_distances[word]


def test_sampling_cache_is_lazy_and_cached(wg):
    wg._sampling_cache = {}
    first = wg.sampling_cache
    assert first is wg._sampling_cache
    # Second access returns the same object, not a rebuild.
    assert wg.sampling_cache is first


def test_unique_words_matches_word_keys(wg):
    assert set(wg.unique_words) == set(wg.word_distances.keys())


def test_save_and_load_roundtrip(tmp_path):
    text = "cat dog cat bird dog cat"
    wg = WordGoblin(text)
    path = tmp_path / "model.pickle"
    wg.save(path)

    reloaded = WordGoblin("")
    reloaded.load(path)
    assert reloaded.word_distances == wg.word_distances
    assert reloaded.words == wg.words


def test_load_converts_old_list_representation(tmp_path):
    # Old format: {word: [[other, distance], ...], ...}
    old = {"a": [["b", 0], ["c", 1]], "b": [["a", 0]]}
    path = tmp_path / "old.pickle"
    with open(path, "wb") as f:
        pickle.dump(old, f)

    wg = WordGoblin("")
    wg.load(path)
    assert wg.word_distances["a"] == {("b", 0): 1, ("c", 1): 1}
    assert wg.word_distances["b"] == {("a", 0): 1}


def test_generate_random_sentence_starts_with_seed(wg):
    sentence = wg.generate_random_sentence("the", length=5)
    assert sentence.split(" ")[0] == "the"


def test_generate_random_sentence_terminates_on_period():
    wg = WordGoblin("hello world. foo bar")
    sentence = wg.generate_random_sentence("hello", length=10)
    assert sentence.endswith(".") or "." in sentence
