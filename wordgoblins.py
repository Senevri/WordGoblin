import pathlib
import pickle
import asyncio
import random
from timeit import default_timer as timer
import threading

class WordGoblin():

    def __init__(self, text_str):
        self.word_distances = {}
        self.words = self.get_words(text_str)
        self.word_distances = self.get_word_distances(self.words)
        self._sampling_cache = {}

    def get_words(self, text):
        whitespace = [" ", "\t", "\n", "\r"]
        lines = []
        for key in whitespace:
            text = text.replace(key, " ")
        #words = (text.split(" "))
        words = [w for w in text.split(" ") if w]
        return words


    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.word_distances, f)

    def load(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.word_distances = {}
        for word, associations in data.items():
            if isinstance(associations, dict):
                # Already using the new representation
                self.word_distances[word] = associations
            else:
                # Convert old list representation
                converted = {}

                for other_word, distance in associations:
                    key = (other_word, distance)
                    converted[key] = converted.get(key, 0) + 1

                self.word_distances[word] = converted

        self.words = list(self.word_distances.keys())


    def get_segment(self, word, window):
        if word not in self.word_distances:
            self.word_distances[word] = {}
        #self.word_distances[word].extend(list((w, idx) for idx, w in enumerate(window)))

        for distance, other_word in enumerate(window):

            key = (other_word, distance)
            #print(self.word_distances[word], key)
            self.word_distances[word][key] = (
                self.word_distances[word].get(key, 0) + 1
            )

    def get_word_data(self, word):
        return self.word_distances[word]



    def get_word_distances(self, words):
        i = 0
        max_distance = 3
        while words:
            word = words[0]
            #idx_last = max_distance - abs(len(words)-max_distance)
            #print(idx_last)
            window = words[1:max_distance + 1]
            self.get_segment(word, window)
            words = words[1:]
            i += 1
            # self.word_distances[word] = sorted(self.word_distances[word], key=lambda x: x[0])
            print(f"{i}/{len(words)}", end="\r")
        return self.word_distances

    def combine_distances(self):
        combined_distances = {}
        for word in self.word_distances:
            combined_distances[word] = {}
            for pair in self.word_distances[word]:
                if word in combined_distances[word]:
                    combined_distances[word].update({pair[1]: pair[0]})
                    continue
                combined_distances[word][pair[1]] = pair[0]
        return combined_distances

    def get_nearby_words(self, word):
        if word not in self.word_distances:
            self.word_distances[word] = {}
        distances = self.word_distances[word]
        return [
            (other_word, distance, weight)
            for (other_word, distance), weight in distances.items()
        ]

    def get_next_word(self, word):
        if word not in self.word_distances:
            self.word_distances[word] = {}
            return random.choice(self.words)
        distances = self.word_distances[word]
        return random.choice([
            other_word
            for (other_word, distance), weight in distances.items()
            if distance == 1
        ])

    def get_buffer_words(self, buffer):
        for word in buffer:
            nearby = [x for x in self.get_nearby_words(word) if x[0].strip()]
            for other_word, distance, weight in nearby:
                if other_word in buffer:
                    nearby = self.get_nearby_words(other_word)
                    yield random.choice(nearby)[0]
                else:
                    yield other_word



    # def generate_random_sentence(self, starting_word="the"):
    #     nearby_words = self.get_nearby_words(starting_word)
    #     # print(nearby_words)
    #     sentence = [starting_word]
    #     for i in range(16):
    #         words_in_irange = [word for word, distance in nearby_words if distance < 2]
    #         if len(words_in_irange) < 2:
    #             break
    #         word = random.choice(words_in_irange)
    #         sentence.append(word)
    #         nearby_words = self.get_nearby_words(word)
    #     return " ".join(sentence)

    # def generate_random_sentence(self, starting_word="the"):
    #     nearby_words = self.get_nearby_words(starting_word)
    #     sentence = [starting_word]

    #     for i in range(16):
    #         candidates = [
    #             (word, weight)
    #             for word, distance, weight in nearby_words
    #             if distance < 2
    #         ]

    #         if sum(weight for word, weight in candidates) < 2:
    #             break

    #         words = [word for word, weight in candidates]
    #         weights = [weight for word, weight in candidates]

    #         word = random.choices(words, weights=weights, k=1)[0]

    #         sentence.append(word)
    #         nearby_words = self.get_nearby_words(word)

    #     return " ".join(sentence)

    def generate_random_sentence(self, starting_word="the", length=16):
        sentence = [starting_word]
        word = starting_word

        for i in range(length):
            candidates = self.sampling_cache.get(word)

            if not candidates:
                break

            words, weights = candidates
            word = random.choices(words, weights=weights, k=1)[0]
            sentence.append(word)
            # if word.endswith(",") or word == ",":
            #     break

            if word.endswith(".") or word == ".":
                break
        while not (word.endswith(".") or word == "."):
            word = self.get_next_word(word)
            sentence.append(word)

        return " ".join(sentence)

    def build_sampling_cache(self):
        self._sampling_cache = {}

        for word, associations in self.word_distances.items():
            candidates = [
                (other_word, weight)
                for (other_word, distance), weight in associations.items()
                if distance < 1
            ]

            if candidates:
                words, weights = zip(*candidates)
                self._sampling_cache[word] = (words, weights)

    @property
    def unique_words(self):
        return list(self.word_distances.keys())

    @property
    def sampling_cache(self):
        if not self._sampling_cache:
            self.build_sampling_cache()
        return self._sampling_cache

def chunk_text(text, chunk_size):
    while text:
        index = str(text[chunk_size:]).index(". ")
        if index == -1:
            index = 0
        yield text[:index + chunk_size]
        text = text[index + chunk_size:]

    return


def threaded_gen(text):
    def thread_goblin(text):
        return WordGoblin(text)

    threads = []
    chunk_size = len(text) // 8
    for t in chunk_text(text, chunk_size):
        threads.append(threading.Thread(target=thread_goblin, args=(t,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

def main(filename):
    from pprint import pprint
    print("Hello from wordgoblin!")

    picklefile = pathlib.Path(filename).with_suffix(".pickle")
    if picklefile.is_file():
        text = ""
        wg = WordGoblin("")
        wg.load(picklefile)
        wg.build_sampling_cache()
    else:
        with open(args.text_file) as f:
            text = f.read()
        wg = WordGoblin(text)
        wg.save(picklefile)
    # print(wg.word_distances)
    # print("-"*80)
    # pprint(wg.combine_distances())
    # print("-"*80)
    # print(wg.unique_words, len(wg.unique_words))
    # print("-"*80)
    # columns = 6
    # for word in (wg.get_nearby_words("the")):
    #     print(f"{word[0]:>3}: {word[1][:16]:<16}", end=" ")
    #     columns -= 1
    #     if columns == 0:
    #         print()
    #         columns = 6

    print("-"*80)
    start = timer()

    for j in range (3):
        print("-"*80)
        for i in range (10):
            print(wg.generate_random_sentence(random.choice(wg.unique_words)))
    end = timer()
    print(f"Time taken: {end - start}") # Time

    # for i in range(10):
    #     word = random.choice(wg.unique_words)
    #     print (f"{word}: {wg.get_word_data(word)}")

def test_two():
    wg1 = WordGoblin("the quick brown fox jumps over the lazy dog")
    wg2 = WordGoblin("the rain in spain falls mainly on the plain")
    wg1.build_sampling_cache()
    wg2.build_sampling_cache()
    print(wg1.word_distances["the"])
    print(wg2.word_distances["the"])

    # how do I combine these two?
    print(wg1.word_distances)
    for word, associations in wg2.word_distances.items():
        if word not in wg1.word_distances:
                wg1.word_distances[word] = {}

        for association, weight in associations.items():
            wg1.word_distances[word][association] = (
                wg1.word_distances[word].get(association, 0) + weight
            )
    print(wg1.word_distances)
    print(wg1.word_distances["the"])

def test_three():
    start = timer()
    goblins = []
    for path in pathlib.Path.cwd().glob("text_and_pickles/*.pickle"):
        wg = WordGoblin("")
        wg.load(path)
        wg.build_sampling_cache()
        print(path, len(wg.unique_words))
        goblins.append(wg)
        print("original goblin phrases")
        for i in range(3):
            word = random.choice(wg.unique_words)
            print (f"Word: {word}:")
            for j in range(10):
                print(f"\t{wg.generate_random_sentence(word)}")

    end = timer()
    print(f"Time taken: {end - start}")

    wg = goblins[0]
    print ("Unique words before", len(wg.unique_words))
    for g in goblins[1:]:
        for word, associations in g.word_distances.items():

            if word not in wg.word_distances:
                wg.word_distances[word] = {}

            for association, weight in associations.items():
                wg.word_distances[word][association] = (
                    wg.word_distances[word].get(association, 0) + weight
                )

    start = timer()
    wg.build_sampling_cache()
    end = timer()
    print(f"Cache build Time taken: {end - start}")

    wg.word_distances = dict(sorted(wg.word_distances.items()))
    start = timer()
    print ("Unique words after", len(wg.unique_words))
    for i in range(10):
        word = random.choice(wg.unique_words)
        print (f"Word: {word}:")
        for j in range(3):
            print(f"\t{wg.generate_random_sentence(word, length=32)}")
    end = timer()
    print(f"Time taken: {end - start}")
    wg.save("combined.pickle")
    return wg

def test_four(wg:WordGoblin):
    sizes = sorted(len(words) for words, weights in wg.sampling_cache.values())

    print("Median:", sizes[len(sizes) // 2])
    print("95th percentile:", sizes[int(len(sizes) * 0.95)])
    print("Maximum:", sizes[-1])
    for word, (words, weights) in sorted(
        wg.sampling_cache.items(),
        key=lambda item: len(item[1][0]),
        reverse=True
    )[:20]:
        print(len(words), repr(word))

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("text_file", help="The text file or path to read")

    args = parser.parse_args()
    # Load text file

    path = pathlib.Path(args.text_file)
    if path.is_dir():
        for file in path.iterdir():
            if file.suffix in [".txt", ".md"]:
                args.text_file = file
                picklefile = pathlib.Path(args.text_file).with_suffix(".pickle")
                if picklefile.is_file():
                    # text = ""
                    # wg = WordGoblin("")
                    # wg.load(picklefile)
                    # wg.build_sampling_cache()
                    pass
                else:
                    with open(args.text_file) as f:
                        text = f.read()
                    wg = WordGoblin(text)
                    wg.save(picklefile)
    # wg = test_three()
    # test_four(wg)

    start = timer()
    wg = WordGoblin("")
    wg.load("combined.pickle")
    wg.build_sampling_cache()
    words = [w for w in wg.unique_words if w and (w[0].isupper() or w.startswith("..."))]
    for i in range(30):
        word = random.choice(words)
        print (f"Word: {word}:")
        for j in range(3):
            print(f"\t{wg.generate_random_sentence(word, length=32)}")
    stop = timer()
    print(f"Time taken: {stop - start}")
