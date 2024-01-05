from configparser import ConfigParser

config_object = ConfigParser()

config_object["INPUT_CONFIG"] = {
    "input": 'demo/demo_data.csv', #.csv file or path to zip folder
    "input_format": 'csv', # 'csv' or 'zip'
    "text_column": 'text', #only relevant if input_format==csv
    "delimiter": ',', #only relevant if input_format==csv
    "language": 'Dutch', # Dutch, English, French, German
    "readability metric": 'RIX', # ARI, Coleman-Liau, Flesch reading ease, Flesch Kincaid grade level, Gunning Fog, SMOG, LIX, RIX
    "lexical diversity metric": "STTR" # TTR, RTTR, CTTR, STTR, Herdan, Summer, Dugast, Maas
}

config_object["OUTPUT_CONFIG"] = {
    "output_dir": 'demo/output', # directory to the output folder
    "overwrite_output_dir": '1' # 1 or 0
}

with open('config.ini', 'w') as conf:
    config_object.write(conf)
