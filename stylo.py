import os
from configparser import ConfigParser
from statistics import mean, stdev
from collections import Counter
from tqdm import tqdm

import pandas as pd
import numpy as np
import stanza, util
from sklearn.decomposition import PCA

import plotly.express as px
#______________________________________________________________________________________________

def main():

#LOAD DATA_____________________________________________________________________________________
    config_object = ConfigParser()
    config_object.read('config.ini')
    input_config = config_object["INPUT_CONFIG"] 
    output_config = config_object["OUTPUT_CONFIG"]
    feature_config = config_object["FEATURE_CONFIG"]

    if input_config['input_format'] == 'txt':  #txt file
        with open(input_config['input']) as f:
            lines = f.readlines()
            lines = [l.strip() for l in lines]
        texts = [' '.join(lines)]
        infiles = input_config['input']
    
    elif input_config['input_format'] in {'xlsx', 'csv'}: # xlsx or csv file
        if input_config['input'][-4:] == '.csv':
            df = pd.read_csv(input_config['input'])
        else:
            df = pd.read_excel(input_config['input'])
        texts = list(df[input_config['text_column']])
        infiles = list(df.index)
    
    else: # directory of txt files
        texts = []
        infiles =  os.listdir(input_config['input'])
        for fn in infiles:
            assert fn[-4:] == '.txt'

        for fn in infiles:
            with open(os.path.join(input_config['input'], fn)) as f:
                lines = f.readlines()
                lines = [l.strip() for l in lines]
                text = ' '.join(lines)
                texts.append(text)
    
    if not output_config['overwrite_output_dir']:
        assert os.path.exists(output_config['output']) == False

    df_out = pd.DataFrame()
    feature_df = pd.DataFrame()

