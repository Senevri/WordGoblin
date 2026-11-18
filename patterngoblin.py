"""PatternGoblin -- recognize structural 'the X of Y' templates.

A template recognizer that identifies the grammatical shape of 'the X of Y' 
patterns in text or from an existing WordGoblin .pickle model. 
It counts template occurrences and does not extract semantic relations.

Usage
-----
    # From raw text:
    goblin = PatternGoblin()
    goblin.feed("The art of war.")
    print(goblin.patterns)

    # From a pickle file:
    goblin = PatternGoblin.load_pickle("combined.pickle")
    patterns = goblin.extract_patterns_from_model()
    print(patterns)

Data model
----------
``patterns``  -- dict mapping ``(x_word, y_word, template) -> count``
    where ``template`` is a string \"the X of Y\", e.g. \"the art of war\".

``raw_patterns`` -- list of every match found, in order of occurrence:
    [(start_pos, end_pos, x_word, y_word, full_match), ...]

Class API
---------
- ``PatternGoblin()``            -- empty goblin (no data loaded)
- ``.feed(text)``                -- parse text and extract templates
- ``.load_pickle(path)``         -- class method: load a .pickle and scan it
- ``.extract_patterns_from_model()`` -- walk word_distances, yield patterns
- ``.get_templates()``           -- return unique templates sorted by count
- ``.show(top=20)``              -- print top N patterns as a table

Examples
--------
    >>> g = PatternGoblin.load_pickle("combined.pickle")
    >>> for tpl, count in g.show(10):
    ...     print(f"{count:>6}  {tpl}")
"""

from __future__ import annotations

import re
import string
import pickle
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Regex for 'the X of Y' pattern.
# - 'the' as a standalone word
# - X = one or more words ending before ' of '
# - 'of' as a standalone word
# - Y = next token (trailing punctuation stripped)
_PATTERN_RE = re.compile(
    r'\bthe\b\s+'              # 'the' + space
    r'(\S+(?:\s+\S+)*?)\s+'   # X: one or more words (non-greedy)
    r'of\b\s+'                 # 'of' + space
    r'(\S+)'                   # Y: next token
    , re.IGNORECASE
)

# Minimum word length to avoid noise like 'the a of b'
_MIN_WORD_LEN = 2


class PatternGoblin:
    """Recognize 'the X of Y' templates in text or goblin models."""

    def __init__(self):
        # {(x_word, y_word, template): count}
        self.patterns: Dict[Tuple[str, str, str], int] = {}
        # ordered list of (start, end, x, y, full_match) for positional context
        self.raw_patterns: List[Tuple[int, int, str, str, str]] = []

    # ------------------------------------------------------------------ #
    # Feeding data
    # ------------------------------------------------------------------ #
    def feed(self, text: str) -> "PatternGoblin":
        """Parse *text* and extract all 'the X of Y' templates.

        Returns self for chaining.
        """
        for m in _PATTERN_RE.finditer(text):
            # Check if this match is part of a relation clause (e.g., "the X of Y is Z")
            # If it is, we skip it to avoid duplicating SemanticGoblin's work.
            tail = text[m.end():].lstrip()
            if re.match(r"^(?:is|known as|refers to|refers)\b", tail, re.IGNORECASE):
                continue

            x_raw = m.group(1).strip()
            y_word = m.group(2)

            # Normalize: lowercase, strip markdown/formatting chars and punctuation
            def _clean(token: str) -> str:
                t = token.lower().strip(string.punctuation)
                return re.sub(r'[^a-z]', '', t)

            x_clean = _clean(x_raw)
            y_clean = _clean(y_word)

            # Filter very short noise words
            if len(x_clean) < _MIN_WORD_LEN or len(y_clean) < _MIN_WORD_LEN:
                continue

            template = f"the {x_clean} of {y_clean}"
            key = (x_clean, y_clean, template)
            self.patterns[key] = self.patterns.get(key, 0) + 1
            self.raw_patterns.append(
                (m.start(), m.end(), x_raw, y_word, template)
            )
        return self

    # ------------------------------------------------------------------ #
    # Loading from pickle models
    # ------------------------------------------------------------------ #
    @classmethod
    def load_pickle(cls, path: str | Path) -> "PatternGoblin":
        """Load a WordGoblin .pickle and scan it for patterns.

        Returns a fresh PatternGoblin with ``patterns`` populated.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot find pickle: {path}")

        with open(path, "rb") as f:
            data = pickle.load(f)

        # New format: (word_distances, words)
        word_distances = data.get("word_distances")
        words = data.get("words")

        if word_distances is None or words is None:
            raise ValueError(
                "Provide both word_distances and words, or use load_pickle()"
            )
        # Reconstruct text from words list
        text = " ".join(words)
        self.feed(text)
        return self

    # ------------------------------------------------------------------ #
    # Querying results
    # ------------------------------------------------------------------ #
    def get_templates(
        self, min_count: int = 1
    ) -> OrderedDict[str, int]:
        """Return unique templates sorted by frequency (desc), with optional filter."""
        filtered = {
            tpl: count
            for (x, y, tpl), count in self.patterns.items()
            if count >= min_count
        }
        # Sort descending by count, then alphabetically for stability
        return OrderedDict(
            sorted(filtered.items(), key=lambda item: (-item[1], item[0]))
        )

    def show(self, top: int = 20) -> List[Tuple[str, int]]:
        """Print top-N patterns and return them as list of (template, count)."""
        templates = self.get_templates()
        result = []
        for tpl, count in list(templates.items())[:top]:
            print(f"{count:>6}  {tpl}")
            result.append((tpl, count))
        return result

    def __len__(self) -> int:
        """Number of unique patterns."""
        return len(self.patterns)

    def __bool__(self) -> bool:
        return bool(self.patterns)

    def __repr__(self) -> str:
        n = len(self)
        return f"PatternGoblin(patterns={n}, total_matches={len(self.raw_patterns)})"


# ------------------------------------------------------------------ #
# CLI entry point
# ------------------------------------------------------------------ #
def _main():
    import argparse

    parser = argparse.ArgumentParser(
        description="PatternGoblin: extract 'the X of Y' patterns from text or pickles."
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Text file, pickle file (.pickle/.letterpickle), or '-' for stdin.",
    )
    parser.add_argument(
        "--top", "-n", type=int, default=20,
        help="Show only the top N patterns (default: 20).",
    )
    parser.add_argument(
        "--min-count", type=int, default=1,
        help="Minimum occurrences to show (default: 1).",
    )
    args = parser.parse_args()

    goblin = PatternGoblin()

    if args.input == "-":
        import sys
        text = sys.stdin.read()
        goblin.feed(text)
    elif args.input and Path(args.input).exists():
        p = Path(args.input)
        if p.suffix in (".pickle", ".letterpickle"):
            goblin = PatternGoblin.load_pickle(p)
        else:
            # Assume text file
            with open(p) as f:
                text = f.read()
            goblin.feed(text)
    else:
        import sys
        print("Reading from stdin...", file=sys.stderr)
        for line in sys.stdin:
            goblin.feed(line)

    if not goblin:
        print("No patterns found.", flush=True)
        return

    print(f"\nFound {goblin}:\n", flush=True)
    templates = goblin.get_templates(min_count=args.min_count)
    for tpl, count in list(templates.items())[:args.top]:
        print(f"{count:>6}  {tpl}")


if __name__ == "__main__":
    _main()
