from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import io
import pickle
import contextlib

from wordgoblins import WordGoblin


def _load_goblin_class(level):
    if level == "letter":
        from lettergoblins import LetterGoblin
        return LetterGoblin, ".letterpickle", "letter_distances"
    return WordGoblin, ".pickle", "word_distances"


def _make_goblin(goblin_cls, dist_attr, distances, cache):
    """Reconstruct a goblin instance from stored distances + cache."""
    goblin = goblin_cls("")
    setattr(goblin, dist_attr, distances)
    goblin._sampling_cache = cache
    goblin.words = list(distances)
    return goblin


def build_goblin(path, level="word"):
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    goblin_cls, suffix, dist_attr = _load_goblin_class(level)
    # The per-word progress print happens during construction
    # (get_word_distances) and during cache building, so wrap both.
    with contextlib.redirect_stdout(io.StringIO()):
        goblin = goblin_cls(text)
        goblin.build_sampling_cache()
    goblin.save(path.with_suffix(suffix))

    distances = getattr(goblin, dist_attr)
    return path.stem, distances, goblin.sampling_cache


def load_goblin(path, level="word"):
    """Load a goblin from an existing pickle (fast path)."""
    path = Path(path)
    goblin_cls, suffix, dist_attr = _load_goblin_class(level)
    pickle_path = path.with_suffix(suffix)
    with open(pickle_path, "rb") as f:
        data = pickle.load(f)
    # New format stores (distances, words); old format stored only distances.
    if isinstance(data, tuple) and len(data) == 2 and isinstance(data[0], dict):
        distances = data[0]
    else:
        distances = data
    goblin = goblin_cls("")
    setattr(goblin, dist_attr, distances)
    goblin.words = list(distances)
    goblin.build_sampling_cache()
    return path.stem, distances, goblin.sampling_cache


def _worker(path, level):
    goblin_cls, suffix, dist_attr = _load_goblin_class(level)
    pickle_path = path.with_suffix(suffix)
    if pickle_path.is_file():
        return load_goblin(path, level)
    return build_goblin(path, level)


def build_goblins(directory, level="word"):
    """Build goblins for every source, loading existing pickles when present."""
    directory = Path(directory)

    paths = list(directory.glob("*.txt"))
    paths.extend(list(directory.glob("*.md")))

    print(f"{len(paths)} text files to process ({level})")

    goblins = {}
    with ProcessPoolExecutor() as pool:
        for name, distances, cache in pool.map(
            _worker, paths, [level] * len(paths)
        ):
            goblin_cls, suffix, dist_attr = _load_goblin_class(level)
            goblins[name] = _make_goblin(
                goblin_cls, dist_attr, distances, cache
            )

    return goblins


def combine_goblins(goblins, level="word"):
    """Sum the per-source distance maps into a single combined goblin."""
    goblin_cls, suffix, dist_attr = _load_goblin_class(level)
    combined = goblin_cls("")

    first = True
    for goblin in goblins.values():
        source = getattr(goblin, dist_attr)
        if first:
            combined_distances = {
                word: dict(assoc) for word, assoc in source.items()
            }
            combined.__setattr__(dist_attr, combined_distances)
            first = False
        else:
            for word, associations in source.items():
                bucket = combined_distances.setdefault(word, {})
                for key, weight in associations.items():
                    bucket[key] = bucket.get(key, 0) + weight

    combined.words = list(combined_distances.keys())
    combined.build_sampling_cache()
    return combined


def build_combined(directory, level="word", out="combined"):
    goblins = build_goblins(directory, level=level)
    if not goblins:
        raise SystemExit(f"No goblins built for {directory} ({level}).")
    combined = combine_goblins(goblins, level=level)
    out_path = Path(out)
    combined.save(out_path)
    print(f"Saved combined.{level} model to {out_path} "
          f"({len(combined.words)} entries)")
    return combined


