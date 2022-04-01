import json
import pandas as pd
import util
import argparse
import stanza
import os
from statistics import mean, stdev
from collections import Counter

from transformers import AutoModel, AutoTokenizer

#_______________________________________________________________

def main(args):

    #load data
    with open(args.infile) as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines]
    text = ' '.join(lines)

    #prepare output
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    #preprocessing
    nlp = stanza.Pipeline(lang='nl', processors='tokenize,mwt,pos')
    doc = nlp(text)

    parsed_sentences = [[(w.text, w.upos) for w in s.words] for s in doc.sentences]
    tokenized_sentences = [[t for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]
    tokens = [t for s in parsed_sentences for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}]
    types = set([t.lower() for t in tokens])
    syllables = [[util.get_n_syllables(t) for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]

    #general statistics
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
        'n characters': n_char,
        'n syllables': n_syllables,
        'n tokens': n_tokens,
        'n polysyllabic tokens': n_polysyllabic,
        'n long tokens (>6 char)': n_longer_than_6_char,
        'n types': n_types,
        'n sentences': n_sentences,
        'avg. characters per word': avg_char_per_word,
        'std. characters per word': std_char_per_word,
        'avg. syllables per word': avg_syl_per_word,
        'std. syllables per word': std_syl_per_word,
        'avg. words per sentence': avg_words_per_sent,
        'std. words per sentence': std_words_per_sent
        }

        with open(f'{output_dir}/stats.json', 'w') as outfile:
            json.dump(stats, outfile)

    #lexical richness
    if args.lexical_richness:
        ttr = util.ttr(n_types, n_tokens)
        rttr = util.rttr(n_types, n_tokens)
        cttr = util.cttr(n_types, n_tokens)
        Herdan = util.Herdan(n_types, n_tokens)
        Summer = util.Summer(n_types, n_tokens)
        Dugast = util.Dugast(n_types, n_tokens)
        Maas = util.Maas(n_types, n_tokens)

        lr = {
        'Type-token ratio (TTR)': ttr,
        'Root type-token ratio (RTTR)': rttr,
        'Corrected type-token ratio (CTTR)': cttr,
        'Herdan (1955)': Herdan,
        "Summer's index": Summer,
        'Dugast (1978)': Dugast,
        'Maas (1972)': Maas
        }

        with open(f'{output_dir}/lr.json', 'w') as outfile:
            json.dump(lr, outfile)

    #readability
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
        'Coleman-Liau index': CL,
        'Flesch reading ease index': Flesch,
        "Gunning's Fog index": Fog,
        'Flesch-Kincaid grade level index': Kincaid,
        'LIX': LIX,
        'RIX': RIX,
        'SMOG': SMOG
        }

        with open(f'{output_dir}/readability.json', 'w') as outfile:
            json.dump(readability, outfile)

    #pos-tags
    if args.pos_distribution:
        pos_tags = [pos for s in parsed_sentences for t, pos in s]
        pos_distribution = dict(Counter(pos_tags))

        with open(f'{output_dir}/pos.json', 'w') as outfile:
            json.dump(pos_distribution, outfile)

    #gender, age, education, personality
    if args.authorship_attributes:
        pass

    #author similarity
    if args.author_comparison:
        pass

    #register
    if args.register:
        pass


#_______________________________________________________________

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', default=None, type=str)
    parser.add_argument('--output_dir', default='output', type=str)
    parser.add_argument('--statistics', default=True, type=bool)
    parser.add_argument('--lexical_richness', default=True, type=bool)
    parser.add_argument('--readability', default=True, type=bool)
    parser.add_argument('--pos_distribution', default=True, type=bool)
    parser.add_argument('--authorship_attributes', default=True, type=bool)
    parser.add_argument('--author_comparison', default=True, type=bool)
    parser.add_argument('--register', default=True, type=bool)

    args = parser.parse_args()
    main(args)
