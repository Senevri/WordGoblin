from wordgoblins import WordGoblin
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    wordgoblin = WordGoblin("")
    wordgoblin.load("combined.pickle")

    buffer = []
    while True:
        new_input = input("> ")
        buffer.append(new_input)
        # wordgoblin.get_words(" ".join(buffer))
        # wordgoblin.get_word_distances(wordgoblin.words)
        #buffer.append(wordgoblin.get_next_word(buffer[-1].strip()))
        buffer.extend(wordgoblin.get_buffer_words(buffer[-3:]))
        #logger.debug(buffer)
        bufferlen = len(" ".join(buffer))
        buffer = [b for b in buffer if b.strip()]
        #print(bufferlen, bufferlen % 80)
        for i in range(1, len(new_input)-1):
            buffer.extend(wordgoblin.get_buffer_words(buffer[-3:]))
            if i >= 18:
                buffer.append("\r\n")

        if len((list(buffer))) > 18:
            buffer.append("\r\n")
        print(".\n".join((" ".join(buffer).split("."))) )









if __name__ == '__main__':
    main()