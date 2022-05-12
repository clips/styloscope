import os, argparse

from statistics import mean, stdev
from collections import Counter
from tqdm import tqdm

import pandas as pd
import numpy as np
import stanza, util
from sklearn.decomposition import PCA

import plotly.express as px
#______________________________________________________________________________________________

def main(args):

#LOAD DATA_____________________________________________________________________________________
    input_format = args.input_format

    if input_format == 'txt': # 1 .txt file
        with open(args.input) as f:
            lines = f.readlines()
            lines = [l.strip() for l in lines]
        texts = [' '.join(lines)]
        infiles = [args.input]
    
    elif input_format in {'xlsx', 'csv'}: # 1 csv/excel file
        if args.input[-4:] == '.csv':
            df = pd.read_csv(args.input)
        else:
            df = pd.read_excel(args.input)
        texts = list(df[args.text_column])
        infiles = list(df.index)
    
    else: # directory with txt files
        texts = []
        infiles =  os.listdir(args.input)
        for fn in infiles:
            assert fn[-4:] == '.txt'

        for fn in infiles:
            with open(os.path.join(args.input, fn)) as f:
                lines = f.readlines()
                lines = [l.strip() for l in lines]
                text = ' '.join(lines)
                texts.append(text)
    
    if args.overwrite_output_dir != 't':
        assert os.path.exists(output_dir) == False

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
        if args.lexical_richness == 'y':
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
        if args.readability == 'y':
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
        if args.distributions == 'y':
            punct_dist = util.get_punct_dist(text)
            function_word_distribution = util.get_function_word_distribution(doc)
            pos_distribution = util.get_pos_distribution(parsed_sentences)
            pos_bigram_distribution = util.get_pos_distribution(parsed_sentences, ngram_range=2)
            
            dist = {
                'punctuation_distribution': punct_dist,
                'function_word_distribution': function_word_distribution,
                'pos_distribution': pos_distribution,
                'pos_bigram_distribution': pos_bigram_distribution
            }

#WRITE RESULTS TO OUTPUT_______________________________________________________________________
        row = dict()

        row['file_id'] = infile
        if args.statistics == 'y':
            for k, v in stats.items():
                row[k] = v
        if args.lexical_richness == 'y':
            for k, v in lr.items():
                row[k] = v
        if args.readability == 'y':
            for k, v in readability.items():
                row[k] = v
        if args.distributions == 'y':
            for k, v in dist.items():
                row[k] = str(v)

        df_out = df_out.append(row, ignore_index=True)

        if args.pca=='y': # group features slightly differently for pca
            feature_row = dict()
            feature_row['file_id'] = infile
            if args.statistics == 'y':
                for k, v in stats.items():
                    if k == 'word_length_distribution':
                        for length, n in v.items():
                            feature_row[str(length)] = n
                    else:
                        feature_row[k] = v
            if args.lexical_richness == 'y':
                for k, v in lr.items():
                    feature_row[k] = v
            if args.readability == 'y':
                for k, v in readability.items():
                    feature_row[k] = v
            if args.distributions == 'y':
                for _, d in dist.items():
                    for k, v in d.items():
                        feature_row[str(k)] = str(v)
            feature_df = feature_df.append(feature_row, ignore_index=True)

    if args.pca == 'y' and len(df_out)>1:
        feature_df.fillna(0, inplace=True)
        columns_to_cast_to_integers = [c for c in feature_df.columns if c[:2]=='n_']
        if type(infiles[0]) != str:
            columns_to_cast_to_integers.append('file_id')
        feature_df = feature_df.astype({k: 'int' for k in columns_to_cast_to_integers})
        feature_df.to_csv('feature_df.csv', index=False)
    
    columns_to_cast_to_integers = [c for c in df_out.columns if c[:2]=='n_']
    if type(infiles[0]) != str:
        columns_to_cast_to_integers.append('file_id')
    df_out = df_out.astype({k: 'int' for k in columns_to_cast_to_integers})
    df_out.to_csv(f'{args.output}', index=False)

#PCA___________________________________________________________________________________________
    if args.pca == 'y' and len(df_out)>2:
        feature_columns = [c for c in feature_df.columns if c[:2]!= 'n_' and c!='file_id']
        X = feature_df[feature_columns]
        pca = PCA(n_components=2)
        components = pca.fit_transform(X)
        fig = px.scatter(components, x=0, y=1)
        fig.write_image("pca_plot.png")

#______________________________________________________________________________________________
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=None, type=str, help='director to input file or path (it is recommended to use this pipeline on texts > 100 tokens)')
    parser.add_argument('--input_format', default=None, type=str, choices=['csv', 'xlsx', 'txt', 'folder_with_txt'], help='type of input data')
    parser.add_argument('--output', default='output.csv', type=str, help='path to output, default=output.csv')
    parser.add_argument('--overwrite_output_dir', default='t', type=str, choices=['y', 'n'], help='overwrite output file (y/n)')
    parser.add_argument('--statistics', default='y', type=str, choices=['y', 'n'], help="compute length features (y/n)")
    parser.add_argument('--distributions', default='y', type=str, choices=['y', 'n'], help="compute (PoS, punctuation, function word) distributions (y/n)")
    parser.add_argument('--lexical_richness', default='y', type=str, choices=['y', 'n'], help='compute lexical richness scores (y/n)')
    parser.add_argument('--readability', default='y', type=str, choices=['y', 'n'], help='compute readability scores (y/n)')
    parser.add_argument('--pca', default='y', type=str, choices=['y', 'n'], help='perform PCA (y/n)')
    parser.add_argument('--text_column', default='text', type=str, help='column that contains text input (only relevant if --input_format == "csv" or "xlsx")') 
    args = parser.parse_args()
    main(args)
