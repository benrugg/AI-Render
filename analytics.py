def count_words(text):
    # convert punctuation to spaces
    for char in '-.,\n':
        text=text.replace(char, ' ')

    # split words by spaces and count
    return len(text.split())

def get_first_words(text, num_words):
    words = text.split()
    return ' '.join(words[:num_words])
