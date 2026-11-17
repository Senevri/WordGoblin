"""Demo of TweenGoblin: recover the word *between* two bracketing words.

Given a 3-word sequence "a b c", TweenGoblin treats a and c as the keys and
recovers b -- the word wedged between them. It reuses WordGoblin's
``word_distances`` model verbatim and does not modify it.

Note: this is the *in-between* lookup, distinct from two_word_search (which
takes two *preceding* words and predicts the third). Here a and c bracket the
recovered word: for "Tomorrow sees undone" the pair is (Tomorrow, undone) -> sees.
"""

import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wordgoblins import WordGoblin
from tweengoblin import TweenGoblin


def build_or_load():
    """Return a WordGoblin instance, preferring a prebuilt pickle."""
    candidates = [
        "diesirae_combined.pickle",
        "combined_prose_2.pickle",
        "combined_prose.pickle",
    ]
    for name in candidates:
        p = SCRIPT_ROOT / name
        if not p.exists():
            continue
        try:
            wg = WordGoblin("")
            if wg.load(str(p)):
                print(f"[model] loaded {name}")
                return wg
        except Exception as exc:
            print(f"[warn] could not load {name}: {exc}")
    print("[model] no pickle found; building from sample text")
    return WordGoblin(
        "Tomorrow sees undone what happens not today; indecision brings "
        "delays, days lost lamenting lost days"
    )


def demo_verbatim(wg):
    """Recover in-between words of a known 3-word sequence, verbatim."""
    print("\n=== Demo 1: recover the word between two bracketing words ===")
    goblin = TweenGoblin(wg)
    # (word_a, word_c, expected_in_between): a and c *bracket* the recovered word.
    examples = [
        ("Tomorrow", "undone", "sees"),
        ("sees", "what", "undone"),
        ("undone", "happens", "what"),
        ("happens", "today;", "not"),
        ("today;", "brings", "indecision"),
        ("days", "lamenting", "lost"),
    ]
    for a, c, expected in examples:
        results = goblin.tween_search(a, c)
        top = results[0][0] if results else "(none)"
        flag = "OK" if expected in [r[0] for r in results] else "miss"
        print(f"  {a!r:12} _ {c!r:12} -> {top!r:12}  [{flag}]")


def demo_corpus(wg):
    """Recover plausible in-between words from a trained corpus."""
    print("\n=== Demo 2: recover in-between words from a trained corpus ===")
    goblin = TweenGoblin(wg)
    pairs = [
        ("the", "night"),
        ("a", "day"),
        ("to", "the"),
        ("of", "the"),
        ("in", "the"),
    ]
    for a, c in pairs:
        results = goblin.tween_search(a, c)
        if results:
            print(f"  {a!r:8} _ {c!r:8} -> {[(r[0], r[1]) for r in results[:5]]}")
        else:
            print(f"  {a!r:8} _ {c!r:8} -> (no in-between word found)")


def main():
    # Demo 1 needs a model that contains the sample sentence verbatim.
    sample = (
        "Tomorrow sees undone what happens not today; indecision brings "
        "delays, days lost lamenting lost days"
    )
    demo_verbatim(WordGoblin(sample))

    # Demo 2 uses a larger trained corpus.
    wg = build_or_load()
    demo_corpus(wg)

    print("\nDone. TweenGoblin recovers the word wedged between two words.")


if __name__ == "__main__":
    main()
