"""goblinlib - Common utilities shared across goblin modules."""
from __future__ import annotations
import random
from typing import List, Tuple, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from array import array

Candidate = Tuple[str, int]
Candidate3 = Tuple[str, int, int]

class GoblinLike:
    def get_model_data(self):
        """Return whatever tuple/dict this goblin persists."""
        ...
    def load_model_data(self, data):
        """Restore internal state from get_model_data's output."""
        ...
    def combine_with(self, other, multiplier=1.0):
        """Merge other's model into self in-place."""
        ...

NTW_CACHE = {}

def n_token_walk(
    l_tid: array[int],
    req_tokens: array[int],
    filter=None,
    max_tokens=20,
    req_resp=1
) -> list:
    """
    Find all occurrences of req_tokens in l_tid and return the tokens that follow each match.

    Optimized version:
    - Avoids creating filtered copy of l_tid (uses filter set for O(1) lookup)
    - Uses memoryview for zero-copy slicing
    - Collects all matches instead of overwriting
    - Early exit when max_tokens reached
    """
    if filter is None:
        filter_set = set()
    else:
        filter_set = set(filter)

    req_len = len(req_tokens)
    if req_len == 0:
        return []

    # Convert to list for faster indexing (array indexing is slower in Python)
    # Only filter if filter_set is not empty
    if filter_set:
        # Build filtered list once
        filtered = [x for x in l_tid if x not in filter_set]
    else:
        filtered = list(l_tid)

    filtered_len = len(filtered)
    if filtered_len < req_len + req_resp:
        return []

    # Convert req_tokens to tuple for faster comparison
    req_tuple = tuple(req_tokens)
    req_resp = min(req_resp, max_tokens)  # Cap response length

    out = []
    # Use local variables for speed
    filtered_local = filtered
    req_len_local = req_len
    req_resp_local = req_resp
    max_tokens_local = max_tokens

    idx = 0
    # Search for all matches
    while idx <= filtered_len - req_len_local - req_resp_local:
        # Quick check: first token must match
        if filtered_local[idx] == req_tuple[0]:
            # Check full sequence
            match = True
            for j in range(1, req_len_local):
                if filtered_local[idx + j] != req_tuple[j]:
                    match = False
                    break

            if match:
                # Collect response tokens
                end_idx = idx + req_len_local + req_resp_local
                out.extend(filtered_local[idx + req_len_local:end_idx])
                if len(out) >= max_tokens_local:
                    break
                idx = end_idx  # Skip past this match
                continue
        idx += 1

    return out[:max_tokens_local]


def n_token_walk_optimized(
    l_tid: array[int],
    req_tokens: array[int],
    filter=None,
    max_tokens=20,
    req_resp=1
) -> list:
    """
    Even more optimized version using a pre-built index for repeated searches.
    Best when searching the same corpus multiple times with different patterns.
    """
    # This would require a pre-built index (e.g., suffix array or hash-based index)
    # For now, use the improved version above
    return n_token_walk(l_tid, req_tokens, filter, max_tokens, req_resp)

def _n_token_walk(l_tid:array[int], req_tokens:array[int], filter=[], max_tokens=20) -> set [int]:
    # Returns all tokens that match from corpus.
    l_tid = [x for x in l_tid if x not in filter]
    out = []
    req_len = len(req_tokens)
    seek_len = len(l_tid)-req_len-1
    for idx in range(0, seek_len) :
        _range = l_tid[idx:idx+req_len]
        if all(a==b for a, b in zip(_range, req_tokens)):
            #print(len(l_tid), idx, seek_len)
            out.append(l_tid[idx+req_len])
            if len(out)>max_tokens: break
    return set(out)


def n_word_search(word_distances: Dict[str, Any], word_list: List[str]) -> List[Candidate]:
    """Predict the word(s) that follow word_list using chain validation.

    Each adjacent pair in word_list must be a real distance-0 transition.
    If the chain is valid, returns candidates at distance 0 from the last word.
    Returns [] when any pair is invalid or the list is empty.
    """
    if not word_list:
        return []
    anchor = word_list[0]
    wd = word_distances.get(anchor)
    if not wd:
        return []
    for i, target in enumerate(word_list[1:], start=1):
        if (target, i - 1) not in wd:
            return []
    last_word = word_list[-1]
    return [(w, d, wt) for (w, d), wt in word_distances.get(last_word, {}).items() if d == 0]


def get_nearby_words(word_distances: Dict[str, Any], word: str, max_distance: int = 8) -> List[Candidate3]:
    """Get words near word up to max_distance."""
    if word not in word_distances:
        return []
    distances = word_distances[word]
    return [
        (other_word, distance, weight)
        for (other_word, distance), weight in distances.items()
        if distance <= max_distance
    ]


