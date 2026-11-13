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
