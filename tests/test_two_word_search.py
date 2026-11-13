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
    """Predict the word(s) that follow ``word_list`` verbatim.

    The first word anchors the check: ``word_list[i]`` must appear at
    distance ``i - 1`` from ``word_list[0]`` (distance 0 == immediately
    follows). If the whole window matches, the candidates are the words at
    distance 0 from the last word of the window. Returns ``[]`` when the
    sequence is not present in the training text.
    """
    if not word_list:
        return []
    anchor = word_list[0]
    wd = wg.word_distances.get(anchor)
    if not wd:
        return []
    # wd = [(w[0].lower(), *w[1:])
    #          for w in wd]
    # word_list = [w.lower() for w in word_list]
    # # Verify the window against the anchor: word_list[i] at distance i-1.
    # O(n) dict lookups.
    for i, target in enumerate(word_list[1:], start=1):
        if (target, i - 1) not in wd:
            return []

    # The word that follows the whole window is the one immediately after
    # the last word. Anchoring the return on the last word (rather than
    # extrapolating back to the anchor) keeps verbatim phrases intact even
    # when the training text is not perfectly linear.
    last_word = word_list[-1]
    return wg.get_nearby_words(last_word, 0)



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

def test_n_word_search(wg):
    wg.load("prose_hifi/alien-log.pickle")
    wg.build_sampling_cache()
    print (len(wg.unique_words))
    word_list = "You know that feeling when".split(" ")
    #word_list = "You know".split(" ")
    n_length = len(word_list)
    wl = list(word_list)
    print (" ".join(word_list), end=" ")
    for j in range(20):
        sequence = []
        sequence.extend(word_list)
        for i in range(20):

            result = n_word_search(wg, wl)
            print((result, wg, wl))
            if not result:
                result = n_word_search(wg, wl)
            #print(result)

            if result:
                #result = [w for w in result if w[0] not in sequence]

                weights = [w[2] for w in result]
                choices = [w[0] for w in result]
                #print(len(weights), len(choices))
                try:
                    #wl.append(random.choices(choices, weights=weights, k=1)[0]) # (word_tuple[1], result[0])
                    wl.append(random.choice(choices)[0]) # (word_tuple[1], result[0])
                    #word_list = word_list[1:]
                    sequence.append(wl[-1])
                    print(wl)
                    wl = wl[1:]
                except IndexError as e:
                    print((weights, choices, wl, word_list, e))
                    pass

            #print(sequence, word_list)
            # if word_list[-1] is not sequence[-1]:
            #     sequence.append(word_list[-1])
            if word_list[-1][-1] in (".","!","?"):
                break
        print (" ".join(sequence))

def tiny_nwx_test():
    wg = WordGoblin("The quick brown fox jumps over the lazy dog")
    wg.build_sampling_cache()

    sequence = []
    word_list = "The quick brown".split(" ")
    sequence.extend(word_list)
    while (word_list[-1][-1] not in (".","!","?")
        and len(sequence) < 10):
        word =n_word_search(wg, word_list)
        weights = [w[2] for w in word]
        if len(word_list)>8:
            word_list=word_list[1:]
        if word and word[0]:
            word_list.append(random.choices(word, weights=weights, k=1)[0][0])
            sequence.append(word_list[-1])

    print(" ".join(sequence))

def big_nwx_test(wg, length=20):
    #print (len(wg.unique_words))
    #word_list = "She looks".split(" ")

    word_list = "You know that feeling when".split(" ")
    wg.build_sampling_cache()

    sequence = []
    sequence.extend(word_list)
    # Do some precalc:
    # words = [w for w in [wg.get_nearby_words(wlw, 0)
    #          for wlw in word_list]]

    def myrandom(_list, _weights):
        #_len = len(_list)
        out_list = []
        for w in _list:
            out_list.append([w for i in range(_weights[0])])
            weights= _weights[1:]
        choice = random.randint(0, len(_list))
        return out_list[choice]

    #print(word_list)
    window_size = 8
    while (len(sequence) < length or word_list[-1][-1] not in (".","!","?", r"\"")):
        start = timer()
        word =n_word_search(wg, word_list[-window_size:])

        if not word:
            window_size-=1
            word =n_word_search(wg, word_list[-window_size:])
        weights = [w[2] for w in word]
        if len(word_list)>window_size:
            word_list=word_list[1:]
        stop = timer()
        #print(f"Time taken: {stop - start}")

        if word and word[0]:
            # Go with the biggest weight?
            choice = sorted(word, key=lambda x: x[2], reverse=True)[0]
            word_list.append(random.choices(word, weights=weights, k=1)[0][0])
            #word_list.append(choice[0])
            #print(word_list)
            sequence.append(word_list[-1])
        #print(len(sequence))
        #print(word_list)
        if len(word_list)<window_size-3:
            window_size+=1
        if len(word_list) == 1:
            break
    print(" ".join(sequence))

if __name__ == "__main__":

    #tiny_nwx_test()
    # test_n_word_search(WordGoblin(""))
    wg = WordGoblin("")
    wg.load("prose_hifi/alien-log.pickle")
    #wg.load("prose_hifi/Light Novel.pickle")
    #wg.load("combined_prose.pickle")
    wg.build_sampling_cache()
    for i in range(20):
        big_nwx_test(wg, 15)