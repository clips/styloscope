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
		texts: list of strings,
		infiles: doc indices
	"""

	if input_format == 'zip': # zip folder with txt
		filenames = []
		texts = []

		with zipfile.ZipFile(input_dir, 'r') as zip_file:
			for file_info in zip_file.infolist():
				if file_info.filename.endswith('.txt'):
					filename = os.path.basename(file_info.filename)
					with zip_file.open(file_info) as txt_file:
						text = txt_file.read().decode('utf-8')  # Assuming UTF-8 encoding
						texts.append(text)
						filenames.append(filename)

		df = pd.DataFrame(data={'filename': filenames, 'text': texts})
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
def get_n_syllables(word, dic):

	"""
	Syllabification based on Pyphen library.
	Arguments:
		word: str
	Returns:
		n_syllables: int
	"""  
	result = dic.inserted(word).split('-')
	return len(result)

#STATISTICS__________________________________________________________________________
def contains_negation(tokenized_sentence, negators={'niet', 'niets', 'geen', 'nooit', 'niemand', 'nergens', 'noch'}):
	"""
	Detects negation in a sentence
	Arguments
		tokenized_sentence: list of tokens
		negators: lexicon indicating negation
	Returns
		Bool
	"""
	for n in negators:
		if n in set(t.lower() for t in tokenized_sentence):
			return True
	return False

def ratio_content_words(doc):
	"""
	Computes ratio of content words (PUNCT, SYM, and X are excluded in this computation)
	Arguments:
		doc: Spacy doc object
	Returns
		Ratio of content words
	"""
	content = [t.text for s in doc.sents for t in s if t.pos_ in {'ADJ', 'ADV', 'NOUN', 'VERB', 'PROPN'}]
	funct = [t.text for s in doc.sents for t in s if t.pos_ not in {'ADP', 'AUX', 'CCONJ', 'DET', 'NUM', 'PART', 'PRON', 'SCONJ'}]
	try:
		return len(content)/(len(content)+len(funct))
	except (ValueError, ZeroDivisionError):
		return 0

def get_passive_ratio(doc, matcher):

	"""
	Computes ratio of sentences that contain a passive verb construction.
	Arguments:
		doc: Spacy doc object
		matcher: Spacy matcher object
	Returns:
		Ratio of passive sentencs
	"""

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

def sttr(tokens):

	"""
	Computes standardized type-token ratio (per 100 tokens).
	Input:
		tokens: list of tokens
	Returns:
		STTR score
	"""

	if len(tokens) < 100:
		return None

	ttr_scores = []

	for segment in tokens[::100]:
		n_types = len(set(segment))
		n_tokens = len(segment)
		ttr_scores.append(ttr(n_types, n_tokens))
	
	return round(mean(ttr_scores), 3)

def rttr(n_types,n_tokens):
	return round(n_types/sqrt(n_tokens), 3)

def cttr(n_types,n_tokens):
	return round(n_types/sqrt(2*n_tokens), 3) 

def Herdan(n_types,n_tokens):
	try:
		return round(log(n_types)/log(n_tokens), 3)
	except (ValueError, ZeroDivisionError):
		return None

def Summer(n_types,n_tokens):
	try:
		return round(log(log(n_types))/log(log(n_tokens)), 3)
	except (ValueError, ZeroDivisionError):
		return None

def Dugast(n_types,n_tokens):
	try:
		return round((log(n_tokens)**2)/(log(n_tokens)-log(n_types)), 3)
	except (ValueError, ZeroDivisionError):
		return None

def Maas(n_types,n_tokens):
	try:
		return round((log(n_tokens)-log(n_types))/(log(n_tokens)**2), 3) 
	except (ValueError, ZeroDivisionError):
		return None

#READABILITY SCORES__________________________________________________________________
"""
Various functions for computing readability scores
"""

def ARI(n_char, n_tokens, n_sentences):
	return round(4.71*(n_char/n_tokens)+0.5*(n_tokens/n_sentences)-21.43, 3)

def ColemanLiau(tokens, tokenized_sentences):
	if len(tokens) < 100:
		return None
	chunks = [tokens[i:i+100] for i in range(0, len(tokens), 100) if i+100<=len(tokens)]
	L = mean([len(''.join(chunk)) for chunk in chunks]) # avg. n char per 100 tokens
	S = len(tokenized_sentences)/len(tokens)*100 # avg. n sent per 100 tokens
	return round(0.0588*L-0.296*S-15.8, 3)

def Flesch(ASL, ASW):
	return round(206.835-(1.015*ASL)-(84.6*ASW), 3)

def Fog(ASL, syllables):
	syllables = [s for sent in syllables for s in sent]
	if len(syllables) < 100:
		return None
	PHW = len([s for s in syllables if s >= 3])/len(syllables) # percentage hard words, i.e. at least three syllables
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
		return None
	else:
		i = floor(length/3)
		sample = sample[:10] + sample[i:i+10] + sample[-10:] # select first 10 sentences, last 10 sentences, and 10 sentences in the middle
		sample = [s for sent in sample for s in sent]
	n_polysyllabic = len([s for s in sample if s > 2]) # check if more than 2 syllables
	return round(sqrt(n_polysyllabic) + 3, 3)

def interpret_readability(score, name):

	"""
	Converts readability score to interpretable results.
	Arguments:
		score: float
		name: readability metric name
	Returns:
		string (or None if score is None)
	"""

	if not score:
		return None
	
	elif name == 'Flesch reading ease':
		if score >= 90:
			return "USA 5th Grade"
		elif score >= 80:
			return "USA 6th Grade"
		elif score >= 70:
			return "USA 7th Grade"
		elif score >= 60:
			return "USA 8th-9th Grade"
		elif score >= 50:
			return "USA 10th-12th Grade"
		elif score >= 30:
			return "USA College Student"
		elif score >= 10:
			return "USA College Graduate"
		else:
			return "Professional"
		
	if name in {'ARI', 'Flesch-Kincaid Grade Level', 'Coleman-Liau', 'Gunning Fog', 'SMOG'}:
		if score < 1:
			return "USA Kindergarten"
		elif score < 2:
			return "USA 1st Grade"
		elif score < 3:
			return "USA 2nd Grade"
		elif score < 4:
			return "USA 3rd Grade"
		elif score < 5:
			return "USA 4th Grade"
		elif score < 6:
			return "USA 5th Grade"
		elif score < 7:
			return "USA 6th Grade"
		elif score < 8:
			return "USA 7th Grade"
		elif score < 9:
			return "USA 8th Grade"
		elif score < 10:
			return "USA 9th Grade"
		elif score < 11:
			return "USA 10th Grade"
		elif score < 12:
			return "USA 11th Grade"
		elif score < 13:
			return "USA 12th Grade"
		elif score < 14:
			return "USA College Freshman"
		elif score < 15:
			return "USA College Sophomore"
		elif score < 16:
			return "USA College Junior"
		elif score < 17:
			return "USA College Senior"
		else:
			return "USA College Graduate"
		
	elif name == 'LIX':
		if score < 30:
			return "Very easy"
		elif score < 40:
			return "Easy"
		elif score < 50:
			return "Medium"
		elif score < 60:
			return "Difficult"
		else:
			return "Very difficult"
	
	elif name == 'RIX':
		if score < 0.2:
			return "USA 1st Grade"
		elif score < 0.5:
			return "USA 2nd Grade"
		elif score < 0.8:
			return "USA 3rd Grade"
		elif score < 1.3:
			return "USA 4th Grade"
		elif score < 1.8:
			return "USA 5th Grade"
		elif score < 2.4:
			return "USA 6th Grade"
		elif score < 3.0:
			return "USA 7th Grade"
		elif score < 3.7:
			return "USA 8th Grade"
		elif score < 4.5:
			return "USA 9th Grade"
		elif score < 5.3:
			return "USA 10th Grade"
		elif score < 6.2:
			return "USA 11th Grade"
		elif score < 7.2:
			return "USA 12th Grade"
		else:
			return "USA College Level"

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
	dist = {k:v/len(tokens) for k,v in sorted(dist.items(), key=lambda x: x[0])}
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
	dist = {k:v/len(dependencies) for k,v in dist.items()}
	dist = {k: [v] for k,v in dist.items()}
	return dist

# def get_grapheme_distribution(tokens):
# 	"""
# 	Compute grapheme distribution
# 	Arguments:
# 		tokens: lst
# 	Returns:
# 		{grapheme: rel_freq}
# 	"""
# 	graphemes = ''.join(tokens)
# 	n_total = len(graphemes)
# 	dist = dict(Counter(graphemes))
# 	for k,v in dist.items():
# 		dist[k] = v/n_total
# 	dist = dict(sorted(dist.items(), key=operator.itemgetter(1),reverse=True))
# 	return dist

