import re
import string
from nltk.metrics.distance import edit_distance

def read_corpus(filename):
    text = open(filename,'r',encoding='utf-8-sig').read()
    return text

def read_lists(sep,not_sep,sh):
    with open(sep,'r',encoding='utf-8-sig') as f:
        separate = {x.strip() for x in f.readlines()}
    with open(not_sep,'r',encoding='utf-8-sig') as f:
        not_separate = {x.strip() for x in f.readlines()}
    with open(sh,'r',encoding='utf-8-sig') as f:
        shorthands = {x.strip() for x in f.readlines()}
    return separate,not_separate,shorthands

def whitespace(text):
    tokens = [x.strip() for x in re.split('[ _\n]',text)]
    return tokens

def detect_smile(token):
    eyes = re.search('[;:=]',token)
    if eyes:
        if token.endswith(eyes.group()):
            if token.startswith('C') or \
               (token.startswith('(') and ')' not in token) or \
               token.startswith(')'):
                return True
            else:
                return False
        elif token.startswith(eyes.group()):
            return True
        else:
            return False
    if token.endswith('((') or token.endswith('))'):
        return True
    if token == ')' or token == '(':
        return True
    return False

def detect_currency(token):
    currencies = '₳฿￠₡¢₢₵₫€￡£₤₣ƒ₲₭Ł₥₦₽₱＄$₮ℳ₶₩￦¥￥₴₸¤₰៛₪₯₠₧﷼円元圓㍐원৳₹₨৲௹'
    if re.search('[A-zА-яЁё]',token) is None and \
       re.search('[0-9,.]+',token) is not None and \
       re.search('['+currencies+']',token) is not None:
        return True

def strip_punc(tokens):
    without_punc = [x.strip(string.punctuation+'—–…“”«»') \
                    if x.strip(string.punctuation+'—–…“”«»') and not detect_smile(x) \
                    and not detect_currency(x) else x for x in tokens]
    without_punc = [x for x in without_punc if x.strip(string.punctuation+'—–…“”«»') or detect_smile(x)]
    new_without_punc = []
    separate_smiles = re.compile('(\\w+)([()]+)')
    for i in without_punc:
        if separate_smiles.search(i):
            new_without_punc += separate_smiles.split(i)
        else:
            new_without_punc.append(i)
    new_without_punc = [x for x in new_without_punc if x]
    return new_without_punc

def spacing(text):
    spaces = re.findall('[^\\w]((?:\\w ){3,}\\w)[ '+string.punctuation+'—–…“”«»'+']',text)
    for elem in spaces:
        text = text.replace(elem,elem.replace(' ',''))
    return text

def separate_word(tokens):
    #смайлики
    punc = re.compile('[,!?"()]')
    new_tokens = []
    for token in tokens:
        if punc.findall(token) and re.search('[A-zА-яЁё]',token) is not None and \
           re.search('[0-9]',token) is None:
            new_tokens += [x.strip(string.punctuation+'—–…“”«»') for x in punc.split(token)]
        elif '/' in token and re.search('[0-9]',token) is None:
            new_tokens += [x.strip(string.punctuation+'—–…“”«»') for x in token.split('/')]
        else:
            new_tokens.append(token)
    return new_tokens
                
def hyphens(tokens,not_separate,to_separate):
    new_tokens = []
    for token in tokens:
        if '-' in token:
            in_separate = [(token.replace(x,''),x[1:]) for x in to_separate if token.lower().endswith(x)]
            if not in_separate:
                in_separate = [(x[:-1],token.replace(x,'')) for x in to_separate if token.lower().startswith(x)]
            in_not_separate = sum([edit_distance(x,token.lower()) <= 2 for x in not_separate])
            if in_separate and not in_not_separate:
                new_tokens += [x for x in in_separate[0]]
            elif not in_not_separate:
                suff_len = sum([len(x) > 2 for x in token.split('-')])
                nums = any([re.search('[0-9]',x) for x in token.split('-')])
                if suff_len == len(token.split('-')) and not nums:
                    new_tokens += token.split('-')
                else:
                    new_tokens.append(token)
            else:
                new_tokens.append(token)       
        else:
            new_tokens.append(token)
    return new_tokens

def tokenizer(sentences,borders,not_separate,separate,output,mode):
    token_file = open(output,mode,encoding='utf-8')
    token_file.write('ID\tStart\tEnd\tText\n')
    separate,not_separate,sokr = read_lists('separate.txt','not_to_separate.txt','sokr.txt')
    for i,s in enumerate(sentences):
        new_text = spacing(s)
        tokens = separate_word(strip_punc(whitespace(new_text)))
        tokens = hyphens(tokens,not_separate,separate)
        s_start = borders[i][0]
        #print([s],borders[i],tokens)
        t_borders = find_borders(s,tokens)
        t_borders = [(x[0] + s_start,x[1] + s_start) for x in t_borders]
        for j in range(len(tokens)):
            token_file.write(str(i)+'-'+str(j)+'\t'+str(t_borders[j][0])+'\t'+str(t_borders[j][1])+'\t'+tokens[j]+'\n')
    token_file.close()
    return tokens,t_borders

def create_reg_list(str_list):
    reg = '(?:'+'|'.join([re.escape(x) for x in str_list])+'| [A-ZА-ЯЁ]\.)'
    return reg

