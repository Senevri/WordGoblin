import sys
import random
import pytest
from pathlib import Path

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

def n_word_search(wg, word_list):
    _word = word_list[0]
    words = wg.get_nearby_words(_word, 0)
    if not words:
        return None
    wd = wg.word_distances[_word]
    word = None
    word_list = word_list[1:]
    #print(wd)
    #print([x for x in wd if x[0] in word_list])
    names = [x for x in wd if x[0] in word_list]
    #print(names)
    idx = 0
    while word_list:
        #print(word_list)
        names = [x for x in wd if x[0] in word_list]
        #print(names)
        if not names:
            return []
            #return wg.get_nearby_words(word, 0)
        word = word_list[0]
        for name in names:
            if name[0] == word and name[1] == idx:
                word_list = word_list[1:]
                idx += 1
                break
    return wg.get_nearby_words(word, 0)


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
    n_length = len(word_list)
    print (" ".join(word_list), end=" ")
    for j in range(20):
        sequence = word_list
        for i in range(20):

            result = n_word_search(wg, word_list[-n_length:])
            if not result:
                result = n_word_search(wg, word_list[-(n_length-1):])
            #print(result)
            if result:
                #result = [w for w in result if w[0] not in sequence]

                weights = [w[2] for w in result]
                choices = [w[0] for w in result]
                #print(len(weights), len(choices))
                try:
                    word_list.append(random.choices(choices, weights=weights, k=1)[0]) # (word_tuple[1], result[0])
                    #word_list.append(random.choice(choices)[0]) # (word_tuple[1], result[0])
                    #word_list = word_list[1:]
                except IndexError as e:
                    print((weights, choices, word_list, e))
                    pass

            #print(sequence, word_list)
            if word_list[-1] is not sequence[-1]:
                sequence.append(word_list[-1])
            if word_list[-1][-1] in (".","!","?"):
                break
        print (" ".join(sequence))

if __name__ == "__main__":

    test_n_word_search(WordGoblin(""))