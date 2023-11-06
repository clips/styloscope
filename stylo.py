import os, shutil
from configparser import ConfigParser
from statistics import mean, stdev
from tqdm import tqdm

import pandas as pd
import stanza, util
from sklearn.decomposition import PCA

import plotly.express as px
#______________________________________________________________________________________________

def main():

#LOAD CONFIG____________________________________________________________________________________
    config_object = ConfigParser()
    config_object.read('config.ini')
    input_config = config_object["INPUT_CONFIG"] 
    output_config = config_object["OUTPUT_CONFIG"]
    feature_config = config_object["FEATURE_CONFIG"]
    dir_out = output_config['output_dir']

#LOAD DATA_____________________________________________________________________________________
    print("Loading data...")
    text_column = input_config['text_column'] if input_config['input_format'] == 'csv' else None
    delimiter = input_config['delimiter'] if input_config['input_format'] == 'csv' else None

    texts, infiles = util.load_data(
        input_config['input_format'],
        input_config['input'],
        text_column,
        delimiter
        )
    
#PREPARE_OUTPUT_DIR____________________________________________________________________________
    dir_out = output_config['output_dir']

    # if overwrite_output_dir is True, delete the directory
    # else, check if output dir exists already and return error if it does
    # create the output directory
    if int(output_config['overwrite_output_dir']):
        if os.path.exists(dir_out):
            shutil.rmtree(dir_out)
    else:
        assert os.path.exists(dir_out) == False

    os.mkdir(dir_out)

    length_dfs = []
    lexical_richness_dfs = []
    readability_dfs = []
    distribution_dfs = {
        'punctuation_distribution': [],
        'function_word_distribution': [],
        'pos_profile': [],
        'dependency_profile': [],
        # 'grapheme_distribution': [],
        # 'word_internal_grapheme_profile': [],
        # 'grapheme_positional_frequency': [],
        'ngram_profile': [],
        # 'positional_word_profile': [],
        'word_length_distribution': [],
    }

    feature_df = pd.DataFrame()

#PREPROCESSING_________________________________________________________________________________
    try:
        nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos,lemma,depparse', verbose=0)
    except: #TO DO: find prettier way of checking whether Dutch Stanza has been downloaded already
        stanza.download('nl')
        nlp = stanza.Pipeline(lang='nl', processors='tokenize,pos,lemma,depparse', verbose=0)
    
    print("Processing data...")
    for text in tqdm(texts):
        doc = nlp(text)
        parsed_sentences = [[(w.text, w.upos) for w in s.words] for s in doc.sentences]
        pos_tags = [w.upos for s in doc.sentences for w in s.words]
        dependencies = [w.deprel for s in doc.sentences for w in s.words if w.deprel]
        tokenized_sentences = [[t for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]
        tokens = [t for s in parsed_sentences for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}]
        types = set([t.lower() for t in tokens])
        syllables = [[util.get_n_syllables(t) for t, pos in s if pos not in {'PUNCT', 'SYM', 'X'}] for s in parsed_sentences]

#LENGTH STATISTICS_____________________________________________________________________________
        n_char = len(text.replace(' ', ''))
        n_syllables = sum([syl for sent in syllables for syl in sent])
        n_polysyllabic = len([i for sent in syllables for i in sent if i > 1])
        n_tokens = len(tokens)
        n_longer_than_6_char = len([t for t in tokens if len(t) < 6])
        n_types = len(types)
        n_sentences = len(doc.sentences)

        avg_char_per_word = round(mean([len(t) for t in tokens]), 3)
        std_char_per_word = round(stdev([len(t) for t in tokens]), 3)

        avg_syl_per_word = round(mean([s for sent in syllables for s in sent]), 3)
        std_syl_per_word = round(stdev([s for sent in syllables for s in sent]), 3)

        avg_words_per_sent = round(mean([len(s) for s in tokenized_sentences]), 3)
        if n_sentences > 1:
            std_words_per_sent = round(stdev([len(s) for s in tokenized_sentences]), 3)
        else:
            std_words_per_sent = 0
        ratio_long_words = round(n_longer_than_6_char/n_tokens, 3)

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
        'avg_words_per_sentence': [avg_words_per_sent],
        'std_words_per_sentence': [std_words_per_sent],
        }

        length_df = pd.DataFrame(data=stats)
        length_dfs.append(length_df)


#LEXICAL RICHNESS______________________________________________________________________________
        ttr = util.ttr(n_types, n_tokens)
        rttr = util.rttr(n_types, n_tokens)
        cttr = util.cttr(n_types, n_tokens)
        Herdan = util.Herdan(n_types, n_tokens)
        Summer = util.Summer(n_types, n_tokens)
        Dugast = 0 if n_types==n_tokens else util.Dugast(n_types, n_tokens)
        Maas = util.Maas(n_types, n_tokens)

        lr = {
        'TTR': [ttr],
        'RTTR': [rttr],
        'CTTR': [cttr],
        'Herdan': [Herdan],
        'Summer': [Summer],
        'Dugast': [Dugast],
        'Maas': [Maas]
        }

        lexical_richness_dfs.append(pd.DataFrame(data=lr))

