# WordGoblin

WordGoblin is a library for building and using "goblin" models that capture word or letter associations from text. These models can be used to generate coherent short phrases or sentences by walking through the association graph.

## Components

### Goblins

- **WordGoblin**: A model that captures associations between words. It builds a graph where words are nodes and associations (with weights) are edges.
- **LetterGoblin**: A model that captures associations at the letter level (inherits from `WordGoblin`).

### Core Functionality

- **Devour**: A utility to "devour" text files or directories and build goblin models. It can build word-level or letter-level models and combine them into a single model.
- **Two-Word Search**: A way to generate coherent short phrases or sentences by walking the weighted association graph.

## Usage

### Building a Model

To build a word-level model from a text file:
```bash
python devour.py <text_file> --level word
```

To build a letter-level model:
```bash
python devour.py <text_file> --level letter
```

To build a combined model from a directory of text files:
```bash
python devour.py <directory> --level word
```

### Generating Phrases

You can use `twowordgoblin.py` to generate random phrases or sentences from a built model:

```bash
python twowordgoblin.py --n 10 --max_words 8
```

## File Formats

- `.pickle`: Word-level goblin model.
- `.letterpickle`: Letter-level goblin model.
