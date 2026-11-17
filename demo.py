"""Demo: SemanticGoblin extracts structured facts from natural language."""
from semantic_goblin import SemanticGoblin

TEXT = """
A bat is a mammal. Bats can fly. The red fox is known as Vulpes vulpes.
The capital of France is Paris. The car has four wheels.
Because it rained, the match was canceled. Poor diet leads to health issues.
After the war, peace was declared. The sky is blue.
The elephant is larger than the mouse. The cheetah is the fastest land animal.
If it rains, the ground gets wet. This book belongs to the library.
"""

sg = SemanticGoblin(TEXT)
facts = sg.extract()

print("=" * 70)
print("SEMANTIC GOBLIN — Extracted Facts")
print("=" * 70)

for f in facts:
    print(f"  [{f.pattern:12s}] {f.subject:20s} --{f.predicate:15s}> {f.object}")

print("=" * 70)
print(f"Total facts extracted: {len(facts)}")
print("=" * 70)

# Group by pattern
patterns = {}
for f in facts:
    patterns.setdefault(f.pattern, []).append(f)

print("\nBy pattern type:")
for pat, items in sorted(patterns.items()):
    print(f"  {pat}: {len(items)} fact(s)")
