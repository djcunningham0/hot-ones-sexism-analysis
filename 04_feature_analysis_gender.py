###
#
# This script runs the informative Dirichlet model on the comments dataset and returns
# a dataframe with the resulting features.
#
# It takes a little over 30 minutes to run on the whole dataset on my MacBook Pro.
#
###


import utils
import nlp_utils as nlp
import os
import json
from models import multinomial_dirichlet_model
from nltk.tokenize import TweetTokenizer
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import random
import math
from datetime import datetime
import time


## PARAMETERS
sample_rate = 1
max_features = 20000
scrub_names = True
bigrams = True


print(f'starting at {datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}', flush=True)
start = time.time()

# load dataframe and remove rows that won't be included in analysis
guest_df = utils.load_guest_list_file(apply_filters=True)

# set up tokenizer
mylemmatizer = nlp.MyLemmatizer()
tknzr = TweetTokenizer(reduce_len=True)
mytokenizer = nlp.MyTokenizer(tokenizer=tknzr, stemmer=mylemmatizer, replace_pronouns=True)

# put (a sample of) combined comments into a column for each guest
for i, row in guest_df.iterrows():
    video_id = row['video_id']
    comment_path = os.path.join(utils.comment_dir, f'comments-{video_id}.json')
    comments_json = json.load(open(comment_path, 'r'))
    comments = [comment['commentText']
                for comment in comments_json
                if 'commentText' in comment]

    if sample_rate < 1:
        random.seed(0)
        comments = random.sample(comments, math.floor(len(comments) * sample_rate))

    guest_df.loc[i, 'comments'] = ' '.join(comments)


# replace names of the guests with generic '<name>' token -- otherwise results are dominated by names
# note: the guest's name is only replaced in his/her comments, not in comments for other guests
if scrub_names:
    guest_df = utils.scrub_names(guest_df)

# group by female_flag, concatenate comments, and put into dictionary that can be passed to CountVectorizer
grouping_col = 'female_flag'
groups = {}
for label in np.unique(guest_df[grouping_col]):
    text = [row['comments'] for i, row in guest_df.iterrows() if row[grouping_col] == label]
    groups[label] = ' '.join(text)

print(f'data prep: {round(time.time() - start)} seconds', flush=True)

# analyze words -- save to CSV and pickle file (CSV probably won't preserve emojis but pickle will)
word_start = time.time()
cv = CountVectorizer(tokenizer=mytokenizer.tokenize, max_features=max_features)
counts = cv.fit_transform(groups.values())
word_df = multinomial_dirichlet_model(counts, feature_names=cv.get_feature_names())
filename = os.path.join(utils.data_dir, f'gender_analysis_word')
if sample_rate < 1:
    filename += f'_{round(sample_rate * 100)}pct'
word_df.to_csv(f'{filename}.csv', index=False)
word_df.to_pickle(f'{filename}.pickle')

print(f'word analysis: {round(time.time() - word_start)} seconds', flush=True)

# analyze words and bigrams -- save to CSV and pickle file
if bigrams:
    bigram_start = time.time()
    cv = CountVectorizer(tokenizer=mytokenizer.tokenize, max_features=max_features, ngram_range=(1,2))
    counts = cv.fit_transform(groups.values())
    bigram_df = multinomial_dirichlet_model(counts, feature_names=cv.get_feature_names())
    filename = os.path.join(utils.data_dir, f'gender_analysis_bigram')
    if sample_rate < 1:
        filename += f'_{round(sample_rate * 100)}pct'
    bigram_df.to_csv(f'{filename}.csv', index=False)
    bigram_df.to_pickle(f'{filename}.pickle')

    print(f'bigram analysis: {round(time.time() - bigram_start)} seconds', flush=True)
    print(f'total: {round(time.time() - start)} seconds elapsed', flush=True)

print(f'finished at {datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}')
