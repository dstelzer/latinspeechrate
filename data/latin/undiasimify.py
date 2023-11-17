import re
from random import choice

from trie import Trie

STRESS = r'[ˈˌ]' # 02C8 02CC
# Generated by taking fullSymbolDiacriticDefs.txt and getting the hex(ord) of each character above 255
DIACRITIC = r'[\u02b0\u02b2\u02e0\u02b7\u1da3\u02e4\u02e1\u0303\u0308\u030d\u030a\u0325\u032c\u032a\u032f\u0329\u0330\u0324\u0339\u02d0]'
# A single alphabetic character, or two alphabetic characters joined by 0361 (tie bar)
IPACHAR = r'\w(?:\u0361\w)?' # The ?: makes this a non-capturing group, important for re.findall
# An alphabetic character plus any number of diacritics after it
PHONEME = fr'({STRESS}?{IPACHAR}{DIACRITIC}*)'

# Taken from symbolDefs.csv: these are all the ones that are +syl -cons
VOWEL = r'[əɜiyɪʏeøɛœæᴂaɶɨʉɘɵɞᴀɯuωʊɤoʌɔɑɒɐ]'
# These are all the ones that are +lat or appear rhotic in the author's view
LIQUID = r'[ɾrɹɬɮlɫɺʎʟʁʀ]'
# And these are all the ones that are -cont (except ʀ̆ which is not a stop)
STOP = r'[pbtdcɟkɡgqɢʔ]'
WAW = r'w'
VELAR = r'[kɡg]'

# 0329, 030d = syllabic
# 032f = not syllabic
SYLLABIC = r'[\u0329\u030d]'
NONSYLLABIC = r'\u032f'

def has(phon, pattern):
	return bool(re.search(pattern, phon))

def is_vowel(phon):
	return has(phon, SYLLABIC) or (has(phon, VOWEL) and not has(phon, NONSYLLABIC))
def is_liquid(phon):
	return has(phon, LIQUID) and not has(phon, SYLLABIC)
def is_stop(phon):
	return has(phon, STOP)
def is_waw(phon):
	return has(phon, WAW)
def is_velar(phon):
	return has(phon, VELAR)

class FrenchWord:
	def __init__(self, ipa, kw_correction=False, stress=True):
		self.ipa = ipa
		self.phonemify(stress)
		self.syllabify(kw_correction)
	
	def phonemify(self, stress=True): # Split continuous IPA into a list of phonemes (i.e. characters with diacritics attached)
		ipa = self.ipa if stress else re.sub(STRESS, '', self.ipa)
		self.phonemes = re.findall(PHONEME, ipa)
		if sum(len(p) for p in self.phonemes) != len(ipa):
			raise ValueError('Something got lost', ipa, ' '.join(self.phonemes))
	#	print(self.phonemes)
	
	def syllabify(self, kw_correction=False): # Split list of phonemes into list of syllables
		self.syllables = [[]] # (Where a syllable is a list of phonemes)
		initial = True
		
		for phon in self.phonemes:
			# First, give each vowel its own syllable, and put everything in the coda
			if is_vowel(phon):
				if initial: # (Exception: everything before the *first* vowel must be in the onset, so the first vowel does *not* make a new syllable)
					self.syllables[-1].append(phon)
					initial = False
					continue
				
				# But if it's not the first vowel we've seen, make a new syllable!
				newsyll = [phon]
				# Now, check if there's a consonant right before this. If so, stick it into the onset.
				if not is_vowel(self.syllables[-1][-1]):
					newsyll.insert(0, self.syllables[-1].pop()) # Remove it from the previous syllable and insert it at the start of this one
					# Now check for the special case of stop + liquid which is the only cluster we're allowing in onsets (I think?)
					if is_liquid(newsyll[0]) and is_stop(self.syllables[-1][-1]):
						newsyll.insert(0, self.syllables[-1].pop()) # Repeat the popping!
					elif kw_correction and is_waw(newsyll[0]) and is_velar(self.syllables[-1][-1]): # If we set the kw_correction flag, we also want kw and gw to remain together instead of being split across syllable boundaries
						newsyll.insert(0, self.syllables[-1].pop())
				self.syllables.append(newsyll) # Stick it into our list of syllables and start building a coda!
			else:
				self.syllables[-1].append(phon)
	#	print(self.syllables)
	
	def output(self, sep='-', phonsep=''):
		return sep.join(phonsep.join(p for p in s) for s in self.syllables)

# Orthography module

V = VOWEL[:-1] + r'\u0303]' # Add tilde to this
C = '[^' + VOWEL[1:] # Everything except vowels
BOUNDARY = '#'
LABIAL = '[pb]'
FRONT = '[ɜiyɪʏeøɛœæᴂaɶ]'
BACK = '[ɨʉɘɵɞᴀɯuωʊɤoʌɔɑɒɐ]'
ORTHOSTRIP = r'\u032a' # bridge is the only diacritic that appears in French

def doubled_consonant(cons, prev, post): # choose b, bb, or be based on context
	if has(post, BOUNDARY): return cons+'e'
	elif has(prev, VOWEL) and has(post, V): return cons*2 # Specifically not including nasalized consonants in the prev here!
	return cons

def gfunc(prev, post): # Too big for a lambda to be clear
	if has(post, BOUNDARY): return 'gue'
	elif has(post, FRONT): return 'gu'
	elif has(prev, V) and has(post, V): return 'gg'
	return 'g'

def kfunc(prev, post):
	if has(post, BOUNDARY):
		if has(prev, C): return 'que' # TODO this probably shouldn't happen
		else: return 'q'
	elif has(prev, V) and has(post, BACK): return 'cc'
	elif has(post, V): return 'qu'
	else: return 'c'

