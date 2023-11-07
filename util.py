from math import log, sqrt, floor
from collections import Counter
from statistics import mean
from string import punctuation
import operator, zipfile, os
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd

def load_data(input_format, input_dir, text_column=None, delimiter=None):

	"""
	Load the dataset.
	Arguments:
		input_format: input format specified in the config file (csv or zip),
		input_dir: input directory specified in the config file,
		text_column: if input_format==csv, column name containing texts,
		delimiter: if input_format==csv, delimiter for reading the csv file.
	Returns:
		df: dataframe of the corpus,
		texts: list of strings,
		infiles: doc indices
	"""

	if input_format == 'zip': # zip folder with txt
		df = pd.DataFrame(columns=['filename', 'text'])
		with zipfile.ZipFile(input_dir, 'r') as zip_file:
			for file_info in zip_file.infolist():
				if file_info.filename.endswith('.txt'):
					filename = os.path.basename(file_info.filename)
					with zip_file.open(file_info) as txt_file:
						text = txt_file.read().decode('utf-8')  # Assuming UTF-8 encoding
					df = df.append({'filename': filename, 'text': text}, ignore_index=True)
		df = df.sort_values('filename')
		texts = list(df.text)
		infiles = list(df.filename)
	
	elif input_format == 'csv': 
		df = pd.read_csv(input_dir, delimiter=delimiter)
		texts = list(df[text_column])
		infiles = list(df.index)
	
	else: # directory of txt files
		raise ValueError("Input type must be 'csv' or 'zip'.")

	return texts, infiles
	
#BASELINE_SYLLABIFIER________________________________________________________________
def get_n_syllables(word):

	"""
	Baseline rule-based syllabification.
	Arguments:
		word: str
	Returns:
		n syllables: int
	"""
	vowels = ['a', 'e', 'i', 'o', 'u', 'y']
	cnt=0
	for i, char in enumerate(word):
		previous_char = '-' if i==0 else word[i-1]
		if char in vowels and previous_char not in vowels:
			cnt+=1
	return cnt


#STATISTICS__________________________________________________________________________
def contains_negation(tokenized_sentence, negators={'niet', 'niets', 'geen', 'nooit', 'niemand', 'nergens', 'noch'}):
    for n in negators:
        if n in set(t.lower() for t in tokenized_sentence):
            return True
    return False

def ratio_content_words(doc):
    content = [t.text for s in doc.sents for t in s if t.pos_ in {'ADJ', 'ADV', 'NOUN', 'VERB', 'PROPN'}]
    funct = [t.text for s in doc.sents for t in s if t.pos_ not in {'ADP', 'AUX', 'CCONJ', 'DET', 'NUM', 'PART', 'PRON', 'SCONJ'}]
    return len(content)/(len(content)+len(funct))

def get_passive_ratio(doc, matcher):

	total = 0
	passive = 0

	for s in doc.sents:
		total += 1
		matches = matcher(s)
		if matches:
			passive += 1
	return round(passive/total, 3)

#LEXICAL_RICHNESS_SCORES_____________________________________________________________
"""
Various functions for computing lexical richness scores
"""

def ttr(n_types,n_tokens):
	return round(n_types/n_tokens, 3)

def rttr(n_types,n_tokens):
	return round(n_types/sqrt(n_tokens), 3)

def cttr(n_types,n_tokens):
	return round(n_types/sqrt(2*n_tokens), 3) 

def Herdan(n_types,n_tokens):
	return round(log(n_types)/log(n_tokens), 3)

def Summer(n_types,n_tokens):
	return round(log(log(n_types))/log(log(n_tokens)), 3)

def Dugast(n_types,n_tokens):
	return round((log(n_tokens)**2)/(log(n_tokens)-log(n_types)), 3)

def Maas(n_types,n_tokens):
	return round((log(n_tokens)-log(n_types))/(log(n_tokens)**2), 3) 

#READABILITY SCORES__________________________________________________________________
"""
Various functions for computing readability scores
"""

def ARI(n_char, n_tokens, n_sentences):
	return round(4.71*(n_char/n_tokens)+0.5*(n_tokens/n_sentences)-21.43, 3)

def ColemanLiau(tokens, tokenized_sentences):
	if len(tokens) < 100:
		return 0
	chunks = [tokens[i:i+100] for i in range(0, len(tokens), 100) if i+100<=len(tokens)]
	L = mean([len(''.join(chunk)) for chunk in chunks]) # avg. n char per 100 tokens
	S = len(tokenized_sentences)/len(tokens)*100 # avg. n sent per 100 tokens
	return round(0.0588*L-0.296*S-15.8, 3)

def Flesch(ASL, ASW):
	return round(206.835-(1.015*ASL)-(84.6*ASW), 3)

def Fog(ASL, syllables):
	syllables = [s for sent in syllables for s in sent]
	if len(syllables) < 100:
		return 0
	PHW = len([s for s in syllables if s >= 3])/len(syllables) # percentage hard words
	return round(0.4*(ASL + PHW), 3)

def Kincaid(ASL, ASW):
	return round((0.39*ASL)+(11.8*ASW)-15.59, 3)

def LIX(n_tokens, n_sentences, n_long_tokens):
	return round((n_tokens/n_sentences)+(n_long_tokens*100/n_tokens), 3)

def RIX(n_long_tokens, n_sentences):
	return round(n_long_tokens/n_sentences, 3)

def SMOG(sample):
	length = len(sample)
	if length < 30:
		return 0
	else:
		i = floor(length/3)
		sample = sample[:10] + sample[i:i+10] + sample[-10:]
		sample = [s for sent in sample for s in sent]
	n_polysyllabic = len([s for s in sample if s > 2])
	return round(3+sqrt(n_polysyllabic), 3)

