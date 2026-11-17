import pathlib
import pickle
import asyncio
import random
from timeit import default_timer as timer
import threading
from wordgoblins import WordGoblin

class LetterGoblin(WordGoblin):

    def __init__(self, text_str):
        self.letter_distances = {}
        self.letters = []
        self.letter_distances = self.get_letter_distances(text_str)
        self._sampling_cache = {}


    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.letter_distances, f)

    def load(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.letter_distances = {}
        for word, associations in data.items():
            if isinstance(associations, dict):
                # Already using the new representation
                self.letter_distances[word] = associations
            else:
                # Convert old list representation
                converted = {}

                for other_word, distance in associations:
                    key = (other_word, distance)
                    converted[key] = converted.get(key, 0) + 1

                self.letter_distances[word] = converted

        self.words = list(self.letter_distances.keys())

    def get_segment(self, letter, window):
        if letter not in self.letter_distances:
            self.letter_distances[letter] = {}
        #self.letter_distances[word].extend(list((w, idx) for idx, w in enumerate(window)))

        for distance, other_letter in enumerate(window):

            key = (other_letter, distance)
            #print(self.letter_distances[word], key)
            self.letter_distances[letter][key] = (
                self.letter_distances[letter].get(key, 0) + 1
            )

        self.letters.append(letter)


    def _get_letter_distances(self, text):
        i = 0
        max_distance = 12
        while text:
            letter = text[0]
            #idx_last = max_distance - abs(len(words)-max_distance)
            #print(idx_last)
            window = text[1:max_distance + 1]
            self.get_segment(letter, window)
            text = text[1:]
            i += 1
            # self.letter_distances[word] = sorted(self.letter_distances[word], key=lambda x: x[0])
            print(f"{i}/{len(text)}", end="\r")
        return self.letter_distances


    def combine_distances(self):
        combined_distances = {}
        for word in self.letter_distances:
            combined_distances[word] = {}
            for pair in self.letter_distances[word]:
                if word in combined_distances[word]:
                    combined_distances[word].update({pair[1]: pair[0]})
                    continue
                combined_distances[word][pair[1]] = pair[0]
        return combined_distances

    def get_nearby_words(self, word):
        if word not in self.letter_distances:
            self.letter_distances[word] = {}
        distances = self.letter_distances[word]
        return [
            (other_word, distance, weight)
            for (other_word, distance), weight in distances.items()
        ]

    def get_next_word(self, word):
        if word not in self.letter_distances:
            self.letter_distances[word] = {}
            return random.choice(self.words)
        distances = self.letter_distances[word]
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

    def get_letter_distances(self, text, max_context=6, lookahead=12):
        self.letter_distances = {}
        for i, char in enumerate(text):
            for ctx_len in range(1, max_context + 1):
                if i < ctx_len:
                    continue
                ctx = text[i - ctx_len:i]
                window = text[i + 1:i + 1 + lookahead]
                bucket = self.letter_distances.setdefault(ctx, {})
                for d, nxt in enumerate(window):
                    bucket[(nxt, d)] = bucket.get((nxt, d), 0) + 1
        return self.letter_distances

    def score_candidates(self, context, max_distance=12, decay=0.5):
        # context: list of last k chars, most recent last
        # for each candidate c, score = sum over j of log P(c appears
        # at distance j after context[-1-j]) with decay
        last = context[-1]
        per_dist = self.sampling_cache.get(last, {})
        scores = {}
        for d, (cs, ws) in per_dist.items():
            if d >= max_distance:
                continue
            # we're looking d+1 ahead: does the char at that offset
            # match what context history suggests?
            f = decay ** d
            total = sum(ws)
            for c, w in zip(cs, ws):
                scores[c] = scores.get(c, 0.0) + f * (w / total)
        return scores

    # def generate_random_sentence(self, starting_word="the", length=16):
    #     sentence = [starting_word]
    #     word = starting_word

    #     for i in range(length):
    #         candidates = self.sampling_cache.get(word)

    #         if not candidates:
    #             break

    #         words, *weights = candidates
    #         word = random.choices(words, weights=weights, k=1)[0]
    #         sentence.append(word)
    #         # if word.endswith(",") or word == ",":
    #         #     break

    #         if word.endswith(".") or word == ".":
    #             break
    #     while not (word.endswith(".") or word == "."):
    #         word = self.get_next_word(word)
    #         sentence.append(word)

    #     return "".join(sentence)

    def generate_random_sentence(self, starting_word="T", length=200, decay=0.5, max_tail=200):
        out = list(starting_word)
        for _ in range(length):
            last_char = out[-1] if out else " "
            nxt = self.sample_next_char(last_char, decay=decay)
            if nxt is None:
                break
            out.append(nxt)
            if nxt in ".!?" and len(out) > 20:
                break
        # bounded, weighted tail instead of uniform walk
        tail = 0
        while tail < max_tail and (not out or out[-1] not in ".!?"):
            last_char = out[-1] if out else " "
            nxt = self.sample_next_char(last_char, decay=decay)
            if nxt is None:
                break
            out.append(nxt)
            tail += 1
        return "".join(out)

    # def build_sampling_cache(self):
    #     self._sampling_cache = {}

    #     for word, associations in self.letter_distances.items():
    #         candidates = [
    #             (other_word, weight)
    #             for (other_word, distance), weight in associations.items()
    #             if distance < 5
    #         ]

    #         if candidates:
    #             words, weights = zip(*candidates)
    #             self._sampling_cache[word] = (words, weights)

    def build_sampling_cache(self, max_distance=12):
        self._sampling_cache = {}
        for char, associations in self.letter_distances.items():
            by_distance = {}
            for (other, distance), weight in associations.items():
                if distance < max_distance:
                    by_distance.setdefault(distance, []).append((other, weight))
            if by_distance:
                self._sampling_cache[char] = {
                    d: (tuple(c for c, _ in pairs), tuple(w for _, w in pairs))
                    for d, pairs in by_distance.items()
                }

    def sample_next_char(self, char, decay=0.5, max_distance=12):
        per_dist = self.sampling_cache.get(char)
        if not per_dist:
            return random.choice(self.unique_words)
        chars, weights = [], []
        for d, (cs, ws) in per_dist.items():
            if d >= max_distance:
                continue
            f = decay ** d
            chars.extend(cs)
            weights.extend(w * f for w in ws)
        return random.choices(chars, weights=weights, k=1)[0]

    @property
    def unique_words(self):
        return list(self.letter_distances.keys())

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
        lg = WordGoblin("")
        lg.load(picklefile)
        lg.build_sampling_cache()
    else:
        with open(args.text_file) as f:
            text = f.read()
        lg = WordGoblin(text)
        lg.save(picklefile)
    # print(lg.letter_distances)
    # print("-"*80)
    # pprint(lg.combine_distances())
    # print("-"*80)
    # print(lg.unique_words, len(lg.unique_words))
    # print("-"*80)
    # columns = 6
    # for word in (lg.get_nearby_words("the")):
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
            print(lg.generate_random_sentence(random.choice(lg.unique_words)))
    end = timer()
    print(f"Time taken: {end - start}") # Time

    # for i in range(10):
    #     word = random.choice(lg.unique_words)
    #     print (f"{word}: {lg.get_letter_data(word)}")

def test_two():
    lg1 = LetterGoblin("the quick brown fox jumps over the lazy dog")
    lg2 = LetterGoblin("the rain in spain falls mainly on the plain")
    lg1.build_sampling_cache()
    lg2.build_sampling_cache()
    print(lg1.letter_distances["the"])
    print(lg2.letter_distances["the"])

    # how do I combine these two?
    print(lg1.letter_distances)
    for word, associations in lg2.letter_distances.items():
        if word not in lg1.letter_distances:
                lg1.letter_distances[word] = {}

        for association, weight in associations.items():
            lg1.letter_distances[word][association] = (
                lg1.letter_distances[word].get(association, 0) + weight
            )
    print(lg1.letter_distances)
    print(lg1.letter_distances["the"])

def test_three():
    start = timer()
    goblins = []
    for path in pathlib.Path.cwd().glob("text_and_pickles/*.letterpickle"):
        lg = LetterGoblin("")
        lg.load(path)
        lg.build_sampling_cache()
        print (lg.unique_words)
        print(path, len(lg.unique_words))
        goblins.append(lg)
        print("original goblin phrases")
        if len(lg.unique_words) == 0:
            continue
        for i in range(3):
            word = random.choice(lg.unique_words)
            print (f"Word: {word}:")
            for j in range(10):
                print(f"\t{lg.generate_random_sentence(word)}")

    end = timer()
    print(f"Time taken: {end - start}")

    lg = goblins[0]

    print ("Unique words before", len(lg.unique_letters))
    for g in goblins[1:]:
        for word, associations in g.letter_distances.items():

            if word not in lg.letter_distances:
                lg.letter_distances[word] = {}

            for association, weight in associations.items():
                lg.letter_distances[word][association] = (
                    lg.letter_distances[word].get(association, 0) + weight
                )

    start = timer()
    lg.build_sampling_cache()
    end = timer()
    print(f"Cache build Time taken: {end - start}")

    lg.letter_distances = dict(sorted(lg.letter_distances.items()))
    start = timer()
    print ("Unique words after", len(lg.unique_letters))
    for i in range(10):
        word = random.choice(lg.unique_letters)
        print (f"Word: {word}:")
        for j in range(3):
            print(f"\t{lg.generate_random_sentence(word, length=32)}")
    end = timer()
    print(f"Time taken: {end - start}")
    lg.save("combined.letterpickle")
    return lg

def test_four(lg:WordGoblin):
    sizes = sorted(len(words) for words, weights in lg.sampling_cache.values())

    print("Median:", sizes[len(sizes) // 2])
    print("95th percentile:", sizes[int(len(sizes) * 0.95)])
    print("Maximum:", sizes[-1])
    for word, (words, weights) in sorted(
        lg.sampling_cache.items(),
        key=lambda item: len(item[1][0]),
        reverse=True
    )[:20]:
        print(len(words), repr(word))

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("--file", type=str, help="Path to a .letterpickle file")
    parser.add_argument("text_file", nargs="?", help="The text file or path to read")
    args = parser.parse_args()

    if args.file:
        lg = LetterGoblin("")
        lg.load(args.file)
        lg.build_sampling_cache()
        letters = [l for l in lg.unique_words if l and (l[0].isupper() or l.startswith("""))]
        if not letters: letters = list(lg.unique_words)
        for i in range(3):
            word = random.choice(letters)
            print(f"\t{lg.generate_random_sentence(word, length=32)}")
    elif args.text_file:
        if args.text_file.endswith(".letterpickle"):
            lg = LetterGoblin("")
            lg.load(args.text_file)
            lg.build_sampling_cache()
        else:
            with open(args.text_file) as f:
                text = f.read()
            lg = LetterGoblin(text)
            lg.save(pathlib.Path(args.text_file).with_suffix(".letterpickle"))
            lg.build_sampling_cache()
        letters = [l for l in lg.unique_words if l and (l[0].isupper() or l.startswith("""))]
        if not letters: letters = list(lg.unique_words)
        for i in range(3):
            word = random.choice(letters)
            print(f"\t{lg.generate_random_sentence(word, length=32)}")
    else:
        print("Please provide a text file or a .letterpickle file.")