def øfunc(prev, post):
	if has(post, BOUNDARY): return 'eux'
	elif has(prev, BOUNDARY): return 'eu'
	else: return 'eû'

def œnfunc(prev, post):
	if has(post, BOUNDARY): return 'eun'
	elif has(post, LABIAL): return 'um'
	else: return 'un'

def sfunc(prev, post):
	if has(prev, BOUNDARY): return 's'
	elif has(prev, V) and has(post, V): return 'ss'
	elif has(post, C): return 's'
	elif has(post, FRONT): return 'c'
	else: return 'ç'

def zfunc(prev, post):
	if has(post, BOUNDARY):
		if has(prev, V): return 'se'
		else: return 'ze'
	elif has(prev, V) and has(post, V): return 's'
	else: return 'z'

def ʒfunc(prev, post):
	if has(post, BOUNDARY): return 'ge'
	elif has(post, FRONT): return choice(['g', 'j'])
	else: return choice(['ge', 'j'])

FRENCH_ORTHO = Trie({
	'#': (lambda prev, post: 'h' if has(post, V) else ''),
	'a': 'a',
	'aɛ': 'aë',
	'aɛ̃': 'aïn',
	'ai': 'aï',
#	'am': 'am',
#	'aɔ': 'ao',
	'au': 'aou',
	'ɑ': 'â',
	'ɑ̃': (lambda prev, post: 'am' if has(post, LABIAL) else 'an'),
	'b': (lambda prev, post: doubled_consonant('b', prev, post)),
	'd': (lambda prev, post: doubled_consonant('d', prev, post)),
	'e': (lambda prev, post: 'er' if has(post, BOUNDARY) else 'é'),
	'ə': 'e',
	'ɛ': (lambda prev, post: 'ay' if has(post, BOUNDARY) else choice(['ai', 'è'])),
	'ɛ̃': (lambda prev, post: choice(['aim', 'im']) if has(post, BOUNDARY) or has(post, LABIAL) else choice(['ain', 'in'])),
#	'ɛi': (lambda prev, post: 'aye' if has(post, BOUNDARY) else '???'),
	'ɛj': 'ay',
	'f': (lambda prev, post: 'ff' if has(prev, V) and has(post, V) else 'f'),
	'ɡ': gfunc,
	'i': (lambda prev, post: 'ie' if has(post, BOUNDARY) else 'i'), # y?
	'j': (lambda prev, post: 'ï' if has(prev, BOUNDARY) else 'i'), # y?
	'jɛ': 'ie',
	'jɛ̃': (lambda prev, post: 'iem' if has(post, LABIAL) else 'ien'),
	'k': kfunc,
	'ks': (lambda prev, post: 'cc' if has(prev, V) and has(post, FRONT) else 'x'),
	'kt': 'ct',
	'l': (lambda prev, post: doubled_consonant('l', prev, post)),
	'm': (lambda prev, post: doubled_consonant('m', prev, post)),
	'n': (lambda prev, post: doubled_consonant('n', prev, post)),
	'ɲ': 'gn',
	'o': (lambda prev, post: 'ot' if has(post, BOUNDARY) else 'au'),
	'oʁ': 'or', # Bleeds the previous one
	'oz': (lambda prev, post: 'ose' if has(post, BOUNDARY) else 'os'),
	'ø': øfunc,
	'œ': (lambda prev, post: 'œu' if has(post, C) else 'œ'),
	'œ̃': œnfunc,
	'ɔ': 'o',
	'ɔ̃': (lambda prev, post: 'om' if has(post, BOUNDARY) or has(post, LABIAL) else 'on'),
	'ɔɛ': 'oë',
	'ɔɛ̃': 'oën',
	'ɔi': 'oï',
	'ɔʁ': 'aur',
	'p': (lambda prev, post: doubled_consonant('p', prev, post)),
	'ʁ': (lambda prev, post: 're' if has(post, BOUNDARY) else 'r'),
	's': sfunc,
#	'sj': 'ti',
#	'stj': 'sti',
	'ʃ': 'ch',
	't': (lambda prev, post: doubled_consonant('t', prev, post)),
#	'tj': (lambda prev, post: 'ti' if has(prev, BOUNDARY) else 'ty'),
	'u': (lambda prev, post: 'oue' if has(post, BOUNDARY) else 'ou'),
	'ɥ': 'u',
#	'ɥɛ': 'ue',
	'ɥij': 'uy',
	'v': (lambda prev, post: 've' if has(post, BOUNDARY) else 'v'),
	'w': 'ou',
	'wa': 'oi',
	'wɛ̃': 'oin',
	'y': (lambda prev, post: 'ue' if has(post, BOUNDARY) else 'u'),
	'z': zfunc,
	'ʒ': ʒfunc,
})

def orthographize(word):
	word = re.sub(ORTHOSTRIP, '', word)
	word = f'#{word}#' # So we can use # as word boundary marker
	whole = word
	prev = ''
	while word:
		token, eaten = FRENCH_ORTHO.findlongest(word)
		if not eaten: # Didn't find anything
			raise ValueError(whole, word[:5])
		post = word[eaten] if eaten<len(word) else ''
		if not isinstance(token, str): token = token(prev, post)
		yield token
		prev = word[eaten-1]
		word = word[eaten:]

if __name__ == '__main__':
	while True:
		print(FrenchWord(input()).output())
	#	print(''.join(orthographize(input())))
# Test case from FLLex: ˌɑd̪fˌɑkt̪ˈɑːre ˌɑd̪fˌɑxt̪ˈɑrɛ ˌaðfˌajt̪ʲˈie̯r ˌafˌɛt̪ʲjˈer ˌafˌɛt̪ˈer afɛt̪e
