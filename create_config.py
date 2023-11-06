from configparser import ConfigParser

config_object = ConfigParser()

config_object["FEATURE_CONFIG"] = {
    "pos_ngram_range": '(1,1)', # 1 or 0
    "token_ngram_range": '(1,1)', # 1 or 0
}

config_object["INPUT_CONFIG"] = {
    "input": 'personae.zip', #.csv file or path to zip folder
    "input_format": 'zip', # 'csv' or 'zip'
    "text_column": 'text', #only relevant if input_format==csv
    "delimiter": ',' #only relevant if input_format==csv
}

config_object["OUTPUT_CONFIG"] = {
    "output_dir": 'demo_output',
    "overwrite_output_dir": '1' # 1 or 0
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)