# def get_word_internal_grapheme_profile(tokens):
# 	"""
# 	Compute word-interal grapheme distribution
# 	Arguments:
# 		tokens: lst
# 	Returns:
# 		{grapheme: % of wors that contain grapheme}
# 	"""
# 	graphemes = set(''.join(tokens))
# 	n_tokens = len(tokens)
# 	profile = {}

# 	for g in graphemes:
# 		for t in tokens:
# 			if g in t:
# 				if g in profile.keys():
# 					profile[g+'_word_internal'] += 1
# 				else:
# 					profile[g+'_word_internal'] = 1
	
# 	profile = {k:v/n_tokens for k,v in profile.items()}
# 	profile = dict(sorted(profile.items(), key=operator.itemgetter(1),reverse=True))
# 	return profile

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
	dist = {k:v/n_function_words for k,v in dist.items()}
	dist = {k: [v] for k,v in dist.items()}
	dist = dict(sorted(dist.items(), key=operator.itemgetter(1),reverse=True))
	return dist

# def get_grapheme_positional_freq(tokens):
# 	"""
# 	Compute positional frequency of graphemes
# 	Arguments:
# 		tokens: lst
# 	Returns:
# 		{pos_idx_in_token: {char: rel_freq}
# 	"""
# 	n_tokens = len(tokens)
# 	lengths = [len(t) for t in tokens]
# 	longest = sorted(lengths)[-1]
# 	profile={}
	
