from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import argparse
import ast
import contextlib
import importlib
import inspect
import io

# Register new goblin types here: level -> (module_name, class_name, file_suffix)
GOBLINS = {
    "word": ("wordgoblins", "WordGoblin", ".pickle"),
    "letter": ("lettergoblins", "LetterGoblin", ".letterpickle"),
    "bin": ("nmgramgoblins", "NMGramGoblin", ".bin.pickle"),
}


def get_goblin_spec(level: str):
    """Dynamically import and return (GoblinClass, suffix) for a given level."""
    module_name, class_name, suffix = GOBLINS[level]
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls, suffix


def filter_kwargs(goblin_cls, extra: dict) -> dict:
    """Keep only kwargs that goblin_cls.__init__ actually accepts."""
    sig = inspect.signature(goblin_cls.__init__)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return extra
    return {k: v for k, v in extra.items() if k in sig.parameters}


def load_goblin(pickle_path: Path, goblin_cls):
    """Instantiate a goblin from an existing pickle file."""
    goblin = goblin_cls("")
    goblin.load(pickle_path)
    goblin.build_sampling_cache()
    return goblin


def build_goblin(text_path: Path, goblin_cls, suffix: str, extra: dict = None):
    """Build a goblin from a text file, cache it to disk, and return it."""
    text = text_path.read_text(encoding="utf-8")
    kwargs = filter_kwargs(goblin_cls, extra or {})
    with contextlib.redirect_stdout(io.StringIO()):
        goblin = goblin_cls(text, **kwargs)
        goblin.tokenize()
        goblin.build_sampling_cache()
    goblin.save(text_path.with_suffix(suffix))
    return goblin


def _build_worker(args):
    """Top-level worker for ProcessPoolExecutor: builds pickle if missing."""
    text_path, level, extra = args
    goblin_cls, suffix = get_goblin_spec(level)
    pickle_path = text_path.with_suffix(suffix)
    if not pickle_path.is_file():
        build_goblin(text_path, goblin_cls, suffix, extra)
    return pickle_path


def combine_goblins(goblins, goblin_cls, multiplier: float = 1.0):
    """Merge an iterable of goblins into a single combined instance."""
    combined = goblin_cls("")
    for i, goblin in enumerate(goblins):
        if i == 0:
            combined.load_model_data(goblin.get_model_data())
        else:
            combined.combine_with(goblin, multiplier)
    combined.build_sampling_cache()
    return combined


def resolve_pickle(path: Path, suffix: str) -> Path:
    return path if path.is_file() else path.with_suffix(suffix)


def parse_kv(items) -> dict:
    extra = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep:
            raise argparse.ArgumentTypeError(f"Expected key=value, got '{item}'")
        try:
            extra[key] = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            extra[key] = value
    return extra


def main():
    parser = argparse.ArgumentParser(description="Devour text into goblin models")
    parser.add_argument("target", nargs="?", help="Text file or directory to process")
    parser.add_argument("--level", choices=GOBLINS.keys(), default="word")
    parser.add_argument("--out", default="combined", help="Output base path")
    parser.add_argument("--combine", nargs=2, metavar=("PICKLE1", "PICKLE2"),
                        help="Combine two existing pickles without modifying them")
    parser.add_argument("--multiplier", nargs=2, type=float, metavar=("W1", "W2"),
                        help="Weight ratio when combining two pickles (W2 / W1)")
    parser.add_argument("--set", nargs="*", default=[], help="Extra key=value pairs (e.g. max_token_len=8)")

    args = parser.parse_args()
    extra_kwargs = parse_kv(args.set)

    goblin_cls, suffix = get_goblin_spec(args.level)
    out_path = Path(args.out)

    if args.combine:
        pickles = [resolve_pickle(Path(p), suffix) for p in args.combine]
        if any(p.resolve() == out_path.resolve() for p in pickles if out_path.exists()):
            raise SystemExit(f"Refusing to overwrite input pickle with --out {out_path}")

        ratio = (args.multiplier[1] / args.multiplier[0]) if args.multiplier else 1.0
        goblins = [load_goblin(p, goblin_cls) for p in pickles]
        combined = combine_goblins(goblins, goblin_cls, multiplier=ratio)

    elif args.target:
        target = Path(args.target)
        if target.is_dir():
            files = sorted([*target.glob("*.txt"), *target.glob("*.md")])
            if not files:
                raise SystemExit(f"No .txt or .md files found in {target}")

            print(f"Processing {len(files)} files ({args.level})...")
            with ProcessPoolExecutor() as pool:
                tasks = [(f, args.level, extra_kwargs) for f in files]
                pickle_paths = list(pool.map(_build_worker, tasks))
            goblins = [load_goblin(p, goblin_cls) for p in pickle_paths]
            combined = combine_goblins(goblins, goblin_cls)
        else:
            combined = build_goblin(target, goblin_cls, suffix, extra_kwargs)
    else:
        parser.error("Provide a text file/directory or --combine PICKLE1 PICKLE2")

    combined.save(out_path)
    print(f"Saved {args.level} model to {out_path} ({len(combined.words)} entries)")


if __name__ == "__main__":
    main()