def generate_short_sentence(
    word_distances: Dict[str, Any],
    start: str,
    max_words: int = 8,
    n_words: int = 2,
) -> str:
    """Generate a short sentence starting from start using n-word search."""
    sentence = [start]
    for _ in range(max_words):
        window = sentence[-n_words:]
        candidates = n_word_search(word_distances, window)
        if not candidates:
            break
        next_word = random.choices(
            [c[0] for c in candidates],
            weights=[c[2] for c in candidates],
            k=1,
        )[0]
        sentence.append(next_word)
    return " ".join(sentence)


def generate_n_word_phrase(
    word_distances: Dict[str, Any],
    n: int = 3,
    max_words: int = 8,
) -> str:
    """Generate a random n-word phrase."""
    unique_words = list(word_distances.keys())
    if not unique_words:
        return ""
    start_word = random.choice(unique_words)
    return generate_short_sentence(word_distances, start=start_word, max_words=max_words, n_words=n)


def is_letter_goblin(obj: Any) -> bool:
    """Check if obj is a LetterGoblin instance."""
    return hasattr(obj, "letter_distances")


def get_words(text: str) -> List[str]:
    """Split text into words, normalizing whitespace."""
    whitespace = [" ", "\t", "\n", "\r"]
    for key in whitespace:
        text = text.replace(key, " ")
    return [w for w in text.split(" ") if w]


class TokenDictionary():
    def __init__(self):
        self.token_to_id = {}
        self.id_to_token = []

    def add(self, token: bytes) -> int:
        if token in self.token_to_id:
            return self.token_to_id[token]

        token_id = len(self.id_to_token)

        if token_id >= 2**24:
            raise OverflowError("Token dictionary full")

        self.token_to_id[token] = token_id
        self.id_to_token.append(token)

        return token_id

    def __contains__(self, token: bytes) -> bool:
        return token in self.token_to_id

    def find_by_str(self, str) -> int | None:
        return self.lookup(str.encode("utf-8"))


    def lookup(self, token: bytes) -> int | None:
        return self.token_to_id.get(token)

    def get(self, token_id: int) -> bytes:
        return self.id_to_token[token_id]

    def get_string(self, token_id:int) -> str:
        return self.id_to_token[token_id].decode("utf-8")

    def get_string_from_list(self, tokenlist:list[int], sep=b"") -> str:

        return sep.join(self.id_to_token[t] for t in tokenlist).decode("utf-8")


    def encode(self, token: bytes) -> bytes:
        return self.add(token).to_bytes(3, LITTLE)

    def decode(self, data: bytes) -> bytes:
        token_id = int.from_bytes(data, LITTLE)
        return self.get(token_id)

    def __repr__(self):
        return str(self.token_to_id)

    def __len__(self):
        return len(self.id_to_token)

    def items(self):
        return self.token_to_id.items()

    def keys(self):
        return self.token_to_id.keys()

    def values(self):
        return self.token_to_id.values()


LITTLE = "little"

def big_to_little(bytes:bytes):
    int_ = int.from_bytes(bytes, "big")
    return int_.to_bytes(3, LITTLE)

TTB_CACHE = {}

def token_to_binary(token:Tuple(int, Union[str, int], int), tokendict):
    cache = TTB_CACHE.setdefault("ttb", {})
    if token in cache:
        return cache[token]

    distance, target_t, weight = token

    if isinstance(target_t, str):
        target_t = target_t.encode("utf-8")
    if isinstance(target_t, bytes):
        target_id = tokendict.add(target_t)
    else:
        target_id = target_t


    # swap to byte repr
    if distance > 256 or weight > 256**3:
        raise ValueError(f"Too large values: {distance} > 256 or {weight} > 24b")

    distance_b = int(distance).to_bytes(1)
    weight_b = int(weight).to_bytes(3, LITTLE)
    target_b = int(target_id).to_bytes(3, LITTLE)
    _bytearr = b"".join((distance_b,target_b,weight_b))
    cache[token] = bytearray(_bytearr)
    return _bytearr

def tokenpair_to_binary(tokenpair:Tuple[str, int, str, int], tokendict:TokenDictionary):
    key_t, distance, target_t, weight = tokenpair
    key_t = key_t.encode("utf-8")
    key_id = tokendict.add(key_t).to_bytes(3, LITTLE)

    return key_id + token_to_binary((distance, target_t, weight), tokendict)

