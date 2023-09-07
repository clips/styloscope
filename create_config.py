from configparser import ConfigParser

config_object = ConfigParser()

config_object["FEATURE_CONFIG"] = {
    "stats": 1, # 1 or 0
    "distributions": 1, # 1 or 0
    "pos_ngram_range": '(1,1)', # 1 or 0
    "token_ngram_range": '(1,1)', # 1 or 0
    "readability": 1, # 1 or 0
    "lexical_richness": 1, # 1 or 0
    "pca": 1 # 1 or 0
}

config_object["INPUT_CONFIG"] = {
    "input": './personae', #.csv file or path to zip folder
    "input_format": 'folder_with_txt', # csv or zip
    "text_column": 'text' #only relevant if input_format==csv
}

config_object["OUTPUT_CONFIG"] = {
    "output_dir": 'output.csv',
    "overwrite_output_dir": '1' # 1 or 0
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)