#READABILITY___________________________________________________________________________________
        ARI = util.ARI(n_char, n_tokens, n_sentences)
        CL = util.ColemanLiau(tokens, tokenized_sentences)
        Flesch = util.Flesch(avg_words_per_sent, avg_syl_per_word)
        Fog = util.Fog(avg_words_per_sent, syllables)
        Kincaid = util.Kincaid(avg_words_per_sent, avg_syl_per_word)
        LIX = util.LIX(n_tokens, n_sentences, n_longer_than_6_char)
        RIX = util.RIX(n_longer_than_6_char, n_sentences)
        SMOG = util.SMOG(syllables)

        readability = {
        'ARI': [ARI],
        'ColemanLiau': [CL],
        'Flesch': [Flesch],
        'FOG': [Fog],
        'Kincaid': [Kincaid],
        'LIX': [LIX],
        'RIX': [RIX],
        'SMOG': [SMOG],
        }

        readability_dfs.append(pd.DataFrame(data=readability))

#DISTRIBUTIONS_________________________________________________________________________________ 
        punct_dist = util.get_punct_dist(text)
        function_word_distribution = util.get_function_word_distribution(doc)
        pos_profile = util.get_ngram_profile(pos_tags, eval(feature_config['pos_ngram_range']))
        dependency_profile = util.get_dependency_distribution(dependencies)
        # grapheme_distribution = util.get_grapheme_distribution(tokens)
        # word_internal_grapheme_profile = util.get_word_internal_grapheme_profile(tokens)
        # grapheme_positional_frequency = util.get_grapheme_positional_freq(tokens)
        ngram_profile = util.get_ngram_profile(tokens, eval(feature_config['token_ngram_range']))
        # positional_word_profile = util.get_positional_word_profile(doc)
        word_length_distribution = util.get_word_length_distribution(tokens)
        
        dist = {
            'punctuation_distribution': punct_dist,
            'function_word_distribution': function_word_distribution,
            'pos_profile': pos_profile,
            'dependency_profile': dependency_profile,
            # 'grapheme_distribution': grapheme_distribution,
            # 'word_internal_grapheme_profile': word_internal_grapheme_profile,
            # 'grapheme_positional_frequency': grapheme_positional_frequency,
            'ngram_profile': ngram_profile,
            # 'positional_word_profile': positional_word_profile,
            'word_length_distribution': word_length_distribution,
        }

        for dist_name in dist.keys():
            if dist_name not in {'positional_word_profile', 'grapheme_positional_frequency'}:
                df = pd.DataFrame(data=dist[dist_name])
            else:
                dfs = [pd.DataFrame(data=dist[dist_name][k]) for k in dist[dist_name].keys()]
                df = pd.concat(dfs, axis=0, keys=dist[dist_name].keys())
            distribution_dfs[dist_name] = distribution_dfs[dist_name] + [df]

#WRITE RESULTS TO OUTPUT_______________________________________________________________________
    print("Saving results...")
    length_df = pd.concat(length_dfs, axis=0).fillna('nan')
    length_df.insert(0, 'doc', infiles)
    length_df.to_csv(os.path.join(dir_out, 'length_statistics.csv'), index=False)

    readability_df = pd.concat(readability_dfs, axis=0).fillna('nan')
    readability_df.insert(0, 'doc', infiles)
    readability_df.to_csv(os.path.join(dir_out, 'readability_statistics.csv'), index=False)

    lexical_richness_df = pd.concat(lexical_richness_dfs, axis=0).fillna('nan')
    lexical_richness_df.insert(0, 'doc', infiles)
    lexical_richness_df.to_csv(os.path.join(dir_out, 'lexical_richness_statistics.csv'), index=False)

    for k in dist.keys():
        df = pd.concat(distribution_dfs[k], axis=0).fillna('nan')
        if k == 'word_length_distribution':
            df = df.sort_index(axis=1)
        df.insert(0, 'doc', infiles)
        df.to_csv(os.path.join(dir_out, f'{k}.csv'), index=False)
#         if int(feature_config['pca']): # group features slightly differently for pca
#             feature_row = dict()
#             feature_row['file_id'] = infile
#             if int(feature_config['stats']):
#                 for k, v in stats.items():
#                     if k == 'word_length_distribution':
#                         for length, n in v.items():
#                             feature_row[str(length)] = n
#                     else:
#                         feature_row[k] = v
#             if int(feature_config['lexical_richness']):
#                 for k, v in lr.items():
#                     feature_row[k] = v
#             if int(feature_config['readability']):
#                 for k, v in readability.items():
#                     feature_row[k] = v
#             if int(feature_config['distributions']):
#                 for _, d in dist.items():
#                     for k, v in d.items():
#                         if type(v) != dict:
#                             feature_row[str(k)] = str(v)
#                         else: # if dictionary within dictionary
#                             for key, value in v.items():
#                                 feature_row[key] = value
#             feature_df = feature_df.append(feature_row, ignore_index=True)

#     if int(feature_config['pca']) and len(df_out)>1:
#         feature_df.fillna(0, inplace=True)
    
#     columns_to_cast_to_integers = [c for c in df_out.columns if c[:2]=='n_']
#     if type(infiles[0]) != str:
#         columns_to_cast_to_integers.append('file_id')
#     df_out = df_out.astype({k: 'int' for k in columns_to_cast_to_integers})
#     df_out.to_csv(output_config['output_dir'], index=False)

# #PCA___________________________________________________________________________________________
#     if int(feature_config['pca']) and len(df_out)>2:
#         feature_columns = [c for c in feature_df.columns if  c != 'file_id']
#         X = feature_df[feature_columns]
#         pca = PCA(n_components=2)
#         components = pca.fit_transform(X)
#         fig = px.scatter(components, x=0, y=1)
#         fig.write_image("pca_plot.png")
    print("Done!")

#______________________________________________________________________________________________
if __name__ == "__main__":
    main() 
