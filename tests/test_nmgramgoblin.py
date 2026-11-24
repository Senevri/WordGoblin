import sys
from pprint import pprint
from pathlib import Path
import time
from array import array
SCRIPT_ROOT = Path(__file__).resolve().parent.parent
from timeit import default_timer as timer
import random

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
        sibs = g.get_token_siblings(k, SPECIAL_TOKENS.t_type.whitespace)
    stop = timer()

    print([
        (td.get(k[0]).decode("utf-8"), [td.get(w).decode("utf-8") for w in v])
           for k,v in g.cache["siblings"].items()])
    print(f"Time: {stop-start}")

    print ("Run 2 start")
    start = timer()
    for _, k in g.token_dict.items():
        if k in SPECIAL_TOKENS.indentation:
            continue
        sibs = g.get_token_siblings(k, filter=SPECIAL_TOKENS.t_type.whitespace)
    stop = timer()

    print([
        (td.get(k[0]).decode("utf-8"), [td.get(w).decode("utf-8") for w in v])
           for k,v in g.cache["siblings"].items()])
    #pprint(g.cache)
    print(f"Time: {stop-start}")



def test_walk(g, seek_range=2, capture=2, max_len=0, max_gens=10, rands=True):
    """
    Optimized version of test_walk:
    - Pre-computes filter set once (O(1) lookups instead of O(n) list searches)
    - Avoids repeated td.add() calls that pollute token dictionary
    - Uses list comprehension with local variables for speed
    - Batches string conversion for output
    """
    print(g.reconstruct_corpus()[:400])
    print(g.token_dict)
    print("Run 1 start")
    start = timer()

    td = g.token_dict
    words = g.words  # Local reference for speed (array("I"))
    word_len = len(words)

    if max_len == 0:
        max_len = word_len
    # Simplified: word_len = min(word_len, max_len)
    effective_len = min(word_len, max_len)

    # Pre-compute filter set ONCE - use lookup instead of add to avoid polluting token_dict
    whitespace_tokens = SPECIAL_TOKENS.get_type(SPECIAL_TOKENS.t_type.whitespace)
    filter_set = set()
    for x in whitespace_tokens:
        token_id = td.lookup(x.encode("utf-8"))
        if token_id is not None:
            filter_set.add(token_id)

    # Build queries - use local variables, avoid repeated function calls
    kq = []
    append_kq = kq.append
    get_string = td.get_string_from_list

    # Convert words to list for faster slicing (array slicing creates new arrays)
    words_list = list(words)

    for i in range(effective_len - seek_range):
        # Build seeking tuple with filter check
        seeking = tuple(w for w in words_list[i:i+seek_range] if w not in filter_set)
        if seeking:
            # Only convert to string if we'll actually use it
            key = get_string(list(seeking), sep=b" ")
            append_kq((key, seeking))

    if rands and kq:
        kq = random.choices(kq, k=min(max_gens, len(kq)))
    elif not rands and max_gens < len(kq):
        kq = kq[:max_gens]

    matchlist = []
    append_match = matchlist.append

    # Process queries - pass words as array to n_token_walk
    for key, seeking in kq:
        # Convert seeking to array once
        seeking_arr = array("I", seeking)
        matches = n_token_walk(words, seeking_arr, filter_set, 20, capture)
        if matches and len(matches) > 1:
            append_match((key, matches))

    # Batch output formatting
    out_lines = []
    for key, matches in matchlist:
        # Convert all matches to strings efficiently
        # matches is a list of token IDs (integers), use td.get_string for each
        values = "|".join(td.get_string(m) for m in matches)
        out_lines.append(f"#{key}: {values}")

    print("\n".join(out_lines))
    stop = timer()
    print(f"Done, {stop-start:.4f}s")


if __name__ == "__main__":
    from goblinlib import n_token_walk
    def wrap(text):
        g = NMGramGoblin(text, max_token_len=10)
        if text:
            g.tokenize()
        return g


    #basic_test()
    #test_siblings()
    #test_walk(TEST_SIBLINGS)
    #test_walk(Path('uncleftish_beholding.md').read_text(),4)
    import cProfile, pstats
    with cProfile.Profile() as p:
        test_walk(wrap(Path('gamelogs/Manic Pixie YA Teen Detective.md').read_text()), 5, 4, 0, 20)
        test_walk(wrap(Path('gamelogs/test run prose only.md').read_text()), 5, 5, 0, 20)
        g = NMGramGoblin("", max_token_len=10)
        g.load(Path("pickles/combined_all.2.bin.pickle"))
        test_walk(g, 5, 7, 0, 10, rands=True)
    pstats.Stats(p).sort_stats('cumulative').print_stats(20)