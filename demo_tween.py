#!/usr/bin/env python
"""Demo: LetterGoblin word tweening."""
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
if SOURCE_DIR not in sys.path:
    sys.path.append(str(SOURCE_DIR))

from lettergoblins import LetterGoblin

# Shakespeare corpus for rich letter patterns
text = """To be, or not to be, that is the question: Whether 'tis nobler in the mind to suffer
The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles
And by opposing end them. To die—to sleep, No more; and by a sleep to say we end
The heart-ache and the thousand natural shocks That flesh is heir to: 'tis a consummation
Devoutly to be wish'd. To die, to sleep; To sleep, perchance to dream—ay, there's the rub:
For in that sleep of death what dreams may come, When we have shuffled off this mortal coil,
Must give us pause—there's the respect That makes calamity of so long life.
For who would bear the whips and scorns of time, Th'oppressor's wrong, the proud man's contumely,
The pangs of despised love, the law's delay, The insolence of office, and the spurns
That patient merit of th'unworthy takes, When he himself might his quietus make
With a bare bodkin? Who would fardels bear, To grunt and groan under a weary life,
But that the dread of something after death, The undiscovere'd country, from whose bourn
No traveller returns, puzzles the brain, And makes us rather bear those ills we have
Than fly to others that we know not of? Thus conscience does make cowards of us all,
And thus the native hue of resolution Is sicklied o'er with the pale cast of thought,
And enterprises of great pith and moment With this regard their currents turn awry
And lose the name of action. All the world's a stage, and all the men and women merely players.
They have their exits and their entrances, And one man in his time plays many parts.
The quality of mercy is not strained, It droppeth as the gentle rain from heaven
Upon the place beneath. It is twice blest: It blesseth him that gives and him that takes.
More especially of mercy. It is an attribute to God himself, And earthly power doth then
Show likest God's when mercy seasons justice. Therefore, though we are in our children's vein
By course of construction, yet, look you, sir, our small kinship shall not be so proud
As to displease you, parting father. How do you? I am very well, thank you.
The weather is fine today. We should go for a walk in the park. The quick brown fox
jumps over the lazy dog. The dog barked at the fox. The fox ran away quickly.
The dog chased the fox through the park. The quick brown fox is very fast.
The lazy dog is very slow. The fox and the dog are friends now. They play together
in the park every day. The cat sat on the mat. The cat meowed at the dog.
The dog barked at the cat. The fox watched them play. The bird flew away.
The brown cat sat on the mat. The quick dog ran past. The lazy fox slept.
The dog barked at the cat. The fox watched them play. The bird flew away."""

lg = LetterGoblin(text)
lg.build_sampling_cache()

print("=" * 60)
print("LetterGoblin Word Tweening Demo")
print("=" * 60)
print()

# Demo 1: Basic tweening
print("1. Basic Word Tweening (n_gram=2, temp=2.0, replace_prob=0.5)")
print("-" * 60)
test_words = ['cat', 'dog', 'fox', 'quick', 'brown', 'lazy', 'park', 'tree', 'mercy', 'justice', 'world', 'stage']
for word in test_words:
    variants = lg.tween_word(word, n_gram=2, num_variants=5, replace_prob=0.5, temperature=2.0)
    print(f"  {word:10} -> {variants}")

print()

# Demo 2: Temperature effects
print("2. Temperature Effects (word='quick')")
print("-" * 60)
for temp in [1.0, 2.0, 3.0, 5.0]:
    variants = lg.tween_word('quick', n_gram=2, num_variants=5, replace_prob=0.5, temperature=temp)
    print(f"  temp={temp:4.1f} -> {variants}")

print()

# Demo 3: Replace probability effects
print("3. Replace Probability Effects (word='brown')")
print("-" * 60)
for prob in [0.2, 0.5, 0.8]:
    variants = lg.tween_word('brown', n_gram=2, num_variants=5, replace_prob=prob, temperature=2.0)
    print(f"  prob={prob:.1f} -> {variants}")

print()

# Demo 4: N-gram effects
print("4. N-gram Effects (word='justice')")
print("-" * 60)
for n in [1, 2, 3]:
    variants = lg.tween_word('justice', n_gram=n, num_variants=5, replace_prob=0.5, temperature=2.0)
    print(f"  n_gram={n} -> {variants}")

print()
print("=" * 60)
print("Demo complete!")
print("=" * 60)
