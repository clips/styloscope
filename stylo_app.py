import os, shutil, io, zipfile
import util, visualizations, warnings
from configparser import ConfigParser
from statistics import mean, stdev
from tqdm import tqdm

import pandas as pd
import gradio as gr
import spacy, pyphen
import numpy as np
from spacy.matcher import Matcher
#______________________________________________________________________________________________

def main(fn, lang, readability_metric, diversity_metric, progress=gr.Progress(track_tqdm=True)):

    progress(0, desc="Starting pipeline...")
    
    warnings.simplefilter(action='ignore', category=FutureWarning)

    # if overwrite_output_dir is True, delete the directory
    # else, check if output dir exists already and return error if it does
    # create the output directory
    dir_out = 'output'
    if os.path.exists(dir_out):
        shutil.rmtree(dir_out)
    os.mkdir(dir_out)
    os.mkdir(os.path.join(dir_out, 'visualizations'))

#LOAD_DATA_____________________________________________________________________________________
    texts, infiles = util.load_data('csv', fn, 'text', ',')
    
#PREPARE_OUTPUT_DIR____________________________________________________________________________

    length_dfs = []
    lexical_richness_dfs = []
    readability_dfs = []
    distribution_dfs = {
        'punctuation_distribution': [],
        'function_word_distribution': [],
        'pos_profile': [],
        'dependency_profile': [],
        'word_length_distribution': [],
    }

    pos_outputs = []
    dependency_outputs = []