def split_into_sent(text,sh):
    text = re.sub('([!?…]+["»”)]?)','\\1<<splitter>>',text) #excl and quest
    text = re.sub('([»”)]+)( *[\nA-ZА-ЯЁ(“«])','\\1<<splitter>>\\2',text) #quotes
    text = re.sub('"((?:[ \n]+?[A-ZА-ЯЁ(“«"]|\n *?[—–-]))','"<<splitter>>\\1',text) #more quotes
    text = re.sub('(?<![:,])(\n+(?:[A-ZА-ЯЁ(“«"]| *?[—–-]))','<<splitter>>\\1',text) #newline
    text = re.sub('([^:;\-]\([^)]+<<splitter>>)','<<splitter>>\\1',text) #opening bracket
    text = re.sub('((?:\({2,}|\){2,}))','\\1<<splitter>>',text) #brackets as a smile
    text = re.sub('(\.+["»”)]?)([ A-ZА-ЯЁ])','\\1<<splitter>>\\2',text) #dot
    new_sh = [x.replace(' ','<<splitter>> ') for x in sh if ' ' in x] #problems with dot
    for s in new_sh:
        text = text.replace(s,s.replace('<<splitter>>',''))
    sh_reg = create_reg_list(sh) #shortcuts
    text = re.sub('( '+sh_reg+')<<splitter>>(?= +[^A-ZА-ЯЁ])','\\1',text)
    text = re.sub('( [A-ZА-ЯЁ]\.)<<splitter>>( ?[A-ZА-ЯЁ]\.)<<splitter>>( *[A-ZА-ЯЁ])','\\1\\2\\3',text) #two names
    text = re.sub('( [A-ZА-ЯЁ]\.)<<splitter>>( *[A-ZА-ЯЁ])','\\1\\2',text) #one name
    sentences = re.split('<<splitter>>',text)
    return sentences


def find_borders(text,sentences):
    borders = []
    for sentence in sentences:
        #print([sentence])
        first = re.search('((^.*?)'+re.escape(sentence)+')',text,flags=re.DOTALL)
        if first is None: #бывает в случае схлопнутых токенов
            sentence = ' '.join(sentence)
            first = re.search('((^.*?)'+re.escape(sentence)+')',text,flags=re.DOTALL)
        if borders:
            start = len(first.group(2)) + borders[-1][-1]
        else:
            start = len(first.group(2))
        end = start + len(sentence)
        borders.append((start,end))
        text = text[len(first.group(1)):]
        #print(sentence,borders[-1])
    return borders
    
def splitter(text,sh,output,mode):
    split = open(output,mode,encoding='utf-8')
    split.write('ID\tStart\tEnd\tText\n')
    sentences = split_into_sent(text,sh)
    borders = find_borders(text,sentences)
    new_borders = []
    new_sentences = []
    idx = 0
    for i in range(len(sentences)):
        sentence_clean = re.sub('[\n ]+',' ',sentences[i]).strip()
        sentence = sentence_clean.strip(string.punctuation+'—–…“”«»'+'*xXхХ ').strip()
        if sentence or detect_smile(sentence_clean):
            new_sentences.append(sentences[i])
            new_borders.append(borders[i])
            split.write(str(idx)+'\t'+str(borders[i][0])+'\t'+str(borders[i][1])+'\t'+sentence_clean+'\n')
            idx += 1
    split.close()
    return new_sentences,new_borders


def analyze(text,separate,not_separate,sokr):
    sent,bor = splitter(s,sokr,'output_split.txt','w')
    tokens,t_bor = tokenizer(sent,bor,not_separate,separate,'output_tokens.txt','w')
    return sent,bor,tokens,t_bor


def tests(separate,not_separate,sokr):
    for i in range(1,7):
        with open('test'+str(i)+'.txt','r',encoding='utf-8') as f:
            text = f.read()
            f1 = open('test'+str(i)+'_output.txt','w',encoding='utf-8')
            f1.write(text+'\n\n\n')
            f1.close()
            sent,bor = splitter(text,sokr,'test'+str(i)+'_output.txt','a')
            f1 = open('test'+str(i)+'_output.txt','a',encoding='utf-8')
            f1.write('\n\n\n')
            f1.close()
            tokenizer(sent,bor,not_separate,separate,'test'+str(i)+'_output.txt','a')
    
separate,not_separate,sokr = read_lists('separate.txt','not_to_separate.txt','sokr.txt')
#s = ' So, B. R. Obama decides to organise an actual race. He says to Trump and Hillary:"The one, who will run around White House and be the fastest will win election."Hillary running first. Obama fires in air and she goes. After around 20 minutes she finishes her run sweating and almost dying. Obama nodes, and tell Trump to get ready.Barack fires again. Trump litterally shoots from start, his wig flies of his head. Time passes, and he comes back, sweat and autotan dripping from him. Obama looks at the time: 13 minutes."HELL YEAH, I WIN! Suck it Hillary, you stupid bitch!" - Trump says."Yeah, yeah, my congratulations, Donald" - Obama answer him with grim face."Damn, whoa... I was fast! Didn\'t I set some kind of record?" - asks Trump. Obama answers: "No. Bush did 9:11."' 
s = open('clear_anek_corporas.txt','r',encoding='utf-8').read()
#s = open('words.txt','r',encoding='utf-8').read()
analyze(s,separate,not_separate,sokr)

tests(separate,not_separate,sokr)