#DISTRIBUTIONS_______________________________________________________________________
def get_word_length_distribution(tokens):
	"""
	Compute word length distribution
	Arguments:
		tokens: lst
	Returns:
		{token_length: rel_freq}
	"""
	lengths = [len(t) for t in tokens]
	dist = dict(Counter(lengths))
	dist = {k:round(v/len(tokens), 3) for k,v in dist.items()}
	dist = {int(k): [v] for k,v in dist.items()}
	return dist

def get_dependency_distribution(dependencies):
	"""
	Compute dependency distribution
	Arguments:
		dependencies: lst
	Returns:
		{dependency: rel_freq}
	"""
	dist = dict(Counter(dependencies))
	dist = {k:round(v/len(dependencies), 3) for k,v in dist.items()}
	dist = {k: [v] for k,v in dist.items()}
	return dist

def get_grapheme_distribution(tokens):
	"""
	Compute grapheme distribution
	Arguments:
		tokens: lst
	Returns:
		{grapheme: rel_freq}
	"""
	graphemes = ''.join(tokens)
	n_total = len(graphemes)
	dist = dict(Counter(graphemes))
	for k,v in dist.items():
		dist[k] = round(v/n_total, 3)
	dist = dict(sorted(dist.items(), key=operator.itemgetter(1),reverse=True))
	return dist

def get_word_internal_grapheme_profile(tokens):
	"""
	Compute word-interal grapheme distribution
	Arguments:
		tokens: lst
	Returns:
		{grapheme: % of wors that contain grapheme}
	"""
	graphemes = set(''.join(tokens))
	n_tokens = len(tokens)
	profile = {}

	for g in graphemes:
		for t in tokens:
			if g in t:
				if g in profile.keys():
					profile[g+'_word_internal'] += 1
				else:
					profile[g+'_word_internal'] = 1
	
	profile = {k:round(v/n_tokens, 3) for k,v in profile.items()}
	profile = dict(sorted(profile.items(), key=operator.itemgetter(1),reverse=True))
	return profile

def get_function_word_distribution(doc):
	"""
	Compute function word distribution
	Arguments:
		doc: Stanza doc object
	Returns:
		{function word: rel_freq}
	"""
	allowed_pos = {'ADP', 'AUX', 'CCONJ', 'DET', 'PART', 'PRON', 'SCONJ'}
	function_words = [w.text.lower() for s in doc.sents for w in s if w.pos_ in allowed_pos]
	n_function_words = len(function_words)
	dist = dict(Counter(function_words))
	dist = {k:round(v/n_function_words, 3) for k,v in dist.items()}
	dist = {k: [v] for k,v in dist.items()}
	dist = dict(sorted(dist.items(), key=operator.itemgetter(1),reverse=True))
	return dist

def get_grapheme_positional_freq(tokens):
	"""
	Compute positional frequency of graphemes
	Arguments:
		tokens: lst
	Returns:
		{pos_idx_in_token: {char: rel_freq}
	"""
	n_tokens = len(tokens)
	lengths = [len(t) for t in tokens]
	longest = sorted(lengths)[-1]
	profile={}
	
	for i in range(1, longest+1):
		grapheme_freq = {}
		for t in tokens:
			if len(t) >= i:
				if t[i-1] in grapheme_freq.keys():
					grapheme_freq[t[i-1]] += 1
				else:
					grapheme_freq[t[i-1]] = 1

		grapheme_freq = {k:round(v/n_tokens, 3) for k,v in grapheme_freq.items()}
		grapheme_freq = {f'char_idx_{i}_{k}':v for k,v in grapheme_freq.items()}
		grapheme_freq = dict(sorted(grapheme_freq.items(), key=operator.itemgetter(1),reverse=True))
		profile['char_idx_'+str(i)] = grapheme_freq

	return profile

def get_punct_dist(text):
	"""
	Compute punctuation distribution
	Arguments:
		tokens: lst
	Returns:
		{punct: relative frequency by n characters}
	"""
	dist = {}
	for p in punctuation:
		dist[p] = text.count(p)	

	n_char = len(text.replace(' ', ''))

	dist_by_char = {k: [round(v/n_char, 3)] for k,v in dist.items()}
	dist_by_char = dict(sorted(dist_by_char.items(), key=operator.itemgetter(1),reverse=True))
	return dist_by_char

def get_positional_word_profile(doc):
	"""
	Compute positional word profile
	Arguments:
		doc: stanza doc object
	Returns:
		{token idx in sentence: {word: relative freq}}
	"""
	tokens = [[w.text.lower() for w in s] for s in doc.sents]
	n_positions = max([len(s) for s in tokens])
	profile = {}

	for i in range(n_positions):
		k = i
		words = [s[k] for s in tokens if len(s)>k]
		n_sentences = len(words)
		v = dict(Counter(words))
		v = {k:v/n_sentences for k,v in v.items()}
		v = {f'token_idx_{str(i)}_{k}':v for k,v in v.items()}
		v = dict(sorted(v.items(), key=operator.itemgetter(1),reverse=True))
		profile['token_idx_'+str(k)] = v

	return profile

def get_ngram_profile(tokens, ngram_range):
	"""
	Compute ngram distribution
	Arguments:
		tokens: lst
		ngram_range: (min, max)
	Returns:
		{ngram: freq}
	"""

	tokens = [[t.lower() for t in tokens]]
	vec = CountVectorizer(ngram_range=ngram_range, analyzer=lambda x:x)
	X = vec.fit_transform(tokens)
	document_lengths = X.sum(axis=1)
	X_normalized = X / document_lengths
	profile = dict()
	for v,k in zip(X_normalized.toarray().flatten(), vec.get_feature_names()):
		profile[k] = [v]
	return profile
