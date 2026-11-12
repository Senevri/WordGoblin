"""Two-word search over the combined word model.

Keeps wordgoblins.py untouched; this module reuses WordGoblin to walk the
weighted distance<1 association graph and emit coherent short phrases.
"""
import random
from pathlib import Path

from wordgoblins import WordGoblin


def generate_two_word_phrase(wg, start=None):
    """Return a weighted (word1, word2) pair that actually co-occur.

    Candidates are neighbours at distance < 1 (the ones the sampler uses),
    filtered to real tokens, then chosen by frequency weight.
    """
    if start is None:
        words = [w for w in wg.unique_words if w and w.strip()]
        if not words:
            return None
        start = random.choice(words)

    nearby = wg.get_nearby_words(start)
    candidates = [
        (other, weight)
        for (other, distance, weight) in nearby
        if distance < 1 and other.strip()
    ]
    if not candidates:
        return None

    words = [c[0] for c in candidates]
    weights = [c[1] for c in candidates]
    second = random.choices(words, weights=weights, k=1)[0]
    return (start, second)


def generate_short_sentence(wg, start=None, max_words=8):
    """Walk the weighted distance<1 graph, stopping on sentence punctuation."""
    phrase = generate_two_word_phrase(wg, start=start)
    if phrase is None:
        return ""
    sentence = [phrase[0]]
    word = phrase[1]
    sentence.append(word)

    while len(sentence) < max_words and not (
        word[-1] in ".!?" or word.endswith(".") or word == "."
    ):
        candidates = [
            (other, weight)
            for (other, distance, weight) in wg.get_nearby_words(word)
            if distance < 1 and other.strip()
        ]
        if not candidates:
            break
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        word = random.choices(words, weights=weights, k=1)[0]
        sentence.append(word)

    return " ".join(sentence)


def two_word_search(n=10, max_words=8):
    path = Path("combined.pickle")
    if not path.is_file():
        print(f"Missing {path} - run: python devour.py <dir> --level word")
        return

    wg = WordGoblin("")
    wg.load(path)
    wg.build_sampling_cache()

    for _ in range(n):
        print(f"{generate_two_word_phrase(wg)}")
    print("-" * 60)
    for _ in range(n):
        print(generate_short_sentence(wg, max_words=max_words))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("--max_words", type=int, default=8)
    parser.add_argument("--n", type=int, default=10)

    args = parser.parse_args()
    two_word_search(args.n, args.max_words)
