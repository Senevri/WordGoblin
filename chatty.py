import shlex
import sys
from pathlib import Path
import logging
from typing import List, Tuple
Candidate = Tuple[str, int, int]
import random
from timeit import default_timer as timer

SCRIPT_ROOT = Path(__file__).resolve().parent.parent

if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wordgoblins import WordGoblin
#from tweengoblin import TweenGoblin

MAX_DEPTH = 20

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

min_window = 1

def _n_word_search(wg, word_list: List[str]) -> List[Candidate]:
    """Predict the word(s) that follow ``word_list`` verbatim.

    The first word anchors the check: ``word_list[i]`` must appear at
    distance ``i - 1`` from ``word_list[0]`` (distance 0 == immediately
    follows). If the whole window matches, the candidates are the words at
    distance 0 from the last word of the window. Returns ``[]`` when the
    sequence is not present in the training text.
    """
    #test
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

def n_word_search(wg, word_list):
    if not word_list:
        return []
    # chain check: each adjacent pair must be a real transition
    for i in range(len(word_list) - 1):
        anchor, target = word_list[i], word_list[i + 1]
        wd = wg.word_distances.get(anchor)
        if not wd or (target, 0) not in wd:
            return []
    last_word = word_list[-1]
    return wg.get_nearby_words(last_word, 0)

def strip_multi(string ,characters):
    for char in characters:
        string = string.replace(char, "")
    return string

def get_word(wg, word_list, window_size, found_word):

    while window_size >= min_window:
        context = word_list[-window_size:]
        word = n_word_search(wg, context)
        if word:
            return word
        window_size -= 1
    # context = word_list[-window_size:]
    # word = n_word_search(wg, context)

    # last-resort fallback at window 1
    last_word = strip_multi(word_list[-1],",.?!")
    word = n_word_search(wg, [last_word])
    print(last_word)
    if word:
        return word

    if last_word[-1] in ",.!?":
        word = [("A", 0, 1)]
    else:
        word = [(random.choice(wg.unique_words), 0, 1)]
    return word  # Return the fallback word

def get_candidate(word, word_list, window_size):
    weights = [w[2] for w in word]

    if word and word[0]:
        candidate = random.choices(word, weights=weights, k=1)[0][0]

        return candidate, word_list
    return None, word_list


def big_nwx_test(wg, phrase, length=20, max_tail=20):
    word_list = phrase.split(" ")
    n_length = len(word_list)
    window_size = min(MAX_DEPTH, n_length)
    if n_length > window_size:
        word_list = word_list[-window_size:]
    sequence = list(word_list)

    while len(sequence) < length:
        word = get_word(wg, word_list, window_size, False)
        if not word:
            window_size = max(min_window, window_size - 1)
            continue
        candidate, word_list = get_candidate(word, word_list, window_size)
        if candidate is None:
            break
        word_list.append(candidate)
        sequence.append(candidate)
        if len(word_list) > window_size:
            word_list = word_list[1:]
        if window_size < MAX_DEPTH:
            window_size += 1

    # punctuation tail
    tail = 0
    while (tail < max_tail
           and sequence
           and sequence[-1]
           and sequence[-1][-1] not in ".!?"):
        word = get_word(wg, word_list, window_size, False)
        if not word:
            window_size = max(min_window, window_size - 1)
            if window_size == min_window:
                sequence[-1] = sequence[-1].rstrip(",;:") + "."
                break
            continue
        candidate, word_list = get_candidate(word, word_list, window_size)
        if candidate is None:
            sequence[-1] = sequence[-1].rstrip(",;:") + "."
            break
        word_list.append(candidate)
        if len(word_list) > window_size:
            word_list = word_list[1:]
        sequence.append(candidate)
        tail += 1

    if sequence and sequence[-1] and sequence[-1][-1] not in ".!?":
        sequence[-1] = sequence[-1].rstrip(",;:") + "."

    return sequence


def main():
    import argparse
    start = timer()
    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("data_file", help="The text/pickle file or path to read")

    args = parser.parse_args()
    # Load text file

    wordgoblin = WordGoblin("")
    wordgoblin.load(args.data_file or "combined_prose_3.pickle")
    wordgoblin.build_sampling_cache()
# tweengoblin = TweenGoblin(wordgoblin.word_distances)
    stop = timer()
    print(f"Loading Time taken: {stop - start}")

    num_words:int = 140

    buffer = []
    while True:
        new_input = input("> ")
        if new_input.startswith("/"):
            cmd, *params = shlex.split(new_input)
            if cmd == "/exit":
                exit(0)
            if cmd == "/n_words":
                num_words = int(params[0])
                print(f"Number of words set to {num_words}")
                continue
        in_str = (" ".join(buffer) + " " + new_input)
        out = big_nwx_test(wordgoblin, in_str, length=num_words)
        # tweengoblin magic
#        print (" --- Original ---", end="");print("-"*65)
#        print(" ".join(out)) # print(out)
#        print (" --- Revised  ---", end="");print("-"*65)
#        new_sentence = []
#        no_insert = True
#        inclusion_block=0
#        for idx, word in enumerate(out):
#            new_sentence.append(word)
#            if idx >= len(out) - 1: break
#            found = tweengoblin.tween_search(word, out[idx+1])
#            foundstr = f"c={len(found)} w={found[0][1]}: {found[0][0]}" if found else ""
#            # print(f"{word} [ {foundstr} ] {out[idx+1]}: ")
#            if found and no_insert:
#                new_sentence.append(f"{found[0][0]}[{found[0][1]}]")
#                no_insert = False
#            else:
#                if found:
#                    inclusion_block += 1
#                no_insert = True
#        out = new_sentence
        # tweengoblin magic end

        buffer = out
        print(" ".join(buffer))
        print (f" --- blocked insert: {inclusion_block}  ---", end="");print("-"*55)
        inclusion_block = 0






if __name__ == '__main__':
    main()