def _build_silently(directory, level):
    """Build goblins with the noisy per-word progress suppressed."""
    with contextlib.redirect_stdout(io.StringIO()):
        return build_goblins(directory, level=level)


def _resolve_pickle_path(pickle_path, level="word"):
    """Return the actual .pickle/.letterpickle file for a user-supplied path.

    If the path already points at an existing file it is used verbatim;
    otherwise the level suffix is appended (e.g. ``foo`` -> ``foo.pickle``).
    """
    pickle_path = Path(pickle_path)
    if pickle_path.is_file():
        return pickle_path
    _, suffix, _ = _load_goblin_class(level)
    return pickle_path.with_suffix(suffix)


def _load_goblin_from_pickle(pickle_path, level="word"):
    """Load a goblin instance from a specific pickle file (read-only)."""
    goblin_cls, _, dist_attr = _load_goblin_class(level)
    path = _resolve_pickle_path(pickle_path, level)
    with open(path, "rb") as f:
        data = pickle.load(f)
    # New format stores (distances, words); old format stored only distances.
    if isinstance(data, tuple) and len(data) == 2 and isinstance(data[0], dict):
        distances = data[0]
    else:
        distances = data
    goblin = goblin_cls("")
    setattr(goblin, dist_attr, distances)
    goblin.words = list(distances)
    return goblin


def combine_pickles(pickle_paths, level="word", out="combined"):
    """Combine two existing model pickles into a brand-new pickle.

    Nondestructive: the input pickles are only read, never modified, and the
    output is written to a separate ``--out`` path. Refuses to clobber an
    input pickle. Returns the combined goblin.
    """
    if len(pickle_paths) != 2:
        raise SystemExit("--combine expects exactly two pickle files.")

    resolved = [_resolve_pickle_path(p, level) for p in pickle_paths]
    out_path = Path(out)
    for inp in resolved:
        try:
            if inp.resolve() == out_path.resolve():
                raise SystemExit(
                    f"Refusing to overwrite input pickle {inp} with --out {out}."
                )
        except OSError:
            pass

    goblins = {
        _resolve_pickle_path(p, level).stem: _load_goblin_from_pickle(p, level)
        for p in resolved
    }
    combined = combine_goblins(goblins, level=level)
    combined.save(out_path)
    print(f"Saved combined.{level} model to {out_path} "
          f"({len(combined.words)} entries)")
    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Devour text into goblin models"
    )
    parser.add_argument(
        "text_file", nargs="?",
        help="The text file or directory to read",
    )
    parser.add_argument(
        "--level", choices=["word", "letter"], default="word",
        help="Model level to build (default: word)",
    )
    parser.add_argument(
        "--out", default="combined",
        help="Combined output base name (default: combined)",
    )
    parser.add_argument(
        "--combine", nargs=2, metavar=("PICKLE1", "PICKLE2"),
        help="Combine two existing model pickles into a new pickle "
             "(nondestructive; inputs are left untouched).",
    )
    args = parser.parse_args()

    if args.combine:
        combine_pickles(args.combine, level=args.level, out=args.out)
        return

    if not args.text_file:
        parser.error("a text_file is required unless --combine is given")

    path = Path(args.text_file)
    if path.is_dir():
        goblins = _build_silently(path, args.level)
        if not goblins:
            raise SystemExit(f"No goblins built for {path} ({args.level}).")
        combined = combine_goblins(goblins, level=args.level)
        out_path = Path(args.out)
        combined.save(out_path)
        print(f"Saved combined.{args.level} model to {out_path} "
              f"({len(combined.words)} entries)")
    else:
        stem, distances, cache = build_goblin(path, level=args.level)
        goblin_cls, suffix, dist_attr = _load_goblin_class(args.level)
        g = _make_goblin(goblin_cls, dist_attr, distances, cache)
        combined = combine_goblins({stem: g}, level=args.level)
        out_path = Path(args.out)
        combined.save(out_path)
        print(f"Saved combined.{args.level} model to {out_path}")


if __name__ == "__main__":
    main()
