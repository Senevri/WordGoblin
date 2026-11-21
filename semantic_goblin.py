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
    event_type: str = ""  # For action pattern: Physical action, Movement, Expression, Communication, Cognitive, State, Contextual event


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


# ── Known entities for capitalization preservation ──────────────────────────

# These are proper nouns that should retain their capitalization
KNOWN_ENTITIES = frozenset([
    # Character names
    "Artemis", "Diana", "Jarvis", "Tony", "Weiss", "Stephen Strange",
    "Astra", "Anansi", "Amazons", "Twili",
    # Places
    "Metropolis", "Centennial Park", "Embassy",
    # Organizations
    "Fate", "Fate SRD",
])

# ── Word sets for pattern matching ──────────────────────────────────────────

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

def _clean_preserve_case(s: str) -> str:
    """Clean string but preserve capitalization for known entities."""
    s = s.strip()
    s = re.sub(r"['\"]+", "", s)
    s = re.sub(r"\s+", " ", s)
    # Capitalize known entities
    for entity in KNOWN_ENTITIES:
        # Use word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(entity) + r'\b'
        s = re.sub(pattern, entity, s, flags=re.IGNORECASE)
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
    r"(?P<subject>\w[\w\s]*?)\s+(?:has|have)\s+(?P<object>\w[\w\s]*?)(?:\.|$)",
    re.IGNORECASE,
)

