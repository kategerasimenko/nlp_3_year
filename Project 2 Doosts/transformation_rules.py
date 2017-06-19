tag = input()
els = list(tag)

changes = {
    '3': '3p',
    's': 'sg',
    'p': 'pl',
    'n': 'nom',
    'g': 'gen',
    'd': 'dat',
    'a': 'acc',
    'l': 'loc',
    'i': 'ins'
}

if len(els) == 6 and els[0] == 'P' and els[2] == '3':
    els[3],els[4],els[5] = els[5],els[3],els[4]
    skipped = [x for x in els if x != '-']
    new_tag = 'SPRO\t'+','.join([changes[x] if x in changes else x
                                 for x in skipped][1:])

elif tag == 'R':
    new_tag = 'ADV'

else:
    new_tag = ''

print('New tag (for 3-person pronouns and adverbs only):\n'+new_tag)
