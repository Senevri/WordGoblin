import sys
from pathlib import Path
from lettergoblins import LetterGoblin

def test1():
    lg = LetterGoblin("")
    lg.load("../texts/prideandprejudice.letterpickle")
    lg.generate_sampling_cache()
    out = "the "
    for i in range(10):
        out = lg.get_random_word(out)
        print(out)


if __name__=="__main__":
    test1()
