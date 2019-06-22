import json
import os
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import utils  # utils.py file


# read the CSV
guest_df = utils.load_guest_list_file()

# initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

for i, row in guest_df.iterrows():
    # don't do anything if there's no video ID or the comments haven't been scraped
    if (row['video_id'] == '') or (row['done'] not in [1, '1']):
        continue

    # get comments by reading the JSON file for the video ID
    video_id = row['video_id']
    comment_file = os.path.join(utils.comment_dir, f'comments-{video_id}.json')
    comments = json.load(open(comment_file, 'r'))
    n_comments = len(comments)

    # get sentiment scores for all comments
    scores = [sia.polarity_scores(comment['commentText'])['compound']
              for comment in comments
              if 'commentText' in comment]

    # compute basic stats about score distribution
    mean_score = np.mean(scores)
    var_score = np.var(scores)
    n_positive = sum([score > 0 for score in scores])
    n_negative = sum([score < 0 for score in scores])
    pos_ratio = n_positive / n_negative

    # same numbers with zeros (completely neutral) removed
    nozero = [score for score in scores if score != 0]
    mean_nozero = np.mean(nozero)
    var_nozero = np.var(nozero)

    # same numbers for first 1000 comments
    scores_1000 = scores[-1000:]
    mean_score_1000 = np.mean(scores_1000)
    var_score_1000 = np.var(scores_1000)
    n_positive_1000 = sum([score > 0 for score in scores_1000])
    n_negative_1000 = sum([score < 0 for score in scores_1000])
    pos_ratio_1000 = n_positive_1000 / n_negative_1000

    nozero_1000 = [score for score in scores_1000 if score != 0]
    mean_nozero_1000 = np.mean(nozero_1000)
    var_nozero_1000 = np.var(nozero_1000)

    # add values to dataframe
    guest_df.loc[i, 'n_comments'] = n_comments
    guest_df.loc[i, 'mean'] = mean_score
    guest_df.loc[i, 'variance'] = var_score
    guest_df.loc[i, 'positive_ratio'] = pos_ratio
    guest_df.loc[i, 'mean_nozero'] = mean_nozero
    guest_df.loc[i, 'variance_nozero'] = var_nozero
    guest_df.loc[i, 'mean_1000'] = mean_score_1000
    guest_df.loc[i, 'variance_1000'] = var_score_1000
    guest_df.loc[i, 'positive_ratio_1000'] = pos_ratio_1000
    guest_df.loc[i, 'mean_nozero_1000'] = mean_nozero_1000
    guest_df.loc[i, 'variance_nozero_1000'] = var_nozero_1000

# write dataframe to CSV
utils.save_guest_list_file(guest_df)
