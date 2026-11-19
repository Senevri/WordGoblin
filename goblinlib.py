"""goblinlib - Common utilities shared across goblin modules."""
from __future__ import annotations
import random
from typing import List, Tuple, Optional, Dict, Any

Candidate = Tuple[str, int]
Candidate3 = Tuple[str, int, int]

def n_word_search(word_distances: Dict[str, Any], word_list: List[str]) -> List[Candidate]:
    """Predict the word(s) that follow word_list using chain validation.

    Each adjacent pair in word_list must be a real distance-0 transition.
    If the chain is valid, returns candidates at distance 0 from the last word.
    Returns [] when any pair is invalid or the list is empty.
    """
    if not word_list:
        return []
    anchor = word_list[0]
    wd = word_distances.get(anchor)
    if not wd:
        return []
    for i, target in enumerate(word_list[1:], start=1):
        if (target, i - 1) not in wd:
            return []
    last_word = word_list[-1]
    return [(w, d, wt) for (w, d), wt in word_distances.get(last_word, {}).items() if d == 0]


def get_nearby_words(word_distances: Dict[str, Any], word: str, max_distance: int = 8) -> List[Candidate3]:
    """Get words near word up to max_distance."""
    if word not in word_distances:
        return []
    distances = word_distances[word]
    return [
        (other_word, distance, weight)
        for (other_word, distance), weight in distances.items()
        if distance <= max_distance
    ]


def generate_short_sentence(
    word_distances: Dict[str, Any],
    start: str,
    max_words: int = 8,
    n_words: int = 2,
) -> str:
    """Generate a short sentence starting from start using n-word search."""
    sentence = [start]
    for _ in range(max_words):
        window = sentence[-n_words:]
        candidates = n_word_search(word_distances, window)
        if not candidates:
            break
        next_word = random.choices(
            [c[0] for c in candidates],
            weights=[c[2] for c in candidates],
            k=1,
        )[0]
        sentence.append(next_word)
    return " ".join(sentence)


def generate_n_word_phrase(
    word_distances: Dict[str, Any],
    n: int = 3,
    max_words: int = 8,
) -> str:
    """Generate a random n-word phrase."""
    unique_words = list(word_distances.keys())
    if not unique_words:
        return ""
    start_word = random.choice(unique_words)
    return generate_short_sentence(word_distances, start=start_word, max_words=max_words, n_words=n)


def is_letter_goblin(obj: Any) -> bool:
    """Check if obj is a LetterGoblin instance."""
    return hasattr(obj, "letter_distances")


def get_words(text: str) -> List[str]:
    """Split text into words, normalizing whitespace."""
    whitespace = [" ", "\t", "\n", "\r"]
    for key in whitespace:
        text = text.replace(key, " ")
    return [w for w in text.split(" ") if w]
