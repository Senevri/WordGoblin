"""Two-word search over the combined word model.

Keeps wordgoblins.py untouched; this module reuses WordGoblin to walk the
weighted distance<1 association graph and emit coherent short phrases.
"""
import random
from pathlib import Path
from timeit import default_timer as timer

from wordgoblins import WordGoblin
from lettergoblins import LetterGoblin
from lettergoblins_fixed_final import LetterGoblin as LG2
from lettergoblins_fixed_v3 import LetterGoblin as LG3

def get_candidates(wg, start=None):
    nearby = wg.get_nearby_words(start)

    candidates = [
        (other, weight)
        for (other, distance, weight) in nearby
        if distance < 1 and other.strip()
    ]
    if not candidates:
        return None
    return candidates

def generate_two_word_phrase(wg, start=None):
    """Return a weighted (word1, word2) pair that actually co-occur.

    Candidates are neighbours at distance < 1 (the ones the sampler uses),
    filtered to real tokens, then chosen by frequency weight.
    """
    if start is None:
        if is_letter_goblin(wg):
            words = [w for w in wg.unique_words]
        else:
            words = [w for w in wg.unique_words if w]
        if not words:
            return None
        start = random.choice(words)

    candidates = get_candidates(wg, start)
    if candidates is None:
        return None

    words = [c[0] for c in candidates]
    weights = [c[1] for c in candidates]
    second = random.choices(words, weights=weights, k=1)[0]
    return (start, second)

def generate_n_word_phrase(wg, start=None, n=10)->list[str]:
    phrase = generate_two_word_phrase(wg, start=start)
    if phrase is None:
        return []

    sentence = [phrase[0]]
    word = phrase[1]
    sentence.append(word)

    while len(sentence) < n:
        candidates = get_candidates(wg, start)
        if candidates is None:
            break

        if not is_letter_goblin(wg):
            # Now what do we want to do?
            # 1. No uppercase words, except names, and we don't know about names.
            # 2. No "---", that's actionable
            pass

        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        word = random.choices(words, weights=weights, k=1)[0]
        sentence.append(word)
    return sentence


def generate_short_sentence(wg, start=None, max_words=8, n_words=2):
    """Walk the weighted distance<1 graph, stopping on sentence punctuation."""

    # phrase = generate_two_word_phrase(wg, start=start)
    phrase = generate_n_word_phrase(wg, start=start, n=n_words)
    if not phrase:
        return ""
    sentence = []
    if isinstance(phrase, list):
        sentence.append(phrase[0])
        word = phrase[1:] if len(phrase) > 1 else [str(phrase)]
        sentence.extend(word)
    else:
        sentence.append(phrase)

    while len(sentence) < max_words and not (
        word[-1][-1] in ".!?" or word[-1] in ".!?"
    ):
        if not isinstance(word, list):
            word = [word]
        candidates = [
            (other, weight)
            for (other, distance, weight) in wg.get_nearby_words(word[-1])
            if distance < 2 and other
        ]
        if not candidates and not is_letter_goblin(wg):
            candidates = [
                (other, weight)
                for (other, distance, weight) in wg.get_nearby_words(word[-1].split(" ")[-1])
                if distance < 2 and other.strip()
            ]
        if not candidates:
            # print("break")
            print(f"No candidates for {word[-1]}")
            break
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        word = random.choices(words, weights=weights, k=1)[0]
        sentence.append(word)
    if is_letter_goblin(wg):
        return "".join(sentence)
    return " ".join(sentence)

def is_letter_goblin(wg):
    return hasattr(wg, "letter_distances")

def two_word_search(picklefile=None,n=10, max_words=8):
    if picklefile:
        path = Path(picklefile)
        if not path.is_file():
            print(f"Missing {path} - run: python devour.py <dir> --level word")
            return
    else:
        path = Path("combined.pickle")
    if not path.is_file():
        print(f"Missing {path} - run: python devour.py <dir> --level word")
        return

    print(path, path.suffix)

    wg = None
    letters = False
    if path.suffix ==".pickle":
        wg = WordGoblin("")
    elif path.suffix ==".letterpickle":
        wg = LetterGoblin("")
        lg2 = LG2("")
        lg3 = LG3("")
        lg2.load(path)
        lg3.load(path)
        lg2.build_sampling_cache()
        lg3.build_sampling_cache()
        letters=True
    if not wg:
        exit(1)
    print(wg)
    wg.load(path)
    wg.build_sampling_cache()

    if hasattr(wg, "letter_distances"):
        print("Letter Goblin")
        for g in [wg, lg2, lg3]:
            if not any([" " in w for w in g.unique_words]):
                print("No space tokens")
                exit(1)
            print(f"space in {g.unique_words.index(' ')}")
    else:
        print("Word Goblin")

    for _ in range(n):
        print(f"{generate_two_word_phrase(wg)}")
    print("-" * 60)
    candidates = []
    for w in [w for w in wg.unique_words if w]:
        if str(w[0]).isupper():
            candidates.append(w)

    for _ in range(n):
        start_word = random.choice(candidates)
        print(generate_short_sentence(wg, start=start_word, max_words=max_words))
        if letters:
            print("2: " + generate_short_sentence(lg2, start=start_word, max_words=max_words))
            print("3: " + generate_short_sentence(lg3, start=start_word, max_words=max_words))

def n_word_search(picklefile=None,n=10, max_words=8, n_words=3):
    if picklefile:
        path = Path(picklefile)
        if not path.is_file():
            print(f"Missing {path} - run: python devour.py <dir> --level word")
            return
    else:
        path = Path("combined.pickle")
    if not path.is_file():
        print(f"Missing {path} - run: python devour.py <dir> --level word")
        return

    print(path, path.suffix)

    wg = None
    letters = False
    if path.suffix ==".pickle":
        wg = WordGoblin("")
    elif path.suffix ==".letterpickle":
        wg = LetterGoblin("")
        lg2 = LG2("")
        lg3 = LG3("")
        lg2.load(path)
        lg3.load(path)
        lg2.build_sampling_cache()
        lg3.build_sampling_cache()
        letters=True
    if not wg:
        exit(1)
    print(wg)
    wg.load(path)
    wg.build_sampling_cache()

    if is_letter_goblin(wg):
        print("Letter Goblin")
        for g in [wg, lg2, lg3]:
            if not any([" " in w for w in g.unique_words]):
                print("No space tokens")
                exit(1)
            print(f"space in {g.unique_words.index(' ')}")
    else:
        print("Word Goblin")

    # for _ in range(n):
    #     phrase = generate_n_word_phrase(wg, n=n_words)
    #     print("-" * 60)
    candidates = []
    for w in [w for w in wg.unique_words if w]:
        if str(w[0]).isupper():
            candidates.append(w)

    for _ in range(n):
        start_word = random.choice(candidates)
        print(generate_short_sentence(wg, start=start_word, max_words=max_words, n_words=n_words))
        if letters:
            print("2: " + generate_short_sentence(lg2, start=start_word, max_words=max_words, n_words=n_words))
            print("3: " + generate_short_sentence(lg3, start=start_word, max_words=max_words, n_words=n_words))



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("--picklefile", help="The pickle file or path to read", nargs="?", default=None)
    parser.add_argument("--max_words", type=int, default=8)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--n_words", type=int, default=2)


    args = parser.parse_args()
    #two_word_search(args.picklefile, args.n, args.max_words)
    start = timer()
    n_word_search(args.picklefile, args.n, args.max_words, n_words=3)
    stop = timer()
    print(f"Time: {stop-start}") # {stop-start)
