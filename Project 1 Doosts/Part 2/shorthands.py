import re
import os
from collections import Counter

def get_texts():
    texts = ''
    files = os.listdir()
    for file in files:
        text = open(file,'r',encoding='utf-8-sig').read()
        texts += text
    return texts

def extract_shorthands(text):
    f = open('freq_shorthands.txt','w',encoding='utf-8')
    shs = re.findall('[^А-яЁё]((?:[а-яё]{1,4}\. ?){1,3})(?:\n| [а-яё])',text)
    freqs = dict(Counter([x.strip() for x in shs]))
    for freq in sorted(freqs, key=freqs.get, reverse=True):
        f.write(freq+'\t'+str(freqs[freq])+'\n')
    f.close()

def extract_initials(text):
    f = open('freq_initials.txt','w',encoding='utf-8')
    initi = re.findall('[\n ]((?:[А-ЯЁ]\. ?){1,2}) ?[А-ЯЁ]',text)
    freqs = dict(Counter([x.strip() for x in initi]))
    for freq in sorted(freqs, key=freqs.get, reverse=True):
        f.write(freq+'\t'+str(freqs[freq])+'\n')
    f.close()
    

def extract_words(text):
    extract_shorthands(text)
    extract_initials(text)
        
corp = get_texts()
extract_words(corp)
