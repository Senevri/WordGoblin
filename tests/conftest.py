"""Shared fixtures for the WordGoblin test-suite."""
import pytest
from pathlib import Path
import sys
from logging import getLogger

log = getLogger(__name__)

SCRIPT_ROOT = Path(__file__).resolve().parent.parent

if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wordgoblins import WordGoblin


@pytest.fixture
def sample_text():
    return (
        "the quick brown fox jumps over the lazy dog "
        "the rain in spain falls mainly on the plain"
    )


@pytest.fixture
def wg(sample_text):
    goblin = WordGoblin(sample_text)
    goblin.build_sampling_cache()
    log.info(f"Unique words: {len(goblin.unique_words)}")
    return goblin


@pytest.fixture
def phrase():
    # A known phrase that appears verbatim in the training text.
    return "You know that feeling when"
