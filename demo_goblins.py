import patterngoblin
import semantic_goblin

from pprint import pprint

# Load the source text
with open('prose_hifi/nnfa.md', 'r') as file:
    source_text = file.read()

# Process the text with patterngoblin
goblin = patterngoblin.PatternGoblin()
goblin.feed(source_text)
pattern_results = goblin.get_templates()

# Process the text with semantic_goblin
semantic_goblin_instance = semantic_goblin.SemanticGoblin(source_text)
semantic_results = semantic_goblin_instance.extract()

# Print the results
print("Pattern Goblin Results:")
pprint(pattern_results)
for result in pattern_results:
    # format result
    print(f"{result[0]} - {result[1]} - {result[2]}")

print("\nSemantic Goblin Results:")
for result in semantic_results:
    # format result
    print(f"{result.subject} - {result.predicate} - {result.object}")