#PREPROCESSING_________________________________________________________________________________
    try:
        nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos', verbose=0)
    except: #TO DO: find prettier way of checking whether Dutch Stanza has been downloaded already
        stanza.download('nl')
        nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos', verbose=0)
    
    for infile, text in tqdm(zip(infiles, texts)):
        doc = nlp(text)
        parsed_sentences = [[(w.text, w.upos) for w in s.words] for s in doc.sentences]
        pos_tags = [w.upos for s in doc.sentences for w in s.words]
        tokenized_sentences = [[t for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]
        tokens = [t for s in parsed_sentences for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}]
        types = set([t.lower() for t in tokens])
        syllables = [[util.get_n_syllables(t) for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]

#LENGTH STATISTICS_____________________________________________________________________________
        n_char = len(text)
        n_syllables = sum([syl for sent in syllables for syl in sent])
        n_polysyllabic = len([i for sent in syllables for i in sent if i > 1])
        n_tokens = len(tokens)
        n_longer_than_6_char = len([t for t in tokens if len(t) < 6])
        n_types = len(types)
        n_sentences = len(doc.sentences)

        avg_char_per_word = round(mean([len(t) for t in tokens]), 5)
        std_char_per_word = round(stdev([len(t) for t in tokens]), 5)

        word_length_distribution = util.get_word_length_distribution(tokens)

        avg_syl_per_word = round(mean([s for sent in syllables for s in sent]), 5)
        std_syl_per_word = round(stdev([s for sent in syllables for s in sent]), 5)

        avg_words_per_sent = round(mean([len(s) for s in tokenized_sentences]), 5)
        if n_sentences > 1:
            std_words_per_sent = round(stdev([len(s) for s in tokenized_sentences]), 5)
        else:
            std_words_per_sent = 0
        ratio_long_words = round(n_longer_than_6_char/n_tokens, 5)

        stats = {
        'n_characters': n_char,
        'n_syllables': n_syllables,
        'n_tokens': n_tokens,
        'n_polysyllabic_tokens': n_polysyllabic,
        'n_long_tokens': n_longer_than_6_char, #(> 6 char)
        'n_types': n_types,
        'n_sentences': n_sentences,
        'avg_characters_per_word': avg_char_per_word,
        'std_characters_per_word': std_char_per_word,
        'avg_syllables_per_word': avg_syl_per_word,
        'std_syllables_per_word': std_syl_per_word,
        'ratio_long_words': ratio_long_words,
        'avg_words_per_sentence': avg_words_per_sent,
        'std_words_per_sentence': std_words_per_sent,
        'word_length_distribution': word_length_distribution
        }

#LEXICAL RICHNESS______________________________________________________________________________
        if feature_config['lexical_richness']:
            ttr = util.ttr(n_types, n_tokens)
            rttr = util.rttr(n_types, n_tokens)
            cttr = util.cttr(n_types, n_tokens)
            Herdan = util.Herdan(n_types, n_tokens)
            Summer = util.Summer(n_types, n_tokens)
            if n_types == n_tokens:
                Dugast = 0
            else:
                Dugast = util.Dugast(n_types, n_tokens)
            Maas = util.Maas(n_types, n_tokens)

            lr = {
            'TTR': ttr,
            'RTTR': rttr,
            'CTTR': cttr,
            'Herdan': Herdan,
            "Summer": Summer,
            'Dugast': Dugast,
            'Maas': Maas
            }

#READABILITY___________________________________________________________________________________
        if feature_config['readability']:
            ARI = util.ARI(n_char, n_tokens, n_sentences)
            CL = util.ColemanLiau(tokens, tokenized_sentences)
            Flesch = util.Flesch(avg_words_per_sent, avg_syl_per_word)
            Fog = util.Fog(avg_words_per_sent, syllables)
            Kincaid = util.Kincaid(avg_words_per_sent, avg_syl_per_word)
            LIX = util.LIX(n_tokens, n_sentences, n_longer_than_6_char)
            RIX = util.RIX(n_longer_than_6_char, n_sentences)
            SMOG = util.SMOG(syllables)

            readability = {
            'ARI': ARI,
            'ColemanLiau': CL,
            'Flesch': Flesch,
            'FOG': Fog,
            'Kincaid': Kincaid,
            'LIX': LIX,
            'RIX': RIX,
            'SMOG': SMOG
            }

#DISTRIBUTIONS_________________________________________________________________________________
        if feature_config['distributions']:
            punct_dist = util.get_punct_dist(text)
            function_word_distribution = util.get_function_word_distribution(doc)
            pos_profile = util.get_ngram_profile(pos_tags, ngram_range=eval(feature_config['pos_ngram_range']))
            grapheme_distribution = util.get_grapheme_distribution(tokens)
            word_internal_grapheme_profile = util.get_word_internal_grapheme_profile(tokens)
            grapheme_positional_frequency = util.get_grapheme_positional_freq(tokens)
            ngram_profile = util.get_ngram_profile(tokens, ngram_range=eval(feature_config['token_ngram_range']))
            positional_word_profile = util.get_positional_word_profile(doc)
            
            dist = {
                'punctuation_distribution': punct_dist,
                'function_word_distribution': function_word_distribution,
                'pos_profile': pos_profile,
                'grapheme_distribution': grapheme_distribution,
                'word_internal_grapheme_profile': word_internal_grapheme_profile,
                'grapheme_positional_frequency': grapheme_positional_frequency,
                'ngram_profile': ngram_profile,
                'positional_word_profile': positional_word_profile
            }

#WRITE RESULTS TO OUTPUT_______________________________________________________________________
        row = dict()

        row['file_id'] = infile
        if feature_config['stats']:
            for k, v in stats.items():
                row[k] = v
        if feature_config['lexical_richness']:
            for k, v in lr.items():
                row[k] = v
        if feature_config['readability']:
            for k, v in readability.items():
                row[k] = v
        if feature_config['distributions']:
            for k, v in dist.items():
                row[k] = str(v)

        df_out = df_out.append(row, ignore_index=True)

        if feature_config['pca']: # group features slightly differently for pca
            feature_row = dict()
            feature_row['file_id'] = infile
            if feature_config['stats']:
                for k, v in stats.items():
                    if k == 'word_length_distribution':
                        for length, n in v.items():
                            feature_row[str(length)] = n
                    else:
                        feature_row[k] = v
            if feature_config['lexical_richness']:
                for k, v in lr.items():
                    feature_row[k] = v
            if feature_config['readability']:
                for k, v in readability.items():
                    feature_row[k] = v
            if feature_config['distributions']:
                for _, d in dist.items():
                    for k, v in d.items():
                        if type(v) != dict:
                            feature_row[str(k)] = str(v)
                        else: # if dictionary within dictionary
                            for key, value in v.items():
                                feature_row[key] = value
            feature_df = feature_df.append(feature_row, ignore_index=True)

    if feature_config['pca'] and len(df_out)>1:
        feature_df.fillna(0, inplace=True)
    
    columns_to_cast_to_integers = [c for c in df_out.columns if c[:2]=='n_']
    if type(infiles[0]) != str:
        columns_to_cast_to_integers.append('file_id')
    df_out = df_out.astype({k: 'int' for k in columns_to_cast_to_integers})
    df_out.to_csv(output_config['output_dir'], index=False)

#PCA___________________________________________________________________________________________
    if feature_config['pca'] and len(df_out)>2:
        feature_columns = [c for c in feature_df.columns if  c != 'file_id']
        X = feature_df[feature_columns]
        pca = PCA(n_components=2)
        components = pca.fit_transform(X)
        fig = px.scatter(components, x=0, y=1)
        fig.write_image("pca_plot.png")

#______________________________________________________________________________________________
if __name__ == "__main__":
    main() 
