"""TweenGoblin: recover the word *between* two words.

NEW module. It does NOT modify ``wordgoblins.WordGoblin`` (or anything else);
it reuses the ``word_distances`` model produced by ``WordGoblin`` verbatim.

Data model (inherited from WordGoblin)
--------------------------------------
``word_distances[word]`` maps ``(other_word, distance) -> weight`` where
``distance`` is the offset of ``other_word`` *after* ``word`` (0 == the word
that immediately follows ``word``).

Tween = "in between".  Given a training string "a b c", the keys are ``a`` and
``c`` and the recovered value is ``b`` -- the word wedged *between* them.  In
the model that means: ``b`` immediately follows ``a`` (``(b, 0)`` in
``word_distances[a]``) *and* ``c`` immediately follows ``b`` (``(c, 0)`` in
``word_distances[b]``).
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from wordgoblins import WordGoblin

# (word, weight)
Candidate = Tuple[str, int]

from logging import getLogger
logger = getLogger(__name__)


class TweenGoblin:
    """Recover the word(s) that sit *between* two bracketing words."""

    def __init__(self, word_distances: Dict[str, Dict[Tuple[str, int], int]]):
        # Accept a WordGoblin instance or a raw word_distances dict.
        if hasattr(word_distances, "word_distances"):
            self.word_distances = word_distances.word_distances # is goblin probably
        else:
            self.word_distances = word_distances

    def get_words(self, text) -> List[str]:
        # Uses a helpergoblin
        goblin = WordGoblin(text)
        goblin.get_word_distances(goblin.words)
        # pass to tweengoblin = combine dicts
        goblin.word_distances.update(self.word_distances)
        # Now we may have duplicates? Sort of?
        # structure = {(other_word, distance): weight}
        # Maybe it's fine?
        for k, v in goblin.word_distances.items():
            goblin.word_distances[k] = dict(sorted(v.items()))

        self.word_distances = goblin.word_distances
        logger.debug(f"Distances: {self.word_distances!r}")  #
        return goblin.words


    # ------------------------------------------------------------------ #
    # Tween (in-between) search  --  the headline feature
    # ------------------------------------------------------------------ #
    def tween_search(self, word_a: str, word_c: str) -> List[Candidate]:
        """Recover the in-between word of a 3-word sequence ``a b c``.

        Given two words ``word_a`` and ``word_c`` separated by exactly one
        word (the pattern ``a b c``), return every word ``b`` that can sit
        between them -- i.e. every ``b`` that *immediately follows* ``word_a``
        *and* for which ``word_c`` *immediately follows*.

        This is the "tween" / in-between lookup: the keys are ``a`` and ``c``,
        the recovered value is the word wedged between them.

        Returns a list of ``(b, weight)`` tuples sorted by weight descending.
        Returns ``[]`` when no such in-between word exists.
        """
        results: List[Candidate] = []
        # Immediate successors of a: words at distance 0 from word_a.
        for b, _dist, weight in self.get_nearby_words(word_a, 0):
            # b qualifies only if word_c immediately follows b.
            if (word_c, 0) in self.word_distances.get(b, {}):
                results.append((b, weight))
        results.sort(key=lambda item: -item[1])
        return results

    # ------------------------------------------------------------------ #
    # Thin wrapper mirroring WordGoblin's API
    # ------------------------------------------------------------------ #
    def get_nearby_words(self, word: str, max_distance: int = 8) -> List[Candidate]:
        if word not in self.word_distances:
            return []
        distances = self.word_distances[word]
        return [
            (other_word, distance, weight)
            for (other_word, distance), weight in distances.items()
            if distance <= max_distance
        ]