def binary_to_token(binary_t: bytes, _dict) -> tuple[int, int, int]:
    if len(binary_t) < 7:
        print(f"Error! {len(binary_t)}, {binary_t}")
        return (0, 0, 0)
    target_b = binary_t[1:4]
    distance_b = binary_t[0]
    weight_b = binary_t[4:]
    endian = LITTLE
    return (
        distance_b,
        _dict.decode(target_b),
        int.from_bytes(weight_b, endian)
    )


def binary_to_tokenpair(binary_t:bytes, _dict):
    key_b = binary_t[:3]
    return (
        _dict.decode(key_b),
        *binary_to_token(binary_t[3:], _dict)
    )

import re

AGENT_WORDS = frozenset([
    "I", "she", "he", "they", "we", "you", "it",
    "that", "this", "my", "your", "their", "our",
])

AUXILIARY_VERBS = frozenset([
    "am", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did",
    "can", "could", "may", "might", "must", "shall",
    "should", "will", "would",
])

POSSESSION_VERBS = frozenset([
    "have", "has", "had",
])

HUB_WORDS = frozenset("The,the,a,A,An,".split(","))

COMMON_SUFFIXES = (
    # Nounforming
    "tion", "sion", "ment", "ness", "ity", "ance", "ence",
    "er", "or", "ist", "ism", "ship", "hood", "age", "cy",

    # Adjectiveforming
    "able", "ible", "al", "ic", "ous", "ful", "less",
    "ive", "ish", "y", "ary", "esque",

    # Adverbforming
    "ly", "ward", "wards", "wise",

    # Verbforming
    "ize", "ise", "ify", "ate", "en",

    # Grammatical / inflectional
    "s", "es", "ed", "ing", "er", "est", "'s",
)


class SPECIAL_TOKENS:
    t_type = IntEnum("tokentype",
        "none indent newline specialchars whitespace all"
    )
    indentation = [" "*8, " "*4, " "*2, " ", "\t"]
    newline = ["\r\n", "\r", "\n"]
    specialchars = list('-*+[]!"#¤%&/()${}\\?=/&%¤#"!\'^¨~§½<>|') + ["'"]
    extra = []
    _all = []
    _single = None      # set of single-char specials
    _multi = None       # multi-char specials sorted longest-first
    _search = None      # compiled regex to find earliest single-char special

    @staticmethod
    def get_type(t_type):
        print(t_type)
        return [
            [],
            SPECIAL_TOKENS.indentation,
            SPECIAL_TOKENS.newline,
            SPECIAL_TOKENS.specialchars,
            SPECIAL_TOKENS.indentation + SPECIAL_TOKENS.newline,
            SPECIAL_TOKENS.all()
        ][t_type-1]

    @staticmethod
    def all():
        _st = SPECIAL_TOKENS
        if _st._all: return _st._all
        _st._all = _st.indentation + _st.newline + _st.specialchars
        return _st._all


    @classmethod
    def _build(cls):
        if cls._single is not None:
            return
        all_toks = cls.all()
        cls._single = frozenset(t for t in all_toks if len(t) == 1)
        cls._multi = sorted(
            (t for t in all_toks if len(t) > 1),
            key=len, reverse=True
        )
        # Build a regex character class: [<all single-char specials>]
        # re.escape handles things like \, ], ^ inside a class.
        chars = ''.join(re.escape(c) for c in cls._single)
        cls._search = re.compile('[' + chars + ']')

    @classmethod
    def check_string(cls, in_str: str):
        if cls._single is None:
            cls._build()
        if not in_str:
            return None

        first = in_str[0]

        # Phase 1: does in_str start with a special token?
        # Only multi-char specials whose first char matches `first` can match.
        # Since all multi-char specials start with ' ' or '\r', we can skip
        # the loop entirely unless first is one of those.
        if first == ' ' or first == '\r':
            for t in cls._multi:
                if in_str.startswith(t):
                    return t
        if first in cls._single:
            return first

        # Phase 2: find earliest single-char special anywhere in in_str.
        # A single C-level regex scan replaces 38 separate find() calls.
        m = cls._search.search(in_str)
        if m and m.start() > 0:
            return in_str[:m.start()]

        return None

if __name__=="__main__":
    # test conversion
    _dict = TokenDictionary()
    binary = tokenpair_to_binary(("hello", 7, "world", 12345), _dict)
    print(_dict)
    print(hex(int.from_bytes(binary, "little")))
    tokens = binary_to_tokenpair(binary, _dict)
    print(tokens)
    SPECIAL_TOKENS.check_string("hello world")  # triggers _build()
    print("single:", SPECIAL_TOKENS._single)
    print("multi:", SPECIAL_TOKENS._multi)
    print("regex:", SPECIAL_TOKENS._search.pattern)
