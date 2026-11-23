
from pathlib import Path
import pickle
import sys
from collections import Counter

path = Path(sys.argv[1])

with path.open("rb") as f:
    data = pickle.load(f)

def inspect(obj, name="root", depth=0, max_depth=3):
    indent = "  " * depth
    print(f"{indent}{name}: {type(obj).__name__}", end="")

    if isinstance(obj, (dict, list, tuple, set, frozenset)):
        print(f" | len={len(obj):,}")
    else:
        print(f" | {obj!r}" if isinstance(obj, (int, float, str, bytes, bool, type(None))) else "")

    if depth >= max_depth:
        return

    if isinstance(obj, dict):
        for key, value in list(obj.items())[:20]:
            inspect(value, f"[{key!r}]", depth + 1, max_depth)

    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj[:10]):
            inspect(value, f"[{i}]", depth + 1, max_depth)

    elif isinstance(obj, (set, frozenset)):
        for i, value in enumerate(list(obj)[:10]):
            inspect(value, f"item {i}", depth + 1, max_depth)

inspect(data)
