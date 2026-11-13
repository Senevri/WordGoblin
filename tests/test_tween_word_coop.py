from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wordgoblins import WordGoblin
from tweengoblin import TweenGoblin


def sanitycheck():
    test = "Tomorrow sees undone what happens not today; indecision brings delays, days lost lamenting lost days."
    wg = WordGoblin(test)
    tg = TweenGoblin(wg.word_distances)
    wg.build_sampling_cache()
    print(tg.tween_search("Tomorrow", "days"))

    sentence = wg.generate_random_sentence("Tomorrow")  # Have wg generate a phrase.
    # tg.get_words(sentence) # leave this off first
    print(sentence)
    words = sentence.split(" ")
    for idx, word in enumerate(words):
        if idx >= len(words) - 2: break
        found = tg.tween_search(word, words[idx+2])[0][0]
        print(f"{word} [ {found} ] {words[idx+2]}: ")

    tg.get_words(sentence)
    for idx, word in enumerate(words):
        if idx >= len(words) - 2: break
        found = tg.tween_search(word, words[idx+2])[0][0]
        print(f"{word} [ {found} ] {words[idx+2]}: ")

def harder_test():
    wg = WordGoblin("")
    #wg.load(Path(SCRIPT_DIR / "prose_hifi/Uncommon Talents Wanted.pickle").resolve())
    wg.load(Path(SCRIPT_DIR / "prose_hifi/Prose Only Log.pickle").resolve())
    tg = TweenGoblin(wg.word_distances)
    wg.build_sampling_cache()
    sentence = wg.generate_random_sentence("Tomorrow")  # Have wg generate a phrase.
    # tg.get_words(sentence) # leave this off first
    print("-"*80)
    print(sentence)
    words = sentence.split(" ")
    new_sentence = []
    for idx, word in enumerate(words):
        if idx >= len(words) - 2: break
        found = tg.tween_search(word, words[idx+2])
        foundstr = f"c={len(found)} w={found[0][1]}: {found[0][0]}" if found else ""
        print(f"{word} [ {foundstr} ] {words[idx+2]}: ")
        if found:
            new_sentence.append(word)
            new_sentence.append(found[0][0])
    new_sentence.append(words[-1])
    print(" ".join(new_sentence))

    print ("-"*80)
    print(sentence)
    # Words to add to sentence:
    new_sentence = []
    for idx, word in enumerate(words):
        new_sentence.append(word)
        if idx >= len(words) - 1: break
        found = tg.tween_search(word, words[idx+1])
        foundstr = f"c={len(found)} w={found[0][1]}: {found[0][0]}" if found else ""
        print(f"{word} [ {foundstr} ] {words[idx+1]}: ")
        if found:
            new_sentence.append(found[0][0])

    print ("-"*80)
    print(" ".join(new_sentence))


def main():
    sanitycheck()
    harder_test()

if __name__ == "__main__":
    # NOTE: Probably should
    #unittest.main()

    main()