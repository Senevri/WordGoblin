from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from wordgoblins import WordGoblin, test_two, test_three, test_four
def build_goblin(path):
    path = Path(path)

    print(path)
    text = path.read_text(encoding="utf-8")

    goblin = WordGoblin(text)
    goblin.build_sampling_cache()
    goblin.save(path.with_suffix(".pickle"))

    return path.stem, goblin.word_distances, goblin.sampling_cache


def build_goblins(directory):
    paths = list(Path(directory).glob("*.txt"))
    paths.extend(list(Path(directory).glob("*.md")))
    print(len(paths))
    for path in paths:
        picklepath = path.with_suffix(".pickle").resolve()
        print(path, picklepath)
        if picklepath.is_file():
            paths.remove(path)
    print(len(paths))
    #exit(0)

    with ProcessPoolExecutor() as pool:
        results = pool.map(build_goblin, paths)

    goblins = {}

    for name, distances, cache in results:
        goblin = WordGoblin("")
        goblin.word_distances = distances
        goblin._sampling_cache = cache
        goblin.words = list(distances)
        goblins[name] = goblin

    return goblins

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("text_file", help="The text file or path to read")

    args = parser.parse_args()
    # Load text file

    path = Path(args.text_file)
    # if path.is_dir():
    #     for file in path.iterdir():
    #         if file.suffix in [".txt", ".md"]:
    #             args.text_file = file
    #             picklefile = Path(args.text_file).with_suffix(".pickle")
    #             if picklefile.is_file():
    #                 # text = ""
    #                 # wg = WordGoblin("")
    #                 # wg.load(picklefile)
    #                 # wg.build_sampling_cache()
    #                 pass
    #             else:
    #                 with open(args.text_file) as f:
    #                     text = f.read()
    #                 wg = WordGoblin(text)
    #                 wg.save(picklefile)


    goblins = build_goblins(path)
    # for goblin in goblins:
    #     goblins[goblin].save(Path(goblin).with_suffix(".pickle"))

    test_two()
    wg = test_three()
    test_four(wg)