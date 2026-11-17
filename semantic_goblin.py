"""SemanticGoblin — extracts structured facts from natural language patterns."""
import re
from dataclasses import dataclass, field
from typing import List, Optional
import pickle
from pathlib import Path

# ── Fact data structure ──────────────────────────────────────────────────────

@dataclass
class ExtractedFact:
    """A single extracted semantic fact."""
    pattern: str          # pattern family name
    subject: str          # entity X
    predicate: str        # relationship verb
    object: str           # entity Y / value
    confidence: float = 1.0
    source_sentence: str = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    """Lowercase, strip, collapse whitespace, remove quotes."""
    s = s.strip().lower()
    s = re.sub(r"['\"]+", "", s)
    return re.sub(r"\s+", " ", s)


def _clean_no_articles(s: str) -> str:
    """Remove leading 'the', 'a', 'an' for cleaner subjects."""
    s = _clean(s)
    for prefix in ("the ", "a ", "an "):
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


# ── Pattern definitions ──────────────────────────────────────────────────────

# Each entry: (compiled_regex, pattern_name, extraction_fn)
# extraction_fn(sentence, match) -> Optional[ExtractedFact]


# --- 1. Definitional: "X is a/an Y" ---
_RE_IS_A = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+is\s+(?:a|an)\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_is_a(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    return ExtractedFact("is_a", subj, "is_a", obj, source_sentence=sentence)


# --- 2. Definitional: "X is known as Y" ---
_RE_KNOWN_AS = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+is\s+known\s+as\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_known_as(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean(m.group("object"))
    return ExtractedFact("known_as", subj, "known_as", obj, source_sentence=sentence)


# --- 3. Definitional: "X refers to Y" ---
_RE_REFERS_TO = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+refers\s+to\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_refers_to(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    return ExtractedFact("refers_to", subj, "refers_to", obj, source_sentence=sentence)


# --- 4. Relational: "The X of Y is Z" / "The capital of France is Paris" ---
_RE_OF_IS = re.compile(
    r"the\s+(?P<relation>\w+)\s+of\s+(?P<subject>\w[\w\s]*?)\s+is\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_of_is(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    rel = _clean(m.group("relation"))
    pred = f"has_{rel}"
    return ExtractedFact("capital_of", subj, pred, obj, source_sentence=sentence)


# --- 5. Relational: "X has Y" ---
_RE_HAS = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+has\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_has(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    return ExtractedFact("has", subj, "has", obj, source_sentence=sentence)


# --- 6. Relational: "X belongs to Y" ---
_RE_BELONGS_TO = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+belongs\s+to\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_belongs_to(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    return ExtractedFact("belongs_to", subj, "belongs_to", obj, source_sentence=sentence)


# --- 7. Causal: "Because X, Y" ---
_RE_BECAUSE = re.compile(
    r"because\s+(?P<cause>\w[\w\s]*?)[,.\s]+(?P<effect>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_because(sentence: str, m) -> Optional[ExtractedFact]:
    cause = _clean_no_articles(m.group("cause"))
    effect = _clean_no_articles(m.group("effect"))
    return ExtractedFact("because", cause, "caused", effect, source_sentence=sentence)


# --- 8. Causal: "X leads to Y" ---
_RE_LEADS_TO = re.compile(
    r"(?P<cause>\w[\w\s]*?)\s+leads\s+to\s+(?P<effect>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_leads_to(sentence: str, m) -> Optional[ExtractedFact]:
    cause = _clean_no_articles(m.group("cause"))
    effect = _clean_no_articles(m.group("effect"))
    return ExtractedFact("leads_to", cause, "leads_to", effect, source_sentence=sentence)


# --- 9. Temporal: "After X, Y" ---
_RE_AFTER = re.compile(
    r"after\s+(?P<earlier>\w[\w\s]*?)[,.\s]+(?P<later>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_after(sentence: str, m) -> Optional[ExtractedFact]:
    earlier = _clean_no_articles(m.group("earlier"))
    later = _clean_no_articles(m.group("later"))
    return ExtractedFact("after", earlier, "precedes", later, source_sentence=sentence)


# --- 10. Attribute: "X is Y" (adjective) ---
_RE_ATTR = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+is\s+(?P<object>\w+)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_attr(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean(m.group("object"))
    # Skip if already matched by is_a (object starts with lowercase = adjective)
    if obj[0].islower():
        return ExtractedFact("attribute", subj, "has_property", obj, source_sentence=sentence)
    return None


# --- 11. Action: "X verb the Y" ---
_RE_ACTION = re.compile(
    r"(?P<agent>\w[\w\s]*?)\s+(?P<action>\w+)\s+(?:the|a|an)\s+(?P<patient>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_action(sentence: str, m) -> Optional[ExtractedFact]:
    agent = _clean_no_articles(m.group("agent"))
    action = m.group("action")
    patient = _clean_no_articles(m.group("patient"))
    return ExtractedFact("action", agent, "action", f"{action} {patient}", source_sentence=sentence)


# --- 12. Comparative: "X is more Y than Z" ---
_RE_COMPARATIVE = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+is\s+more\s+(?P<adj>\w+)\s+than\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_comparative(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    adj = _clean(m.group("adj"))
    return ExtractedFact("comparative", subj, f"{adj}_than", obj, source_sentence=sentence)


# --- 13. Superlative: "X is the most Y" / "X is the Y-est" ---
_RE_SUPERLATIVE = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+is\s+the\s+(?:most\s+)?(?P<adj>\w+)(?:\s+(?P<object>\w[\w\s]*?))?(?:\.|$)",
    re.IGNORECASE,
)

def _extract_superlative(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    adj = _clean(m.group("adj"))
    obj = _clean_no_articles(m.group("object")) if m.group("object") else ""
    return ExtractedFact("superlative", subj, adj, obj, source_sentence=sentence)


# --- 14. Conditional: "If X, Y" ---
_RE_IF = re.compile(
    r"if\s+(?P<condition>\w[\w\s]*?)[,.\s]+(?P<result>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_if(sentence: str, m) -> Optional[ExtractedFact]:
    cond = _clean_no_articles(m.group("condition"))
    result = _clean_no_articles(m.group("result"))
    return ExtractedFact("conditional", cond, "implies", result, source_sentence=sentence)


# --- 15. Ability: "X can Y" ---
_RE_CAN = re.compile(
    r"(?P<subject>\w[\w\s]*?)\s+can\s+(?P<ability>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_can(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_no_articles(m.group("subject"))
    ability = _clean_no_articles(m.group("ability"))
    return ExtractedFact("can", subj, "can", ability, source_sentence=sentence)


# ── Pattern registry ─────────────────────────────────────────────────────────

PATTERNS = [
    # Order matters: more specific patterns first to avoid false positives
    (_RE_IS_A, _extract_is_a),
    (_RE_KNOWN_AS, _extract_known_as),
    (_RE_REFERS_TO, _extract_refers_to),
    (_RE_OF_IS, _extract_of_is),
    (_RE_HAS, _extract_has),
    (_RE_BELONGS_TO, _extract_belongs_to),
    (_RE_BECAUSE, _extract_because),
    (_RE_LEADS_TO, _extract_leads_to),
    (_RE_AFTER, _extract_after),
    (_RE_CAN, _extract_can),
    (_RE_COMPARATIVE, _extract_comparative),
    (_RE_SUPERLATIVE, _extract_superlative),
    (_RE_IF, _extract_if),
    (_RE_ACTION, _extract_action),
    (_RE_ATTR, _extract_attr),
]


# ── SemanticGoblin class ─────────────────────────────────────────────────────

class SemanticGoblin:
    """Extracts structured semantic facts from natural language text."""

    def __init__(self, text: str):
        self.text = text
        self._facts: List[ExtractedFact] = []

    def save_facts(self, path: str):
        """Save extracted facts to a pickle file."""
        _path = Path(path)
        if len(_path.suffixes) < 2 or "".join(_path.suffixes[-2]) != ".facts.pickle":
            # remove old suffixes
            _path = _path.with_suffix("")
            # add new suffix
            _path = _path.with_suffix(".facts.pickle")
        with open(_path, "wb") as f:
            pickle.dump(self._facts, f)
        print(f"Saved {len(self._facts)} facts to {_path}")

    def load_facts(self, path: str):
        with open(path, "rb") as f:
            self._facts = pickle.load(f)
        print(f"Loaded {len(self._facts)} facts from {path}")


    def extract(self) -> List[ExtractedFact]:
        """Run all pattern matchers and return extracted facts."""
        self._facts = []
        sentences = self._split_sentences(self.text)
        for sentence in sentences:
            self._extract_from_sentence(sentence)
        return self._facts

    def _split_sentences(self, text: str) -> List[str]:
        # FIXME: Naive implementation. will happily split on abbreviations,
        # initials, decimal numbers, and punctuation inside quoted dialogue.
        # It also discards the delimiters.
        """Split text into sentences on '.', '!', '?'."""
        if not text.strip():
            return []
        return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    def _extract_from_sentence(self, sentence: str):
        """Try each pattern against a single sentence."""
        for regex, extractor in PATTERNS:
            m = regex.search(sentence)
            if m:
                fact = extractor(sentence, m)
                if fact is not None:
                    self._facts.append(fact)

    def get_facts_by_pattern(self, pattern_name: str) -> List[ExtractedFact]:
        """Filter facts by pattern type."""
        return [f for f in self._facts if f.pattern == pattern_name]

    def __repr__(self):
        return f"SemanticGoblin(text={self.text!r}, facts={len(self._facts)})"

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Goblin")
    parser.add_argument("text_file", help="The text file or path to read")
    parser.add_argument("--pickle", help="The pickle file or path to read")

    args = parser.parse_args()

    path = Path(args.text_file)
    if not args.pickle:
        sg = SemanticGoblin(path.read_text())
        facts = sg.extract()
        sg.save_facts(str(Path(path).with_suffix(".facts.pickle")))
    else:
        sg = SemanticGoblin("")
        sg.load_facts(args.pickle)
        facts = sg._facts

    print("=" * 70)
    print("SEMANTIC GOBLIN — Extracted Facts")
    print("=" * 70)

    for f in facts:
        print(f"  [{f.pattern:12s}] {f.subject:20s} --{f.predicate:15s}> {f.object}")

    print("=" * 70)
    print(f"Total facts extracted: {len(facts)}")
    print("=" * 70)


if __name__ == "__main__":
    main()