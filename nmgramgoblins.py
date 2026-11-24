import sys

from wordgoblins import WordGoblin
from goblinlib import SPECIAL_TOKENS, TokenDictionary, tokenpair_to_binary, token_to_binary, binary_to_token
from mojibake_cleanup import clean_mojibake
import pickle
from pathlib import Path
import random
from time import time
from timeit import default_timer as timer
from collections import Counter
from array import array # Benchmark current ver first!
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ALL_SPECIAL_TOKENS = SPECIAL_TOKENS.all()

class NMGramGoblin(WordGoblin):

    def __init__(self, text_str, n_len=2, m_len = 2, max_token_len=2):
        super().__init__("")
        text_str = clean_mojibake(text_str)

        #logger.debug("! %s", text_str)
        self.corpus = str(text_str) # ensure copy
        self.n_len = n_len
        self.m_len = m_len
        # self.words = []
        self.words = array("I") # AGAIN first benchmark.
        self.max_token_len=int(max_token_len)

        self.token_dict = TokenDictionary()
        for token in SPECIAL_TOKENS.all():
            self.token_dict.add(token.encode("utf-8"))
        self.token_map = {} #key:bytearray
        self.cache={
            "siblings":{},
            "cache_hits": {}
        }
        #self.tokenize()

    def get_counts(self, recount=False):
        if "wordcounts" in self.cache and not recount:
            return self.cache["wordcounts"]
        c = Counter(self.words)
        self.cache["wordcounts"] = c
        return c

    def invalidate_cache(self):
        self.cache = {
            "siblings": {}
        }

    def set_text(self, text_str):
        self.corpus = clean_mojibake(text_str)

    def _cache_path(self, path) -> Path:
        p = Path(path)
        return p.with_name(p.name.removesuffix(".pickle") + ".cache.pickle")


    def save(self, path, cache=False):
        data = self.get_model_data()
        with Path(path).open("wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

        if cache:
            _cache = self.cache.copy()
            for key in ("strings", "id_tlen", "transition", "transition_key", "cache_hits"):
                _cache.pop(key, None)

            sibs = _cache.pop("siblings", {})
            _cache["siblings"] = {
                    (k[0], int(k[1])): v.tobytes()
                    for k, v in sibs.items()
                    }

            with self._cache_path(path).open("wb") as f:
                pickle.dump(_cache, f, protocol=pickle.HIGHEST_PROTOCOL)


    def load(self, path, cache=False):
        with Path(path).open("rb") as f:
            self.load_model_data(pickle.load(f))

        if cache:
            cache_path = self._cache_path(path)
            if cache_path.exists():
                with cache_path.open("rb") as f:
                    self.cache = pickle.load(f)
                self.cache["siblings"] = {
                    (k[0], SPECIAL_TOKENS.t_type((k[1]))): array("I", v) for k, v in self.cache.pop("siblings", {}).items()
                }
                self.cache.setdefault("cache_hits", {})



    def _get_token(self, c_str:str):
        cache = self.cache.setdefault("id_tlen", {})

        base_t_len = self.max_token_len
        t_len = base_t_len
        token = SPECIAL_TOKENS.check_string(c_str)
            #return (int.from_bytes(cache[token][:3], "little"), cache[token][3])
        if token in cache:
            return cache[token]

        if token:
            if token in ALL_SPECIAL_TOKENS:
                t_len = len(token)
            else:
                t_len = min(base_t_len, len(token))
                token = token[:t_len]
        #if not token:
        else:
            token = c_str[:t_len]
            t_len = len(token)
            #print(t_len, base_t_len)
            assert t_len <= base_t_len
        _id = self.token_dict.add(token.encode("utf-8"))
        # cache[token] = b"".join((int.to_bytes(_id, 3, "little"), int.to_bytes(t_len, 1, "little")))
        cache[token] = (_id, t_len)
        return (_id, t_len)



    def _filtered_words(self, filter=SPECIAL_TOKENS.indentation) -> list:
        if "filtered_words" not in self.cache:
            td = self.token_dict
            ws = set(filter)
            self.cache["filtered_words"] = [
                w for w in self.words if self.to_str(w) not in ws
            ]
        return self.cache["filtered_words"]


    def _build_transition_table(self, filter=0):
        words = self._filtered_words(SPECIAL_TOKENS.get_type(filter)) if filter > 0 else self.words
        successors = {}      # token_id -> set of tokens that follow it
        precedents = {}      # token_id -> set of tokens that precede it
        prev = None
        for w in words:
            if prev is not None:
                successors.setdefault(prev, set()).add(w)
                precedents.setdefault(w, set()).add(prev)
            prev = w
        self.cache["transition"] = (successors, precedents)

    def get_token_siblings(self, token_id, filter=0, get_bytes=False):
        cache = self.cache.setdefault("siblings", {})
        self.cache["cache_hits"].setdefault("siblings", 0)

        td = self.token_dict

        cache_key = (token_id, filter)
        if cache_key in cache:
            self.cache["cache_hits"]["siblings"] = self.cache["cache_hits"].get("siblings", 0) + 1
            sibs = cache[cache_key]
            return [td.get(cw) for cw in sibs] if get_bytes else sibs

        key = ("filtered" if filter else "raw")

        # if "transition" not in self.cache or self.cache.get("transition_key") != key:
        #     self._build_transition_table(ignore_whitespace)
        #     self.cache["transition_key"] = key
        if self.cache.get("transition_key") != key:
            self._build_transition_table(filter)
            self.cache["transition_key"] = key

        successors, precedents = self.cache["transition"]

        # for p in precedents.get(token_id, ()):
        #     sibs |= successors.get(p, ())
        preds = precedents.get(token_id)
        if preds:

            sibs = set().union(*(successors.get(p, ()) for p in preds))
            sibs.discard(token_id)
        else:
            sibs = ()

        cache[cache_key] = array("I", sibs)
        return [self.token_dict.get(s) for s in sibs] if get_bytes else sibs

        # precedents = [
        #     words[i-1]
        #     for i, w in enumerate(words)
        #     if w == token_id and i > 0
        # ]

        # precedents = set(precedents)

        # siblings = set([words[i+1]
        #     for i, t_id in enumerate(words) if t_id in precedents and i<len(words)-1
        # ])

        # cache[token_id] = siblings
        # return [td.get(s) for s in siblings] if get_bytes else siblings

    def _nxt_bytes(self, nxt_id):
        cache = self.cache.setdefault("nxt_bytes", {})
        b = cache.get(nxt_id)
        if b is None:
            b = token_to_binary((0, nxt_id, 1), self.token_dict)
            cache[nxt_id] = b
        return b


    def tokenize(self, show_time=True):
        corpus = str(self.corpus)
        max_lookahead = 16 # Feels low :D
        max_len = len(corpus)
        print(f"Tokenizing {max_len} characters")

        # Bootstrap: look up the very first token
        cur_id, cur_len = self._get_token(corpus[0:max_lookahead])
        pos = 0
        ctr = 0

        while pos < len(corpus):
            # cur_id is the token at position `pos`
            self.words.append(cur_id)
            pos += cur_len
            if pos >= len(corpus):
                break
            if cur_len == 0:
                break

            # Look up the next token (it sits at the new `pos`)
            nxt_id, nxt_len = self._get_token(corpus[pos:pos+max_lookahead])

            # Emit the pair (cur_id → nxt_id) into token_map
            buf = self.token_map.setdefault(cur_id, bytearray())
            buf += self._nxt_bytes(nxt_id)

            # Slide: the next token becomes current for the next iteration
            cur_id, cur_len = nxt_id, nxt_len

            ctr += 1
            if ctr == 2000:
                ctr = 0
                print(f"{str(100-(100*(max_len-pos)/max_len))[:5]} %", end="\r")

        # ... your existing dedup pass ...

        for t_id, buf in self.token_map.items():
            counts = {}
            for i in range(0, len(buf), 7):
                tgt = bytes(buf[i+1:i+4])           # bytes is hashable; bytearray is not
                counts[tgt] = counts.get(tgt, 0) + 1
            new_buf = bytearray()
            for tgt, w in sorted(counts.items(), key=lambda item: item[1], reverse=True):
                new_buf += b'\x00' + tgt + w.to_bytes(3, "little")
            self.token_map[t_id] = new_buf

    def decode_token_list(self, token_list):
        #print(token_list)
        len_b = len(token_list)
        return [binary_to_token(token_list[i:i+7], self.token_dict) for i in range(0, len_b, 7)]

    def encode_token_list(self, token_list):
        buf = bytearray()
        for t in token_list:
            buf += token_to_binary(t, self.token_dict)
        return buf

    def to_word_distances(self):
        # compatibility layer
        buffer = {}
        for k, v in self.token_map.items():
            tokens = self.decode_token_list(v)
            key = self.token_dict.id_to_token[k]
            #print(key)
            buffer.update(
                {key.decode("utf-8"): {
                    (t[1].decode("utf-8"), t[0]): t[2]
                    }
                    for t in tokens
                })
        return buffer

    def get_model_data(self):
        return {
            "corpus": self.corpus,
            "words": self.words,
            "n_len": self.n_len,
            "m_len": self.m_len,
            "token_dict": self.token_dict,
            "token_map": self.token_map,
        }

    def load_model_data(self, data):
        # data = (token_map, token_dict)
        self.words = data["words"]
        self.corpus = data["corpus"]
        self.n_len = data["n_len"]
        self.m_len = data["m_len"]
        self.token_dict = data["token_dict"]
        self.token_map = data["token_map"]

    def combine_with(self, other, multiplier=1.0):
        """Merge other's transitions and token stream into self."""
        # 1. Build id mapping: other_id -> unified id in self.token_dict
        id_map = {
            other_id: self.token_dict.add(token_bytes)
            for token_bytes, other_id in other.token_dict.items()
        }

        # 2. Remap other's flat word ID array before appending
        self.words.extend(id_map[wid] for wid in other.words)
        self.corpus += other.corpus

        # 3. Remap and merge token_map transitions (your existing logic is already right)
        for other_cur_id, other_buf in other.token_map.items():
            cur_id = id_map[other_cur_id]
            buf = self.token_map.setdefault(cur_id, bytearray())

            existing = {}
            for i in range(0, len(buf), 7):
                key = (buf[i], bytes(buf[i+1:i+4]))
                existing[key] = (i, int.from_bytes(buf[i+4:i+7], "little"))

            for i in range(0, len(other_buf), 7):
                dist = other_buf[i]
                target = int.from_bytes(other_buf[i+1:i+4], "little")
                weight = int.from_bytes(other_buf[i+4:i+7], "little")

                new_target_b = id_map[target].to_bytes(3, "little")
                scaled_weight = round(weight * multiplier)

                key = (dist, new_target_b)
                if key in existing:
                    offset, old_w = existing[key]
                    total = old_w + scaled_weight
                    buf[offset+4:offset+7] = total.to_bytes(3, "little")
                    existing[key] = (offset, total)
                else:
                    buf += bytes([dist]) + new_target_b + scaled_weight.to_bytes(3, "little")
                    existing[key] = (len(buf) - 7, scaled_weight)

    def reconstruct_corpus(self):
        td = self.token_dict
        return "".join([td.get(t).decode("utf-8") for t in self.words])


    # Modified for different algo
    def get_next_word(self, word):
        distances = {k:v for k,v in self.word_distances.items() if k.strip()}
        words = [w for w in self.words]
        if isinstance(word, int):
            word = self.to_str(word)
        if word not in distances:
            distances[word] = {}
            return random.choice(words)
        distances = distances[word]
        candidates = [
            other_word
            for (other_word, distance), weight in distances.items()
            if distance == 1
        ]
        if not candidates:
            return random.choice(words)
        return random.choice(candidates)

    def to_str(self, token):
        cache = self.cache.setdefault("strings", {})
        if token in cache:
            return cache[token]
        b = self.token_dict.get(token) if isinstance(token, int) else token
        s = b.decode("utf-8")
        cache[token] = s
        return s

if __name__=="__main__":
    # a simple test
    import argparse
    parser = argparse.ArgumentParser("NMGramGoblin")
    parser.add_argument("--source")
    parser.add_argument("--pickle")
    parser.add_argument("--max_wordsize", type=int, default=5)
    parser.add_argument("--out")
    parser.add_argument("--siblings", action="store_true")
    parser.add_argument("--cache", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--tokenize", action="store_true")

    args = parser.parse_args()

    base_path = str(args.out).removesuffix(".md").removesuffix(".txt")
    start = timer()
    if args.source:

        text = Path(args.source).read_text()
        out_path = args.out or args.source
        base_path = str(args.out).removesuffix(".md").removesuffix(".txt")

        g = NMGramGoblin(text, max_token_len=args.max_wordsize)

        if args.profile:
            import cProfile, pstats
            with cProfile.Profile() as p:
                print("PROFILE:", sys.getprofile())
                print("TRACE:", sys.gettrace())
                g.tokenize()
            pstats.Stats(p).sort_stats('cumulative').print_stats(20)
            exit(0)
        g.tokenize()
        g.save(Path(base_path + ".bin.pickle"))

    if args.pickle:
        g=NMGramGoblin("", max_token_len=args.max_wordsize)
        g.tokenize()
        g.load(Path(args.pickle), cache=args.cache)
    stop = timer()
    print(f"Time init: {stop-start}")

    if args.tokenize:
        start = timer()
        g.tokenize()
        stop = timer()
        print(f"Time tokenizing: {stop-start}")


    start = timer()
    #print(g.token_map)
    print(g.reconstruct_corpus()[-500:])
    def test():
        wg = WordGoblin("")
        wg.words = [g.token_dict.get(w).decode("utf-8") for w in g.words]
        wg.word_distances = g.to_word_distances()
        wg.build_sampling_cache()
        print(wg.generate_random_sentence("The", 100), sep=":")
    #test()
    # g.build_sampling_cache()
    # g.generate_random_sentence("The", sep=":")
    stop = timer()
    print(f"orig length: {len(g.corpus)}, token length: {len(g.words)}")
    print(f"Time gen: {stop-start}")
    print(f"Num Tokens: {len(g.token_map)}")
    weights = [
        entry[2]
        for buf in g.token_map.values()
        for entry in g.decode_token_list(buf)
    ]
    print(f"Largest weight: {max(weights)}")

    print(args.siblings)
    s_stop = 0.0
    s_start = 0.0
    run1 = 0.0
    run2 = 0.0
    start1 = 0.0
    stop1 = 0.0
    stop2 = 0.0
    p_stop = 0.0
    processed=0
    first_run_cache_hits = 0
    td = g.token_dict

    hub_words = [w for w in "The,the,a,A,An,".split(",") if td.find_by_str(w)]
    print (hub_words)
    exit()

    if args.siblings:
        start = timer()
        start1 = float(start)

        g._filtered_words(SPECIAL_TOKENS.all() + hub_words)


        try:
            for _, word in g.token_dict.items():
                sibs = g.get_token_siblings(word, filter=SPECIAL_TOKENS.t_type.all)
                processed += 1
                if processed % 100 == 0: print(f"{processed}", end="\r")
            stop=timer()
            run1 = stop-start
            print(f"run1 sibs took: {run1}")
            start = timer()
            processed=0
            first_run_cache_hits = g.cache["cache_hits"]["siblings"]
            for _, word in g.token_dict.items():
                sibs = g.get_token_siblings(word, filter=SPECIAL_TOKENS.t_type.all)
                processed += 1
                if processed % 100 == 0: print(f"{processed}", end="\r")
            stop2 = timer()
            run2 = stop2-start
            print(f"run2 sibs took: {run2}, a difference of {run1/run2}")
        except KeyboardInterrupt:
            print("User interrupt!")
            stop=timer()
        print(f"Time taken: {stop2 - start1}, processed {processed}")
        p_start = timer()


        #print(weights.keys())
        for word, sibs in g.cache.get("siblings", {}).items():
            recs = g.token_map.get(word[0], b"")
            w = {
                entry[1]: entry[2]                                   # target_bytes → weight
                for entry in g.decode_token_list(recs)
            }
            sibs = sorted(sibs, key=lambda x: w.get(td.get(x), -1), reverse=True)
            print(f"|{g.to_str(word[0])}[{len(sibs)}]:"
                f"{[g.to_str(s) for s in sibs[:14] if s]}")
        print(f"Time gen: {stop-start}")
        print(f"Saving took {s_stop-s_start} s")
        print(f"Printing took {p_stop-p_start} s")
        print(f"Run 1: sibs took: {run1} s")
        print(f"run 2: sibs took: {run2} s, a difference of {run2-run1}")
        print(f"Time taken: {stop2-start1}, processed {processed}")
        print(f"Cache hits: run 1: {first_run_cache_hits} run 2:{g.cache["cache_hits"]}")


    weights = {
        entry[1]:entry[2]
        for buf in g.token_map.values()
        for entry in g.decode_token_list(buf)
    }

    if args.out:
        s_start = timer()
        g.save(base_path + ".2.bin.pickle", cache=True)
        s_stop = timer()
        print(f"Time saving: {stop-start}")


    print(f"orig length: {len(g.corpus)}, token length: {len(g.words)}")

    print(f"Num Tokens: {len(g.token_map)}")
    print(f"Largest weight: {max(weights)}")
    print("Words:", sys.getsizeof(g.words))
    print("Token map:", sys.getsizeof(g.token_map))
    print("Token buffers:", sum(sys.getsizeof(v) for v in g.token_map.values()))
    print("Token dictionary:", sys.getsizeof(g.token_dict))
    print(f"ids len: {len(g.token_dict.id_to_token)}")
    print(f"tokens len: {len(g.token_dict.token_to_id.keys())}")
    print(f"Cache: {g.cache.keys()} - {[{len(v) for v in g.cache.values()}]}")
    print(f"Filtered: {[w for w in set(g.words) if w not in g.cache.get("filtered_words")]}")
