from configparser import ConfigParser

config_object = ConfigParser()

config_object["FEATURE_CONFIG"] = {
    "stats": 1,
    "distributions": 1,
    "pos_ngram_range": '(1,1)',
    "token_ngram_range": '(1,1)',
    "readability": 1,
    "lexical_richness": 1,
    "pca": 1
}

config_object["INPUT_CONFIG"] = {
    "input": './personae',
    "input_format": 'folder_with_txt',
    "text_column": 'text' #if input_format=csv
}

config_object["OUTPUT_CONFIG"] = {
    "output_dir": 'output.csv',
    "overwrite_output_dir": True
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)
