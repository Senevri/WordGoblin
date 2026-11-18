import sys
import random
import pytest
from typing import List, Tuple
from pathlib import Path
Candidate = Tuple[str, int, int]
from timeit import default_timer as timer
import time
SCRIPT_ROOT = Path(__file__).resolve().parent.parent

if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wordgoblins import WordGoblin

def test_two_word_search():
    wg = WordGoblin("Tomorrow sees undone what happens not today; indecision brings delays, days lost lamenting lost days")
    wg.get_words("Tomorrow was a day just like the rest of them")

    #wg.load("combined.pickle")
    wg.save("tomorrow_sees.pickle")
    wg.build_sampling_cache()
    input_tests = {
        ("Tomorrow", "sees"): "undone",
        ("undone", "what"): "happens",
        ("happens", "not"): "today;",
        ("today;", "indecision"): "brings",
        ("indecision", "brings"): "delays,",
        ("delays,", "days"): "lost",
        ("lost", "lamenting"): "lost",
        ("lamenting", "lost"): "days",
    }

    for k, v in input_tests.items():
        print(f"Data {k}: {v}")#, k,v)
        res:list = two_word_search(wg, k)
        print(res, end="")
        assert v in [x[0] for x in res if x[1] == 0]
        print ("✅")
    return wg


def two_word_search(wg, word_tuple):
    # find third word based on two preceding words
    sentence = []
    _word = word_tuple[0]
    #print(_word)
        # find second word
    words = wg.get_nearby_words(_word, 0)
    #print(f"words, {_word}:", words)
    if not words:
        return None
    #print(words)
    word2 = word_tuple[1]

    wd = wg.word_distances[_word]
    for tw in wd:
        if word2 == tw[0]:
            return wg.get_nearby_words(tw[0], 0)
        _word = tw[0]

def n_word_search(wg, word_list: List[str]) -> List[Candidate]:
    """Return the word(s) that follow word_list verbatim.

    Position-aware: finds every place word_list appears as a *consecutive*
    run in wg.words and returns the word(s) that follow those runs,
    weighted by frequency. Returns [] when the phrase does not appear
    verbatim. This is what makes known phrases reproduce verbatim -- unlike
    WordGoblin.get_nearby_words which aggregates distances across every
    context of a word and loses position information.
    """
    if not word_list:
        return []
    words = getattr(wg, "words", [])
    if not words:
        return []
    n = len(word_list)
    followers: dict = {}
    for pos, w in enumerate(words):
        if w != word_list[0]:
            continue
        if pos + n > len(words):
            continue
        if words[pos:pos + n] != word_list:
            continue
        nxt = pos + n
        if nxt < len(words):
            followers[words[nxt]] = followers.get(words[nxt], 0) + 1
    return [(w, 0, c) for w, c in followers.items()]


def test():
    wg = None
    try:
        wg = test_two_word_search()
    except Exception as e:
        print(e)
        print(wg)
    if not wg:
        exit(1)
    print("-"*80)
    wg.load("prose_hifi/alien-log.pickle")
    wg.build_sampling_cache()
    print (len(wg.unique_words))
    word_tuple = ("I", "am")
    for i in word_tuple:
        print(f"<{i}>")
        print(", ".join([f"{x[0]}: {x[2]}" for x in wg.get_nearby_words(i, 0)]), end=" ")
        print(f"\n</{i}>")

    print (" ".join(word_tuple), end=" ")
    for j in range(20):
        sequence = list(word_tuple)
        for i in range(20):
            result = two_word_search(wg, word_tuple)
            if result:
                result = [w for w in result if w[0] not in sequence]
                #print(result)
                weights = [w[2] for w in result]
                choices = [w[0] for w in result]
                #print(len(weights), len(choices))
                try:
                    word_tuple = (word_tuple[1], random.choices(choices, weights=weights, k=1)[0]) # (word_tuple[1], result[0])
                except IndexError as e:
                    print((weights, choices, word_tuple, e))

            #print (word_tuple[1], end=" ")
            sequence.append(word_tuple[1])
            if word_tuple[1][-1] in (".","!","?"):
                break
        print (" ".join(sequence))

