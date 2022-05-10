import pandas as pd
import util
import argparse
import os
import stanza
from statistics import mean, stdev
from collections import Counter

#_______________________________________________________________

def main(args):

#LOAD DATA_____________________________________________________________________________________
    if args.input[-4:] == '.txt': # 1 .txt file
        with open(args.input) as f:
            lines = f.readlines()
            lines = [l.strip() for l in lines]
        texts = [' '.join(lines)]
        infiles = [args.input]
    
    elif args.input[-4:] in {'.csv', '.xlsx'}: # 1 csv/excel file
        if args.input[-4:] == '.csv':
            df = pd.read_csv(args.input)
        else:
            df = pd.read_excel(args.input)
        df = df.head(2)
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
    
    if not args.overwrite_output_dir:
        assert os.path.exists(output_dir) == False

    df_out = pd.DataFrame()

#PREPROCESSING_________________________________________________________________________________________
    try:
        nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos', verbose=0)
    except: #TO DO: find prettier way of checking whether Dutch Stanza has been downloaded already
        stanza.download('nl')

    nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos', verbose=0)
    
    for infile, text in zip(infiles, texts):
        doc = nlp(text)
        parsed_sentences = [[(w.text, w.upos) for w in s.words] for s in doc.sentences]
        tokenized_sentences = [[t for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]
        tokens = [t for s in parsed_sentences for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}]
        types = set([t.lower() for t in tokens])
        syllables = [[util.get_n_syllables(t) for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]

#STATISTICS_________________________________________________________________________________________
        if args.statistics:
            n_char = len(text)
            n_syllables = sum([syl for sent in syllables for syl in sent])
            n_polysyllabic = len([i for sent in syllables for i in sent if i > 1])
            n_tokens = len(tokens)
            n_longer_than_6_char = len([t for t in tokens if len(t) < 6])
            n_types = len(types)
            n_sentences = len(doc.sentences)

            avg_char_per_word = round(mean([len(t) for t in tokens]), 2)
            std_char_per_word = round(stdev([len(t) for t in tokens]), 2)

            avg_syl_per_word = round(mean([s for sent in syllables for s in sent]), 2)
            std_syl_per_word = round(stdev([s for sent in syllables for s in sent]), 2)

            avg_words_per_sent = round(mean([len(s) for s in tokenized_sentences]), 2)
            std_words_per_sent = round(stdev([len(s) for s in tokenized_sentences]), 2)

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
            'avg_words_per_sentence': avg_words_per_sent,
            'std_words_per_sentence': std_words_per_sent
            }
        
#DISTRIBUTIONS_________________________________________________________________________________________
        if args.distributions:
            word_length_distribution = util.get_word_length_distribution(tokens)
            grapheme_distribution = util.get_grapheme_distribution(tokens)
            word_internal_grapheme_profile = util.get_word_internal_grapheme_profile(tokens)
            token_distribution = util.get_token_distribution(tokens)
            grapheme_positional_freq = util.get_grapheme_positional_freq(tokens)
            punct_dist = util.get_punct_dist(text)
            bigram_profile = util.get_bigram_profile(tokens)
            positional_word_profile = util.get_positional_word_profile(doc)
            
            dist = {
                'word_length_distribution': word_length_distribution,
                'unigram_distribution': token_distribution,
                'bigram_distribition': bigram_profile,
                'punctuation_distribution': punct_dist,
                'positional_word_profile': positional_word_profile,
                'grapheme_distribution': grapheme_distribution,
                'word_internal_grapheme_profile': word_internal_grapheme_profile,
                'grapheme_positional_distribution': grapheme_positional_freq
            }

#LEXICAL RICHNESS_________________________________________________________________________________________
        if args.lexical_richness:
            ttr = util.ttr(n_types, n_tokens)
            rttr = util.rttr(n_types, n_tokens)
            cttr = util.cttr(n_types, n_tokens)
            Herdan = util.Herdan(n_types, n_tokens)
            Summer = util.Summer(n_types, n_tokens)
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

#READABILITY_________________________________________________________________________________________
        if args.readability:
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

#POS-TAG DISTRIBUTION_________________________________________________________________________________________
        if args.pos_distribution:
            pos_tags = [pos for s in parsed_sentences for t, pos in s]
            n_total = len(pos_tags)
            pos_distribution = dict(Counter(pos_tags))
            pos_distribution = {k:v/n_total for k,v in pos_distribution.items()}

#WRITE RESULTS TO OUTPUT______________________________________________________________________________________
        row = dict()

        row['filename'] = infile
        for k, v in stats.items():
            row[k] = v
        for k, v in readability.items():
            row[k] = v
        for k, v in lr.items():
            row[k] = v
        for k, v in dist.items():
            row[k] = str(v)
        row['pos_distribution'] = str(pos_distribution)

        df_out = df_out.append(row, ignore_index=True)
    
    columns_to_cast_to_integers = [c for c in df_out.columns if c[:2]=='n_']
    if type(infiles[0]) != str:
        columns_to_cast_to_integers.append('filename')
    df_out = df_out.astype({k: 'int' for k in columns_to_cast_to_integers})
    df_out.to_csv(f'{args.output}', index=False)

#_______________________________________________________________
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=None, type=str)
    parser.add_argument('--output', default='output.csv', type=str)
    parser.add_argument('--overwrite_output_dir', default=True, type=bool)
    parser.add_argument('--statistics', default=True, type=bool)
    parser.add_argument('--distributions', default=True, type=bool)
    parser.add_argument('--lexical_richness', default=True, type=bool)
    parser.add_argument('--readability', default=True, type=bool)
    parser.add_argument('--pos_distribution', default=True, type=bool)
    parser.add_argument('--text_column', default='text', type=str)

    args = parser.parse_args()
    main(args)