def _extract_has(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean_preserve_case(m.group("subject"))
    obj = _clean_no_articles(m.group("object"))
    return ExtractedFact("has", subj, "--has-->", obj, source_sentence=sentence)


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


# --- 10b. Inverted Attribute: "How X Y is" -> "Y is X" ---
_RE_INVERTED_ATTR = re.compile(
    r"how\s+(?P<adj>\w+)\s+(?P<subject>\w+)\s+is(?:\.|$)",
    re.IGNORECASE,
)

def _extract_inverted_attr(sentence: str, m) -> Optional[ExtractedFact]:
    subj = _clean(m.group("subject"))
    obj = _clean(m.group("adj"))
    return ExtractedFact("attribute", subj, "has_property", obj, source_sentence=sentence)


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



# --- 11. Communication: "X talk/tell to Y about Z" ---
_RE_COMMUNICATE = re.compile(
    r'(?P<speaker>\w[\w\s]*?)\s+(talk|tell|explain|ask|mention)\s+(?:to\s+)?(?P<listener>\w[\w\s]*?)\s+(?:about\s+(?P<topic>\w[\w\s]*?))?(?:\.|$)',
    re.IGNORECASE,
)

def _extract_communicate(sentence: str, m) -> Optional[ExtractedFact]:
    speaker = _clean_preserve_case(m.group("speaker"))
    listener = _clean_preserve_case(m.group("listener"))
    topic = _clean(m.group("topic")) if m.group("topic") else ""
    if topic:
        return ExtractedFact("communicate", speaker, "communicates_with", listener,
                           source_sentence=sentence)
    return ExtractedFact("communicate", speaker, "communicates_with", listener,
                       source_sentence=sentence)


# --- 11. Action: "X verb the Y" with event type classification ---

# Verbs that indicate movement
_MOVEMENT_VERBS = frozenset([
    "appears", "comes", "goes", "moves", "walks", "runs", "jumps", "steps",
    "enters", "exits", "leaves", "arrives", "returns", "displaces",
])

# Verbs that indicate expression
_EXPRESSION_VERBS = frozenset([
    "raises", "hides", "huffs", "makes", "smiles", "grins", "laughs",
    "frowns", "nods", "shakes", "tilts", "gestures",
])

# Verbs that indicate communication
_COMMUNICATION_VERBS = frozenset([
    "says", "tells", "asks", "answers", "speaks", "whispers", "shouts",
    "explains", "mentions", "replies", "responds",
])

# Verbs that indicate cognitive processes
_COGNITIVE_VERBS = frozenset([
    "considers", "thinks", "realizes", "understands", "notices", "recognizes",
    "decides", "wonders", "remembers", "forgets", "believes", "suspects",
])

# Verbs that indicate states
_STATE_VERBS = frozenset([
    "is", "are", "was", "were", "seems", "feels", "remains", "stays",
])

# Verbs that indicate contextual events (past tense, narrative)
_CONTEXTUAL_VERBS = frozenset([
    "came", "went", "gave", "took", "made", "set", "put", "held",
    "picked", "handed", "programmed", "mentioned", "approved",
])

# Verbs that indicate physical actions
_PHYSICAL_VERBS = frozenset([
    "cracks", "closes", "opens", "sets", "grabs", "holds", "studies",
    "finishes", "checks", "feels", "taps", "brushes", "forms",
])

def _classify_event_type(action_word: str) -> str:
    """Classify an action word into an event type."""
    action_lower = action_word.lower()
    if action_lower in _MOVEMENT_VERBS:
        return "Movement"
    elif action_lower in _EXPRESSION_VERBS:
        return "Expression"
    elif action_lower in _COMMUNICATION_VERBS:
        return "Communication"
    elif action_lower in _COGNITIVE_VERBS:
        return "Cognitive"
    elif action_lower in _STATE_VERBS:
        return "State"
    elif action_lower in _CONTEXTUAL_VERBS:
        return "Contextual event"
    elif action_lower in _PHYSICAL_VERBS:
        return "Physical action"
    else:
        # Default to Physical action for unknown verbs
        return "Physical action"

_agent_words_pattern = "|".join(
    sorted(map(re.escape, AGENT_WORDS), key=len, reverse=True)
)
_AGENT_PATTERN = r'(?:[A-Z]\w+|\b(?:' + _agent_words_pattern + r')\b)\w*'
_RE_ACTION = re.compile(
    r'(?P<agent>' + _AGENT_PATTERN + r')\b\s+(?P<action>\w+)\s+(?:(?:\b(?:the|a|an)\b)\s+)?(?P<patient>\w[\w\s]*?)(?:\.|$)',
)

def _extract_action(sentence: str, m) -> Optional[ExtractedFact]:
    agent = m.group("agent").strip()
    action = m.group("action")
    patient = m.group("patient").strip()

    # Filter out garbage: agent should be a proper noun or pronoun, not a random word
    # Common garbage patterns: "not", "and", "or", "but", "if", "unless", etc.
    garbage_words = frozenset([
        "not", "and", "or", "but", "if", "unless", "when", "while", "where",
        "what", "which", "who", "whom", "whose", "that", "this", "these",
        "those", "there", "here", "then", "than", "so", "as", "to", "for",
        "with", "from", "in", "on", "at", "by", "of", "up", "out", "off",
        "over", "under", "again", "further", "once", "only", "very",
        "also", "just", "even", "still", "already", "yet", "now", "always",
        "never", "ever", "sometimes", "often", "usually", "probably",
        "maybe", "perhaps", "certainly", "definitely", "absolutely",
        "actually", "basically", "essentially", "literally", "figuratively",
    ])

    agent_lower = agent.lower().strip()
    if agent_lower in garbage_words:
        return None

    # Filter out possession verbs - these are handled by the 'has' pattern
    action_lower = action.lower().strip()
    if action_lower in POSSESSION_VERBS:
        return None

    # Also filter if agent is too short (single letter except I, A)
    if len(agent_lower) == 1 and agent_lower not in ("i", "a"):
        return None

    # Classify event type
    event_type = _classify_event_type(action)

    # Use preserve case for proper nouns
    agent_clean = _clean_preserve_case(agent)
    patient_clean = _clean_preserve_case(patient)

    return ExtractedFact(
        "action", agent_clean, "action", f"{action} {patient_clean}",
        source_sentence=sentence, event_type=event_type
    )


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
    (_RE_INVERTED_ATTR, _extract_inverted_attr),
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
        """Split text into sentences on '.', '!', '?', preserving punctuation."""
        if not text.strip():
            return []
        # Use finditer to capture sentences with their trailing punctuation
        matches = re.finditer(r'([^.!?]*[.!?]+)', text)
        result = []
        for m in matches:
            sentence = m.group(1).strip()
            if sentence:
                result.append(sentence)
        return result


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