def test_n_word_search(wg, phrase=""):
    """n_word_search must return the verbatim continuation of a known phrase.

    Loads the alien-log model, then for several phrases that appear verbatim
    in the training text asserts that the word immediately after the window
    (distance 0 from the last word) matches the original text.
    """
    wg.load("prose_hifi/alien-log.pickle")
    wg.build_sampling_cache()
    print("unique_words:", len(wg.unique_words))

    # (phrase, expected_next_word) pairs taken verbatim from the training text.
    known = [
        ("You know", "that"),
        ("You know that", "feeling"),
        ("that feeling", "when"),
    ]
    for phrase, expected in known:
        word_list = phrase.split(" ")
        result = n_word_search(wg, word_list)
        next_words = [w for (w, _d, _w) in result]
        print(f"{phrase!r} -> {next_words} (expected {expected!r})")
        assert expected in next_words, (phrase, expected, next_words)
        print("OK")

def tiny_nwx_test():
    # 1. Added a period so the punctuation break actually works!
    wg = WordGoblin("The quick brown fox jumps over the lazy dog.")
    wg.build_sampling_cache()

    sequence = []
    word_list = "The quick brown".split(" ")
    sequence.extend(word_list)

    # 2. Increased length limit slightly so we can see it finish naturally
    while word_list[-1][-1] not in (".", "!", "?") and len(sequence) < 15:
        word = n_word_search(wg, word_list)

        if not word:
            # 3. If we can't find the sequence, drop the oldest word to try a shorter context
            if len(word_list) > 1:
                word_list = word_list[1:]
            else:
                print("\n[Dead end reached, stopping generation]")
                break
            continue # Skip to next iteration to try the shorter context

        # 4. If we found a match, proceed normally
        weights = [w[2] for w in word]
        candidate = random.choices(word, weights=weights, k=1)[0][0]
        word_list.append(candidate)
        sequence.append(candidate)

    print(" ".join(sequence))
def big_nwx_test(wg, phrase, length=20):
    word_list = phrase.split(" ")
    n_length = len(word_list)
    window_size = min(8, n_length)


    #wg.build_sampling_cache()

    sequence = []
    sequence.extend(word_list)

    #print(word_list)

    desired_window_size = 8
    if n_length< window_size: window_size = n_length
    while (len(sequence) < length
        or sequence[-1][-1] not in (".", "!", "?")):
        context = word_list[-window_size:]
        word = n_word_search(wg, context)

        if not word:
            if window_size == 2:
                last_word = word_list[-1]
                word = n_word_search(wg, last_word.strip(".?!"))
                if not word:
                    word = (
                        "A" if last_word[-1] in (".","!","?")
                        else wg.get_random_word()
                    )

                    word = [(word, 0, 1)]
                break
            window_size = max(2, window_size - 1)
            continue

        word =n_word_search(wg, context)

        weights = [w[2] for w in word]
        if len(word_list) > window_size:
            word_list = word_list[1:]

        if word and word[0]:
            candidate = random.choices(word, weights=weights, k=1)[0][0]
            # Go with the biggest weight?
            choice = sorted(word, key=lambda x: x[2], reverse=True)[0]
            word_list.append(candidate)
            #word_list.append(choice[0])
            #print(word_list)
            sequence.append(candidate)
        #print(len(sequence))
        #print(word_list)
        if window_size < desired_window_size:
            window_size+=1
        if len(word_list) == 0:
            break
    print(" ".join(sequence))


if __name__ == "__main__":

    tiny_nwx_test()
    # test_n_word_search(WordGoblin(""))
    #phrase = "You know that feeling when"
    phrase ="Welp,"
    wg = WordGoblin("")
    start = timer()

    #wg.load("prose_hifi/alien-log.pickle")
    #wg.load("prose_hifi/Light Novel.pickle")
    wg.load("combined_prose_2.pickle")

    #wg.load("prose_hifi/Uncommon Talents Wanted.pickle")
    stop = timer()
    print(f"Loading Time taken: {stop - start}")

    start = timer()
    wg.build_sampling_cache()
    stop = timer()
    print(f"Sampling Cache Time taken: {stop - start}")

    start = timer()

    for i in range(20):
        big_nwx_test(wg, phrase, 20)

    stop = timer()
    print(f"Time taken: {stop - start}")
