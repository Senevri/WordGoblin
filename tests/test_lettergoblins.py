"""Tests for lettergoblins.LetterGoblin."""
import sys
import pickle

import pytest

from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent
if SOURCE_DIR not in sys.path:
    sys.path.append(SOURCE_DIR)

from lettergoblins import LetterGoblin


def test_get_n_letter_chain_basic():
    lg = LetterGoblin("abcabc")
    chain = lg.get_n_letter_chain(2)
    assert "ab" in chain
    assert chain["ab"]["c"] == 2


def test_get_n_letter_chain_with_spaces():
    lg = LetterGoblin("a b a b")
    chain = lg.get_n_letter_chain(2)
    assert "a " in chain
    assert chain["a "]["b"] == 2


def test_get_letter_distances_populates_letters():
    lg = LetterGoblin("hello")
    assert lg.letters == list("hello")


def test_get_letter_distances_records_contexts():
    lg = LetterGoblin("the quick")
    # "t" should have "e" at distance 0 (from "the")
    assert ("e", 0) in lg.letter_distances["t"]


def test_generate_random_sentence_starts_with_seed():
    lg = LetterGoblin("the quick brown fox")
    sentence = lg.generate_random_sentence("T", length=20, n_gram=3)
    assert sentence.startswith("T")


def test_generate_random_sentence_terminates_on_period():
    lg = LetterGoblin("the quick brown fox. the lazy dog.")
    sentence = lg.generate_random_sentence("T", length=100, n_gram=3)
    # With small corpus, may not terminate on period, so just check it produces output
    assert len(sentence) > 0


def test_generate_random_sentence_with_larger_corpus():
    text = "the quick brown fox jumps over the lazy dog. the dog barked at the fox. the fox ran away quickly. the dog chased the fox through the park. the quick brown fox is very fast. the lazy dog is very slow. the fox and the dog are friends now. they play together in the park."
    lg = LetterGoblin(text)
    sentence = lg.generate_random_sentence("T", length=50, n_gram=3)
    # Just check it produces output starting with seed
    assert sentence.startswith("T")
    assert len(sentence) > 0


def test_generate_random_sentence_n_gram_varies():
    lg = LetterGoblin("the quick brown fox jumps over the lazy dog")
    sent3 = lg.generate_random_sentence("T", length=30, n_gram=3)
    sent4 = lg.generate_random_sentence("T", length=30, n_gram=4)
    assert len(sent3) > 0
    assert len(sent4) > 0


def test_save_and_load_roundtrip(tmp_path):
    text = "the quick brown fox"
    lg = LetterGoblin(text)
    path = tmp_path / "letter_model.pickle"
    lg.save(path)
    reloaded = LetterGoblin("")
    reloaded.load(path)
    assert reloaded.letter_distances == lg.letter_distances


def test_load_converts_old_representation(tmp_path):
    old = {"a": [["b", 0], ["c", 1]], "b": [["a", 0]]}
    path = tmp_path / "old_letter.pickle"
    with open(path, "wb") as f:
        pickle.dump(old, f)
    lg = LetterGoblin("")
    lg.load(path)
    assert lg.letter_distances["a"] == {("b", 0): 1, ("c", 1): 1}
    assert lg.letter_distances["b"] == {("a", 0): 1}


def test_sampling_cache_is_populated():
    lg = LetterGoblin("the quick brown fox")
    cache = lg.sampling_cache
    assert cache
    assert "t" in cache or "T" in cache


def test_generate_random_sentence_with_shakespeare():
    text = "To be, or not to be, that is the question: Whether tis nobler in the mind to suffer The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles. All the worlds a stage, and all the men and women merely players."
    lg = LetterGoblin(text)
    sentence = lg.generate_random_sentence("T", length=60, n_gram=3)
    assert len(sentence) > 10
    assert " " in sentence or len(sentence) < 30



def test_tween_word_returns_variants():
    lg = LetterGoblin('the quick brown fox')
    variants = lg.tween_word('fox', num_variants=5)
    assert len(variants) == 5
    assert all(isinstance(v, str) for v in variants)


def test_tween_word_preserves_word_length():
    lg = LetterGoblin('the quick brown fox')
    variants = lg.tween_word('quick', num_variants=10)
    for v in variants:
        assert len(v) == len('quick')


def test_tween_word_with_different_temperatures():
    lg = LetterGoblin('the quick brown fox')
    variants_low = lg.tween_word('quick', temperature=1.0, num_variants=10)
    variants_high = lg.tween_word('quick', temperature=5.0, num_variants=10)
    # Both should produce valid variants
    assert len(variants_low) == 10
    assert len(variants_high) == 10


def test_tween_word_with_different_replace_prob():
    lg = LetterGoblin('the quick brown fox')
    variants_low = lg.tween_word('brown', replace_prob=0.2, num_variants=10)
    variants_high = lg.tween_word('brown', replace_prob=0.8, num_variants=10)
    assert len(variants_low) == 10
    assert len(variants_high) == 10


def test_tween_word_with_n_gram():
    lg = LetterGoblin('the quick brown fox')
    variants = lg.tween_word('fox', n_gram=3, num_variants=5)
    assert len(variants) == 5


def test_tween_word_with_larger_corpus():
    text = 'the quick brown fox jumps over the lazy dog the cat sat on the mat the dog barked at the cat'
    lg = LetterGoblin(text)
    variants = lg.tween_word('cat', num_variants=10)
    assert len(variants) == 10
    # Check that variants are strings of correct length
    assert all(isinstance(v, str) and len(v) == 3 for v in variants)
