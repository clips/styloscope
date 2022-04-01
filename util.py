from math import log, sqrt, floor
from statistics import mean

#BASELINE_SYLLABIFIER________________________________________________________________
def get_n_syllables(word):
    vowels = ['a', 'e', 'i', 'o', 'u', 'y']
    cnt=0
    for i, char in enumerate(word):
        previous_char = '-' if i==0 else word[i-1]
        if char in vowels and previous_char not in vowels:
            cnt+=1
    return cnt

#LEXICAL_RICHNESS_SCORES_____________________________________________________________
def ttr(n_types,n_tokens):
	return n_types/n_tokens

def rttr(n_types,n_tokens):
	return n_types/sqrt(n_tokens)

def cttr(n_types,n_tokens):
	return n_types/sqrt(2*n_tokens) 

def Herdan(n_types,n_tokens):
	return log(n_types)/log(n_tokens)

def Summer(n_types,n_tokens):
	return log(log(n_types))/log(log(n_tokens))

def Dugast(n_types,n_tokens):
	return (log(n_tokens)**2)/(log(n_tokens)-log(n_types))

def Maas(n_types,n_tokens):
	return (log(n_tokens)-log(n_types))/(log(n_tokens)**2) 

#READABILITY SCORES__________________________________________________________________
def ARI(n_char, n_tokens, n_sentences):
	return 4.71*(n_char/n_tokens) + 0.5*(n_tokens/n_sentences) - 21.43

def ColemanLiau(tokens, tokenized_sentences):
	if len(tokens) < 100:
		return None
	chunks = [tokens[i:i+100] for i in range(0, len(tokens), 100) if i+100<=len(tokens)]
	L = mean([len(''.join(chunk)) for chunk in chunks]) # avg. n char per 100 tokens
	S = len(tokenized_sentences)/len(tokens)*100 # avg. n sent per 100 tokens
	return 0.0588*L - 0.296*S - 15.8

def Flesch(ASL, ASW):
	return 206.835 - (1.015*ASL) - (84.6*ASW)

def Fog(ASL, syllables):
	syllables = [s for sent in syllables for s in sent]
	if len(syllables) < 100:
		return None
	PHW = len([s for s in syllables if s >= 3])/len(syllables) # percentage hard words
	return 0.4*(ASL + PHW)

def Kincaid(ASL, ASW):
	return (0.39*ASL) + (11.8*ASW) - 15.59

def LIX(n_tokens, n_sentences, n_long_tokens):
	return (n_tokens/n_sentences) + (n_long_tokens*100/n_tokens)

def RIX(n_long_tokens, n_sentences):
	return n_long_tokens/n_sentences

def SMOG(sample):
	length = len(sample)
	if length < 30:
		return None
	else:
		i = floor(length/3)
		sample = sample[:10] + sample[i:i+10] + sample[-10:]
		sample = [s for sent in sample for s in sent]
	n_polysyllabic = len([s for s in sample if s > 2])
	return 3 + sqrt(n_polysyllabic)