# 	for i in range(1, longest+1):
# 		grapheme_freq = {}
# 		for t in tokens:
# 			if len(t) >= i:
# 				if t[i-1] in grapheme_freq.keys():
# 					grapheme_freq[t[i-1]] += 1
# 				else:
# 					grapheme_freq[t[i-1]] = 1

# 		grapheme_freq = {k:v/n_tokens for k,v in grapheme_freq.items()}
# 		grapheme_freq = {f'char_idx_{i}_{k}':v for k,v in grapheme_freq.items()}
# 		grapheme_freq = dict(sorted(grapheme_freq.items(), key=operator.itemgetter(1),reverse=True))
# 		profile['char_idx_'+str(i)] = grapheme_freq

# 	return profile

def get_punct_dist(text):
	"""
	Compute punctuation distribution
	Arguments:
		tokens: lst
	Returns:
		{punct: relative frequency by n characters}
	"""
	dist = {}
	n_punct = 0
	for p in punctuation:
		n = text.count(p)
		dist[p] = n	
		n_punct += n
	
	if not n_punct:
		return None

	dist_by_char = {k: [v/n_punct] for k,v in dist.items()}
	dist_by_char = dict(sorted(dist_by_char.items(), key=operator.itemgetter(1),reverse=True))
	return dist_by_char

# def get_positional_word_profile(doc):
# 	"""
# 	Compute positional word profile
# 	Arguments:
# 		doc: stanza doc object
# 	Returns:
# 		{token idx in sentence: {word: relative freq}}
# 	"""
# 	tokens = [[w.text.lower() for w in s] for s in doc.sents]
# 	n_positions = max([len(s) for s in tokens])
# 	profile = {}

# 	for i in range(n_positions):
# 		k = i
# 		words = [s[k] for s in tokens if len(s)>k]
# 		n_sentences = len(words)
# 		v = dict(Counter(words))
# 		v = {k:v/n_sentences for k,v in v.items()}
# 		v = {f'token_idx_{str(i)}_{k}':v for k,v in v.items()}
# 		v = dict(sorted(v.items(), key=operator.itemgetter(1),reverse=True))
# 		profile['token_idx_'+str(k)] = v

# 	return profile

def get_ngram_profile(tokens):
	"""
	Compute ngram distribution
	Arguments:
		tokens: lst
		ngram_range: (min, max)
	Returns:
		{ngram: freq}
	"""

	tokens = [[t.lower() for t in tokens]]
	vec = CountVectorizer(analyzer=lambda x:x)
	X = vec.fit_transform(tokens)
	document_lengths = X.sum(axis=1)
	X_normalized = X / document_lengths
	profile = dict()
	for v,k in zip(X_normalized.toarray().flatten(), vec.get_feature_names_out()):
		profile[k] = [v]
	return profile
