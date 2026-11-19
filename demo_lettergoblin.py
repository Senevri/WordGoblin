#!/usr/bin/env python
"""Demo: LetterGoblin - letter-level n-gram model with tweening."""
import sys
import pickle
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
if SOURCE_DIR not in sys.path:
    sys.path.append(str(SOURCE_DIR))

from lettergoblins import LetterGoblin

def demo(text, pickle_path, n_gram=2, length=30, num_variants=5, temperature=2.0, r_prob=0.5):
    lg = LetterGoblin(text, defer_load=True)
    if pickle_path:
        lg.load(pickle_path)
    else:
        lg._get_letter_distances(lg.text)
    lg.build_sampling_cache()

    print('=' * 60)
    print('LetterGoblin Demo')
    print('=' * 60)
    print()

    print(f'1. Letter Chain Model (text) (n_gram={n_gram})')
    print('-' * 60)
    chain = lg.get_source_n_letter_chain(min(len(text)-1,n_gram))
    print(f'Unique letters: {len(lg.unique_letters)}')
    print('Sample contexts:')
    for ctx in list(chain.keys())[:5]:
        candidates = chain[ctx]
        top = sorted(candidates.items(), key=lambda x: -x[1])[:n_gram]
        print(f'  {ctx!r} -> {top}')

    print()
    print(f'1.1 Letter Chain Model (distances) (n_gram={n_gram})')
    print('-' * 60)
    chain = lg.get_associated_n_letter_chain(text[:n_gram],n_gram)
    #print(chain)
    print(f'Unique letters: {len(lg.unique_letters)}')
    print('Sample contexts:')
    for ctx in list(chain.keys())[:5]:
        candidates = chain[ctx]
        title = candidates[0] #sorted(candidates, key=lambda x: x)[:n_gram]
        top = candidates[1][:n_gram]
        print(f'  {title!r} -> {top}')


    print()
    print('2. Random Sentence Generation')
    print('-' * 60)
    for _ in range(3):
        print(">>>")
        sentence = lg.generate_random_sentence('T', length=length, n_gram=n_gram)
        print(f'  {sentence}')
        print('  ---  ')
        sentence = lg.generate_random_sentence('T', length=length, n_gram=n_gram, mode="distances")
        print(f'  {sentence}')


    print()
    print('2.1 Test ngram values')
    print('-' * 60)
    for ngram in range(12):
        sentence = lg.generate_random_sentence('T', length=length, n_gram=ngram)
        print(f'[{ngram}]:  {sentence}\n')
        sentence = lg.generate_random_sentence('T', length=length, n_gram=n_gram, mode="distances")
        print(f'[{ngram}]:  {sentence}\n\n')
        print("-" * 60)



    print()
    print(f"The following tests only show variants with differences. Generating {num_variants} variants per word.")
    print('3. Word Tweening (letter replacement)')
    print('-' * 60)
    test_words = ['cat', 'dog', 'fox', 'quick', 'brown', 'lazy', 'park', 'tree', 'mercy', 'justice', 'world', 'stage']
    for word in test_words:
        variants = set(lg.tween_word(word, n_gram=n_gram, num_variants=num_variants, replace_prob=r_prob, temperature=temperature))
        print(f'  {word:10} -> {variants}')

    print()
    print('3.1. Sentence Tweening (letter replacement)')
    print('-' * 60)
    sentence = "the quick brown fox jumps over the lazy dog"
    variants = set(lg.tween_word(sentence, n_gram=n_gram, num_variants=num_variants, replace_prob=r_prob, temperature=temperature))
    print(f'  {sentence} -> {variants}')

    print()
    print('4. Temperature Effects (word=quick)')
    print('-' * 60)
    for temp in [1.0, 2.0, 3.0, 5.0, 10.0]:
        variants = set(lg.tween_word('quick', n_gram=n_gram, num_variants=num_variants, replace_prob=r_prob, temperature=temp))
        print(f'  temp={temp:4.1f} -> {variants}')

    print()
    print('5. Replace Probability Effects (word=brown)')
    print('-' * 60)
    for prob in [0.2, 0.5, 0.8, 1.0]:
        variants = set(lg.tween_word('brown', n_gram=n_gram, num_variants=num_variants, replace_prob=prob, temperature=temperature))
        print(f'  prob={prob:.1f} -> {variants}')

    print()
    print('6. N-gram Effects (word=justice)')
    print('-' * 60)
    for n in range(n_gram + 1):
        variants = set(lg.tween_word('justice', n_gram=n, num_variants=num_variants, replace_prob=r_prob, temperature=temperature))
        print(f'  n_gram={n} -> {variants}')

    print()
    print('=' * 60)
    print('Demo complete!')
    print('=' * 60)


default_text = """To be, or not to be, that is the question: Whether tis nobler in the mind to suffer
The slings and arrows of outrageous fortune, Or to take arms against a sea of troubles
And by opposing end them. To die to sleep, No more; and by a sleep to say we end
The heart ache and the thousand natural shocks That flesh is heir to: tis a consummation
Devoutly to be wished. To die, to sleep; To sleep, perchance to dream, there is the rub:
For in that sleep of death what dreams may come, When we have shuffled off this mortal coil,
Must give us pause, there is the respect That makes calamity of so long life.
For who would bear the whips and scorns of time, The oppressor wrong, the proud man contumely,
The pangs of despised love, the law delay, The insolence of office, and the spurns
That patient merit of the unworthy takes, When he himself might his quietus make
With a bare bodkin? Who would fardels bear, To grunt and groan under a weary life,
But that the dread of something after death, The undiscovered country, from whose bourn
No traveller returns, puzzles the brain, And makes us rather bear those ills we have
Than fly to others that we know not of? Thus conscience does make cowards of us all,
And thus the native hue of resolution Is sicklied oer with the pale cast of thought,
And enterprises of great pith and moment With this regard their currents turn awry
And lose the name of action. All the world is a stage, and all the men and women merely players.
They have their exits and their entrances, And one man in his time plays many parts.
The quality of mercy is not strained, It droppeth as the gentle rain from heaven
Upon the place beneath. It is twice blest: It blesseth him that gives and him that takes.
More especially of mercy. It is an attribute to God himself, And earthly power doth then
Show likest Gods when mercy seasons justice. Therefore, though we are in our childrens vein
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


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Demo: LetterGoblin - letter-level n-gram model with tweening.")
    parser.add_argument("text", default=default_text, nargs="?", help="Text file or path to read. '-' for stdin.")
    parser.add_argument("--pickle", help="The pickle file or path to read.")
    parser.add_argument("--n_gram", type=int, default=2, help="N-gram length.")
    parser.add_argument("--num_variants", type=int, default=10, help="Number of variants to generate.")
    parser.add_argument("--temperature", type=float, default=2.0, help="Temperature for sampling.")
    parser.add_argument("--length", type=int, default=100, help="Number of words to generate.")
    parser.add_argument("--replace_prob", type=float, default=0.5, help="Probability of replacing a letter.")

    args = parser.parse_args()

    if args.text == "-":
        import sys
        args.text = sys.stdin.read()
    else:
        path = Path(args.text)
        if path.exists() and path.is_file():
            args.text = path.read_text()

    demo(args.text, args.pickle or None, args.n_gram, args.length, args.num_variants, args.temperature)
