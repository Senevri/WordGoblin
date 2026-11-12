from wordgoblins import WordGoblin


def main():
    wordgoblin = WordGoblin("")
    wordgoblin.load("combined.pickle")

    buffer = []
    while True:
        new_input = input("> ")
        buffer.append(new_input)
        wordgoblin.get_words(" ".join(buffer))
        wordgoblin.get_word_distances(wordgoblin.words)
        buffer.append(wordgoblin.get_next_word(buffer[-1].strip()))
        bufferlen = len(" ".join(buffer))
        print(bufferlen, bufferlen % 80)
        for i in range(1, len(new_input)-1):
            buffer.append(wordgoblin.get_next_word(buffer[-1].strip()))
            if i == 18:
                buffer.append("\r\n")

        if len((list(buffer))) % 20 <= 2:
            buffer.append("\r\n")
        print(" ".join(buffer), )









if __name__ == '__main__':
    main()