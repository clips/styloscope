from configparser import ConfigParser

config_object = ConfigParser()

config_object["INPUT_CONFIG"] = {
    "input": '', #.csv file or path to zip folder
    "input_format": '', # 'csv', 'zip' or 'huggingface'
    "text_column": '', #only relevant if input_format==csv
    "delimiter": ',', #only relevant if input_format==csv
    "language": '', # Dutch, English, French, German
    "readability metric": 'RIX', # ARI, Coleman-Liau, Flesch reading ease, Flesch Kincaid grade level, Gunning Fog, SMOG, LIX, RIX
    "lexical diversity metric": "STTR", # TTR, RTTR, CTTR, STTR, Herdan, Summer, Dugast, Maas
    "STTR span size": 100, # Span (n tokens) used to compute STTR; irrelevant if other diversity metric is used
}

config_object['HUGGINGFACE_CONFIG'] = {
    "dataset_name": '', # identifier of HuggingFace dataset
    "subset": '', # subset of dataset (optional if dataset does not contain subsets)
    "split": '', # split of dataset (optional if dataset does not contain splits)
    "text_column": '', # column name of text to analyze
}

config_object["OUTPUT_CONFIG"] = {
    "output_dir": 'output', # directory to the output folder
    "overwrite_output_dir": '1' # 1 or 0
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)
