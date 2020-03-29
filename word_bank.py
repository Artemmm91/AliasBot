def translate(file):
    f = open(file, 'r', encoding='utf8')
    array = f.read().splitlines()
    return array


words_easy = translate('Library/easy.txt')
words_medium = translate('Library/middle.txt')
words_hard = translate('Library/difficult.txt')
words = translate('Library/all.txt')