#PREPROCESSING_________________________________________________________________________________
    
    # Determine language
    if lang == 'Dutch':
        nlp = spacy.load("nl_core_news_lg")
        dic = pyphen.Pyphen(lang='nl_NL')
    elif lang == 'English':
        nlp = spacy.load("en_core_web_lg")
        dic = pyphen.Pyphen(lang='en')
    elif lang == 'French':
        nlp = spacy.load("fr_core_news_lg")
        dic = pyphen.Pyphen(lang='fr_FR')
    else:
        nlp = spacy.load("de_core_news_lg")
        dic = pyphen.Pyphen(lang='de')
    
    # Initialize the SpaCy matcher with a vocab and passive rules
    passive_rules = [
        [{'DEP': 'nsubj:pass'}, {'DEP': 'aux:pass'}],
        [{'DEP': 'aux:pass'}],
        [{'DEP': 'nsubj:pass'}],
    ]
    matcher = Matcher(nlp.vocab)  
    matcher.add('Passive',  passive_rules)
  
    print("Processing data...")
    for text in progress.tqdm(texts, unit='documents processed'): # Analyze text by text

        # check if text is empty
        if not text.strip():
            dummy_df = pd.DataFrame(data={'__Dummy__': ['dummy']}) # add dummy data to output
            length_dfs.append(dummy_df)
            lexical_richness_dfs.append(dummy_df)
            readability_dfs.append(dummy_df)
            for k in distribution_dfs.keys():
                distribution_dfs[k].append(dummy_df)
            continue # skip to the next text
    
        text = ' '.join(text.split()) # remove redundant whitespace

        # tokenization, parsing, etc.
        doc = nlp(text)
        parsed_sentences = [[(w.text, w.pos_) for w in s] for s in doc.sents]
        pos_tags = [w.pos_ for s in doc.sents for w in s]
        dependencies = [w.dep_ for s in doc.sents for w in s if w.dep_]
        tokenized_sentences = [[t for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]
        tokens = [t for s in parsed_sentences for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}]
        types = set([t.lower() for t in tokens])
        syllables = [[util.get_n_syllables(t, dic) for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]

        # store parsing results
        pos_outputs.append(' '.join(pos_tags))
        dependency_outputs.append(' '.join(dependencies))

#LENGTH STATISTICS_____________________________________________________________________________

        # check if text is empty (or contains only punctuation/symbols/other) -> skip
        n_tokens = len(tokens)
        n_char = len(text.replace(' ', ''))
        n_syllables = sum([syl for sent in syllables for syl in sent])
        n_polysyllabic = len([i for sent in syllables for i in sent if i > 1])
        n_longer_than_6_char = len([t for t in tokens if len(t) > 6])
        n_types = len(types)
        n_sentences = len(list(doc.sents))

        avg_char_per_word = mean([len(t) for t in tokens]) if n_tokens > 0 else 0
        std_char_per_word = stdev([len(t) for t in tokens]) if n_tokens > 1 else 0

        avg_syl_per_word = mean([s for sent in syllables for s in sent]) if n_tokens > 0  else 0
        std_syl_per_word = stdev([s for sent in syllables for s in sent]) if n_tokens > 1 else 0

        avg_words_per_sent = mean([len(s) for s in tokenized_sentences])
        std_words_per_sent = stdev([len(s) for s in tokenized_sentences]) if n_sentences > 1 else 0

        ratio_long_words = 0 if n_tokens == 0 else n_longer_than_6_char/n_tokens
        ratio_content_words = util.ratio_content_words(doc)
        ratio_passive_sentences = util.get_passive_ratio(doc, matcher)

        stats = {
        'n_characters': [n_char],
        'n_syllables': [n_syllables],
        'n_tokens': [n_tokens],
        'n_polysyllabic_tokens': [n_polysyllabic],
        'n_long_tokens': [n_longer_than_6_char],
        'n_types': [n_types],
        'n_sentences': [n_sentences],
        'avg_characters_per_word': [avg_char_per_word],
        'std_characters_per_word': [std_char_per_word],
        'avg_syllables_per_word': [avg_syl_per_word],
        'std_syllables_per_word': [std_syl_per_word],
        'ratio_long_words': [ratio_long_words],
        'ratio_content_words': [ratio_content_words],
        'ratio_passive_sentences': [ratio_passive_sentences],
        'avg_words_per_sentence': [avg_words_per_sent],
        'std_words_per_sentence': [std_words_per_sent],
        }

        length_df = pd.DataFrame(data=stats)
        length_dfs.append(length_df)


#LEXICAL DIVERSITY______________________________________________________________________________
        if diversity_metric == 'TTR':
            score = util.ttr(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'RTTR':
            score = util.rttr(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'CTTR':
            score = util.cttr(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'STTR':
            score = util.sttr(tokens) if n_tokens != 0 else None
        elif diversity_metric == 'Herdan':
            score = util.Herdan(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'Summer':
            score = util.Summer(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'Dugast':
            score = util.Dugast(n_types, n_tokens) if n_tokens != 0 else None
        elif diversity_metric == 'Maas':
            score = util.Maas(n_types, n_tokens) if n_tokens != 0 else None
        else:
            ValueError('Please provide one of the following lexical diversity metrics: "TTR", "RTTR", "CTTR", "STTR", "Herdan", "Summer", "Dugast", "Maas"')

        lr = {
        'score': [score],
        }

        lexical_richness_dfs.append(pd.DataFrame(data=lr))

#READABILITY___________________________________________________________________________________
        if readability_metric == 'ARI':
            score = util.ARI(n_char, n_tokens, n_sentences) if n_tokens != 0 else None
        elif readability_metric == 'Coleman-Liau':
            score = util.ColemanLiau(tokens, tokenized_sentences) if n_tokens != 0 else None
        elif readability_metric == 'Flesch reading ease':
            score = util.Flesch(avg_words_per_sent, avg_syl_per_word) if n_tokens != 0 else None
        elif readability_metric == 'Flesch Kincaid grade level':
            score = util.Kincaid(avg_words_per_sent, avg_syl_per_word) if n_tokens != 0 else None
        elif readability_metric == 'Gunning Fog':
            score = util.Fog(avg_words_per_sent, syllables) if n_tokens != 0 else None
        if readability_metric == 'SMOG':
            score = util.SMOG(syllables) if n_tokens != 0 else None
        elif readability_metric == 'LIX':
            score = util.LIX(n_tokens, n_sentences, n_longer_than_6_char) if n_tokens != 0 else None
        elif readability_metric == 'RIX':
            score = util.RIX(n_longer_than_6_char, n_sentences) if n_tokens != 0 else None
        else:
            ValueError('Please provide one of the following metrics: "ARI", "Coleman-Liau", "Flesch reading ease", "Flesch Kincaid grade level", "Gunning Fog", "SMOG", "LIX", "RIX".')

        interpretation = util.interpret_readability(score, readability_metric)

        readability = {
            'score': [score],
            'interpretation': [interpretation]
        }

        readability_dfs.append(pd.DataFrame(data=readability))

#DISTRIBUTIONS_________________________________________________________________________________ 
        punct_dist = util.get_punct_dist(text)
        function_word_distribution = util.get_function_word_distribution(doc)
        pos_profile = util.get_ngram_profile(pos_tags)
        dependency_profile = util.get_dependency_distribution(dependencies)
        word_length_distribution = util.get_word_length_distribution(tokens)
        
        dist = {
            'punctuation_distribution': punct_dist,
            'function_word_distribution': function_word_distribution,
            'pos_profile': pos_profile,
            'dependency_profile': dependency_profile,
            'word_length_distribution': word_length_distribution,
        }

        for dist_name in dist.keys():
            df = pd.DataFrame(data=dist[dist_name])
            distribution_dfs[dist_name] = distribution_dfs[dist_name] + [df]
    
#WRITE RESULTS TO OUTPUT_______________________________________________________________________
    print("Aggregating data, creating visualizations, and saving raw results...")
    progress(1, desc="Aggregating data. Please wait...")

    # length statistics
    print('    ...length statistics')
    length_df = pd.concat(length_dfs, axis=0)
    length_df = length_df.drop(columns=['__Dummy__']) if '__Dummy__' in length_df.columns else length_df
    length_df.insert(0, 'doc', infiles)

    mean_length_df = length_df.mean().to_frame().T
    mean_length_df['doc'] = 'mean'

    std_length_df = length_df.std().to_frame().T
    std_length_df['doc'] = 'std'

    length_df = pd.concat([length_df, mean_length_df, std_length_df])
    length_df = length_df.round(3)
    length_df.to_csv(os.path.join(dir_out, 'length_statistics.csv'), index=False)

    # readability statistics
    print('    ...readability statistics')
    readability_df = pd.concat(readability_dfs, axis=0)
    readability_df = readability_df.drop(columns=['__Dummy__']) if '__Dummy__' in readability_df.columns else readability_df
    readability_df.insert(0, 'doc', infiles)

    mean_readability_df = readability_df.mean().to_frame().T
    mean_readability_df['doc'] = 'mean'

    std_readability_df = readability_df.std().to_frame().T
    std_readability_df['doc'] = 'std'

    readability_df = pd.concat([readability_df, mean_readability_df, std_readability_df])
    readability_df = readability_df.round(3)
    readability_df.to_csv(os.path.join(dir_out, 'readability_statistics.csv'), index=False)

    # lexical richness statistics
    print('    ...lexical richness statistics')
    lexical_richness_df = pd.concat(lexical_richness_dfs, axis=0)
    lexical_richness_df = lexical_richness_df.drop(columns=['__Dummy__']) if '__Dummy__' in lexical_richness_df.columns else lexical_richness_df
    lexical_richness_df.insert(0, 'doc', infiles)

    mean_lexical_richness_df = lexical_richness_df.mean().to_frame().T
    mean_lexical_richness_df['doc'] = 'mean'

    std_lexical_richness_df = lexical_richness_df.std().to_frame().T
    std_lexical_richness_df['doc'] = 'std'

    lexical_richness_df = pd.concat([lexical_richness_df, mean_lexical_richness_df, std_lexical_richness_df])
    lexical_richness_df = lexical_richness_df.round(3)
    lexical_richness_df.to_csv(os.path.join(dir_out, 'lexical_richness_statistics.csv'), index=False)

    # parsing results
    parsing_df = pd.DataFrame(data={
        'document': infiles,
        'part-of-speech tags': pos_outputs,
        'syntactic dependencies': dependency_outputs,
    })
    parsing_df.to_csv(os.path.join(dir_out, 'parsing_results.csv'), index=False)
    
    # distributions
    print('    ...distributions')
    for k in dist.keys():
        distribution_dfs[k] = [df if not df.empty else pd.DataFrame([np.nan], columns=['__Empty__']) for df in distribution_dfs[k]] # when there is an empty dataframe, pd.concat ignores this leading to incongruencies in length
        df = pd.concat(distribution_dfs[k], axis=0).fillna(0)
        df = df.drop(columns=['__Dummy__']) if '__Dummy__' in df.columns else df
        df = df.drop(columns=['__Empty__']) if '__Empty__' in df.columns else df          
        df.insert(0, 'doc', infiles)
        mean_df = df.mean().to_frame().T
        std_df = df.std().to_frame().T
        mean_df['doc'] = 'mean'
        std_df['doc'] = 'std'
        df = pd.concat([df, mean_df, std_df])
        df = df.round(3)
        df.to_csv(os.path.join(dir_out, f'{k}.csv'), index=False)
        
        # visualizations
        if k != 'function_word_distribution':
            df.insert(0, 'source', ['input corpus']*len(df))
            mean_df, std_df = visualizations.prepare_df(df, k, lang)
            plt = visualizations.generate_bar_chart(mean_df, std_df, k, dir_out)
            if k == 'punctuation_distribution':
                punct_plot = plt 
            elif k == 'dependency_profile':
                dep_plot = plt 
            elif k == 'pos_profile':
                pos_plot = plt 
            elif k == 'word_length_distribution':
                len_plot = plt
            else:
                pass

    return (
        shutil.make_archive(base_name='output', format='zip', base_dir='output', root_dir='.'),
        dep_plot,
        pos_plot,
        punct_plot,
        len_plot,
    )
