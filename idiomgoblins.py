import re


class IdiomGoblin:
    def __init__(self):
        self.templates = {}
        self.idiom_patterns = {}
        self.meanings = {}
        self.compiled_patterns = {}

    def add_template(self, template_name, template):
        self.templates[template_name] = template

    def remove_template(self, template_name):
        if template_name in self.templates:
            del self.templates[template_name]

    def get_template(self, template_name):
        return self.templates.get(template_name)

    def train(self, idioms_file):
        with open(idioms_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        idiom = parts[0].strip()
                        meaning = parts[1].strip()
                        self.meanings[idiom] = meaning
                        # Store the idiom itself as a template
                        self.add_template(idiom, idiom)
                        # Pre-compile regex for the idiom
                        self.add_idiom_pattern(idiom, re.compile(re.escape(idiom), re.IGNORECASE))

    def add_idiom_pattern(self, pattern_name, pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)
        self.idiom_patterns[pattern_name] = pattern
        self.compiled_patterns[pattern_name] = pattern

    def recognize_idiom(self, text):
        for pattern_name, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                return pattern_name
        return None

    def get_meaning(self, idiom_name):
        return self.meanings.get(idiom_name)

    def preprocess_text(self, text):
        matches = []
        for pattern_name, pattern in self.compiled_patterns.items():
            match = pattern.search(text)
            if match:
                matches.append((pattern_name, match.start(), match.end()))

        if matches:
            # Select the match with the earliest start position (longest match first)
            best_match = max(matches, key=lambda x: x[2] - x[1])
            idiom_name = best_match[0]
            meaning = self.get_meaning(idiom_name)
            return {
                "idiom": idiom_name,
                "meaning": meaning,
                "processed_text": text[:best_match[1]] + f"[{idiom_name}]" + text[best_match[2]:]
            }
        return {"processed_text": text}

    def add_optional_idiom(self, base_idiom, optional_words):
        """
        Add an idiom with optional words.
        Example: base_idiom = "hit the", optional_words = ["hay", "sack"]
        This will create patterns for "hit the hay" and "hit the sack".
        """
        for word in optional_words:
            full_idiom = f"{base_idiom} {word}"
            self.add_idiom_pattern(full_idiom, full_idiom)


# Example usage
if __name__ == "__main__":
    idiom_goblin = IdiomGoblin()
    idiom_goblin.train("idioms.md")

    # Add optional idioms
    idiom_goblin.add_optional_idiom("hit the", ["hay", "sack"])

    # Test preprocessing
    test_text = "He kicked the bucket last year."
    result = idiom_goblin.preprocess_text(test_text)
    print(result)

    test_text_2 = "She hit the hay early."
    result_2 = idiom_goblin.preprocess_text(test_text_2)
    print(result_2)

    test_text_3 = "They hit the sack after the party."
    result_3 = idiom_goblin.preprocess_text(test_text_3)
    print(result_3)