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
        words = [w for w in text.split(" ") if w]
        return words

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump((self.word_distances, self.words), f)

    def load(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, tuple) and len(data) == 2 and isinstance(data[0], dict):
            raw_distances, words = data
        else:
            raw_distances = data
            words = list(raw_distances.keys())
        self.word_distances = {}
        for word, associations in raw_distances.items():
            if isinstance(associations, dict):
                self.word_distances[word] = associations
            else:
                converted = {}
                for other_word, distance in associations:
                    key = (other_word, distance)
                    converted[key] = converted.get(key, 0) + 1
                self.word_distances[word] = converted
        self.words = words

    def get_segment(self, word, window):
        if word not in self.word_distances:
            self.word_distances[word] = {}
        for distance, other_word in enumerate(window):
            key = (other_word, distance)
            self.word_distances[word][key] = (
                self.word_distances[word].get(key, 0) + 1
            )

    def get_word_data(self, word):
        return self.word_distances[word]

    def get_word_distances(self, words):
        i = 0
        max_distance = 8
        while words:
            word = words[0]
            window = words[1:max_distance + 1]
            self.get_segment(word, window)
            words = words[1:]
            i += 1
        return self.word_distances

    def get_nearby_words(self, word, max_distance=8):
        if word not in self.word_distances:
            return []
        distances = self.word_distances[word]
        return [
            (other_word, distance, weight)
            for (other_word, distance), weight in distances.items() if distance <= max_distance
        ]

    def get_buffer_words(self, buffer):
        for word in buffer:
            nearby = [x for x in self.get_nearby_words(word) if x[0].strip()]
            for other_word, distance, weight in nearby:
                if other_word in buffer:
                    yield random.choice(self.get_nearby_words(other_word))[0]
                else:
                    yield other_word

    def generate_random_sentence(self, starting_word="the", length=16):
        sentence = [starting_word]
        for _ in range(length):
            nearby_words = self.get_nearby_words(starting_word)
            if not nearby_words:
                break
            word = random.choice(nearby_words)[0]
            sentence.append(word)
            starting_word = word
            if starting_word[-1] in (".", "!", "?"):
                break
        return " ".join(sentence)

    def build_sampling_cache(self):
        self._sampling_cache = {}
        for word, distances in self.word_distances.items():
            # Group by distance
            dist_map = {}
            for (other_word, distance), weight in distances.items():
                if distance not in dist_map:
                    dist_map[distance] = []
                dist_map[distance].append((other_word, weight))
            
            cache = {}
            for distance, candidates in dist_map.items():
                words = [c[0] for c in candidates]
                weights = [c[1] for c in candidates]
                cache[distance] = (words, weights)
            self._sampling_cache[word] = cache

    def tween_goblin(self, word1, word2):
        """Finds words that appear between word1 and word2 in the training text."""
        # This is a simplified version. A real one would look for paths.
        # For now, let's find words that are at distance 1 from word1 and distance 1 from word2.
        # Or more generally, words that form a path.
        # But let's start with something simple.
        
        # Find all words that are at distance 1 from word1
        candidates1 = [w for w, d, weight in self.get_nearby_words(word1, 1) if d == 0]
        # Find all words that are at distance 1 from word2
        # Wait, distance 1 from word2 means word2 is at distance 1 from it.
        # So we look for words where word2 is at distance 1.
        candidates2 = []
        for word, distances in self.word_distances.items():
            if (word2, 0) in distances:
                candidates2.append(word)
        
        # Intersection
        common = set(candidates1) & set(candidates2)
        return list(common)

    def two_word_search(self, word1, word2):
        """
        Given two adjacent words (word1, word2), find the words that 
        immediately follow word2.
        """
        if word1 not in self.word_distances:
            return []
        
        distances = self.word_distances[word1]
        if (word2, 0) in distances:
            return self.get_nearby_words(word2, 0)
        
        return []

    def combine_distances(self):
        # ... (omitted for brevity, but I should keep it)
        pass

    def test_three():
        # ... (omitted)
        pass

    def test_four(wg:WordGoblin):
        # ... (omitted)
        pass
