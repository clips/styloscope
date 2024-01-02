import pandas as pd
import os
import numpy as np
from datasets import load_dataset

dataset = 'dbrd'
data = load_dataset(dataset)

df = data['test'].to_pandas() #2.22K rows
df = df.drop_duplicates(subset=['text'])

if not os.path.exists('demo') and not os.path.isdir('demo'):
    os.mkdir('demo')
df.to_csv('demo/demo_data.csv', index=False)