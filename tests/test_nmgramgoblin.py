import sys
from pprint import pprint
from pathlib import Path
import time
SCRIPT_ROOT = Path(__file__).resolve().parent.parent
from timeit import default_timer as timer

if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from goblinlib import binary_to_token, SPECIAL_TOKENS
from nmgramgoblins import NMGramGoblin

def basic_test():
    g = NMGramGoblin("the quick brown fox jumps over the lazy dog\n" #, max_token_len=3)
                    "tabs:\tand  spaces    are        special", max_token_len=4)
        #g=NMGramGoblin("aabb")
    g.n_len=2
    g.tokenize()

    td = g.token_dict
    from pprint import pprint
    pprint(g.token_dict)
    [pprint({t:td.get(t)}) for t in g.token_map.keys()]
    for k, t in g.token_map.items():
        print(td.get(k).decode("utf-8"), end=":")
        for i in range(0, len(t), 7):
            #print(f"{i}-{i+7}")
            tk = binary_to_token(t[i:i+7], td)
            #print("   token:", tk)
            tk_id = tk[1]
            #rint("token_value:", tk_id)

            #print(f"{td.get(k)}: {tk}")
            print(tk[1].decode("utf-8"), end="|")

    print("\n\n# Same in ids:\n")
    for k, t in g.token_map.items():
        print(k, end=":")
        for i in range(0, len(t), 7):
            tk = binary_to_token(t[i:i+7], td)
            print(td.lookup(tk[1]), end="|")
    print("\n--- endl ---")
    print (g.words)
    print("\n--- Words ---")
    for word_id in g.words:
        print(td.get(word_id).decode("utf-8"), end="|")
    #g.words = g.word_distances.keys()
    #print(g.words)
    # Convert to wordgoblin format
    g.words=[td.get(word_id).decode("utf-8") for word_id in g.words]
    pprint (g.word_distances)
    g.word_distances = g.to_word_distances()
    g.build_sampling_cache()
    print(len(g.words))
    print(g.generate_random_sentence("The"), sep=":")
    print(f"orig length: {len(g.corpus)}, token length: {len(g.words)}")


TEST_SIBLINGS = """
she sells seashells on the seashore
she has a really nice car
she drives a red car and her favourite food is pizza
he drives a rusted car and his favourite animal is a cat
"""

def test_siblings():
    from pprint import pprint
    g = NMGramGoblin(TEST_SIBLINGS, max_token_len=10)
    g.tokenize()

    print(g.reconstruct_corpus())

    print (g.token_dict)
    print("Run 1 start")
    start = timer()
    td = g.token_dict
    for _, k in g.token_dict.items():
        #bytes, id
        if k in SPECIAL_TOKENS.indentation:
            continue
        sibs = g.get_token_siblings(k, ignore_whitespace=True)
    stop = timer()

    print([
        (td.get(k).decode("utf-8"), [td.get(w).decode("utf-8") for w in v])
           for k,v in g.cache["siblings"].items()])
    print(f"Time: {stop-start}")

    print ("Run 2 start")
    start = timer()
    for _, k in g.token_dict.items():
        if k in SPECIAL_TOKENS.indentation:
            continue
        sibs = g.get_token_siblings(k, ignore_whitespace=True)
    stop = timer()

    print([
        (td.get(k).decode("utf-8"), [td.get(w).decode("utf-8") for w in v])
           for k,v in g.cache["siblings"].items()])
    #pprint(g.cache)
    print(f"Time: {stop-start}")




if __name__ == "__main__":
    basic_test()
    test_siblings()
