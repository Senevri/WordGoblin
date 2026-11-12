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

    def get_words(self, text):
        whitespace = [" ", "\t", "\n", "\r"]
        lines = []

        for key in whitespace:
            text = text.replace(key, " ")
        words = text.split(" ")
        return words


    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.word_distances, f)

    def load(self, path):
        with open(path, "rb") as f:
            self.word_distances = pickle.load(f)
        self.words = list(self.word_distances.keys())

    def get_segment(self, word, window):
        if word not in self.word_distances:
            self.word_distances[word] = []
        self.word_distances[word].extend(list((w, idx) for idx, w in enumerate(window)))

    def get_word_data(self, word):
        return self.word_distances[word]



    def get_word_distances(self, words):
        i = 0
        max_distance = 3
        word_tasks = []
        while words:
            word = words[0]
            #idx_last = max_distance - abs(len(words)-max_distance)
            #print(idx_last)
            window = words[1:max_distance + 1]
            self.get_segment(word, window)
            words = words[1:]
            i += 1
            self.word_distances[word] = sorted(self.word_distances[word], key=lambda x: x[0])
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
        distances = sorted(self.word_distances[word], key=lambda x: x[0])
        return distances

    def generate_random_sentence(self, starting_word="the"):
        nearby_words = self.get_nearby_words(starting_word)
        # print(nearby_words)
        sentence = [starting_word]
        for i in range(16):
            words_in_irange = [word for word, distance in nearby_words if distance < 2]
            if len(words_in_irange) < 2:
                break
            word = random.choice(words_in_irange)
            sentence.append(word)
            nearby_words = self.get_nearby_words(word)
        return " ".join(sentence)



    @property
    def unique_words(self):
        return list(self.word_distances.keys())

def chunk_text(text, chunk_size):
    while text:
        index = str(text[chunk_size:]).index(". ")
        yield text[:index + chunk_size]
        text = text[index + chunk_size:]

    return


def threaded_gen(text):
    def thread_goblin(text):
        return WordGoblin(text)

    threads = []
    chunk_size = len(text) // 8
    for t in chunk_text(text, chunk_size):
        threads.append(threading.Thread(target=thread_goblin, args=(t)))

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


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="A word goblin")
    parser.add_argument("text_file", help="The text file to read")

    args = parser.parse_args()
    # Load text file

    main(args.text_file)
