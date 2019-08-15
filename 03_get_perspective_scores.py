###
#
# This script loops through all comments for every guest and computes toxicity and
# severe toxicity scores for each comment using the Google Perspective API. It adds
# the scores to the comments JSON file and it adds some basic aggregate metrics
# to the guest list CSV file for each guest.
#
# This script takes a long time to run because the API has an hourly usage limit. I
# alleviated that issue a bit by creating 20 different API keys and rotating through
# them, but it still took multiple days to finish computing scores for all comments.
# The script should be fairly robust about picking up where it left off if it gets
# interrupted and needs to be run again.
#
###

import json
import os
import numpy as np
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import time
import sys
import utils  # utils.py file


## Parameters
verbose = True

# read the CSV
guest_df = utils.load_guest_list_file()

# set up Perspective API
# the text file has multiple API keys (from multiple projects) so they can hopefully all be used to speed up the process
api_service_name = 'commentanalyzer'
api_version = 'v1alpha1'
api_keys = open(utils.perspective_api_key_file).read().split()
api_list = [discovery.build(api_service_name, api_version, developerKey=key) for key in api_keys]

# specify that we'll start by using teh first API key
which_api = 0


def compute_perspective_scores(apis, comment_text, which_api=0, retry_rate=0.5, max_tries=0, current_tries=1,
                               verbose=False):
    """
    Compute toxicity and severe toxicity scores of a comment using Google's Perspective API.

    :param apis: list of Perspective API services set up using different API keys
    :param comment_text: comment text (string)
    :param which_api: index of of the API service that will be used from apis
    :param retry_rate: how long to wait before making another API call if it fails
    :param max_tries: maximum times to retry (set to 0 for no maximum)
    :param current_tries: the current attempt number
    :param verbose: if True, print some status messages

    :return: toxicity score, severe toxicity score, and which API number was used
    """

    # if we've tried too many times, quit and print a message
    if current_tries > max_tries > 0:
        sys.exit(f'Maximum tries ({max_tries}) exceeded without success.')

    # select the API out of the list
    if not isinstance(apis, list):
        apis = [apis]
    api = apis[which_api]

    # attempt to get scores from Perspective API; if quota is exceeded, wait and try again with the next API
    try:

        # max comment length is 20480 -- truncate if it's that long
        if len(comment_text) > 20480:
            comment_text = comment_text[:20479]

        analyze_request = {
            'comment': {'text': comment_text},
            'requestedAttributes': {'TOXICITY': {}, 'SEVERE_TOXICITY': {}},
            'languages': ['en']
        }

        response = api.comments().analyze(body=analyze_request).execute()

        tox_score = response['attributeScores']['TOXICITY']['summaryScore']['value']
        sev_tox_score = response['attributeScores']['SEVERE_TOXICITY']['summaryScore']['value']

        # return the toxicity score, severe toxicity score, and which API key was used
        return tox_score, sev_tox_score, which_api

    except HttpError as e:
        # long comments are already handled above, but sometimes this error is thrown for comments w/ no
        # readable characters -- skip those
        if 'Comment text too long' in e._get_reason():
            return np.nan, np.nan, which_api

        elif verbose and ('Quota exceeded' not in e._get_reason()):
            print(f'\nOther HttpError -- API {which_api}: {e._get_reason()}')

        time.sleep(retry_rate)

        # retry using the next entry in the API list
        next_api = (which_api + 1) % len(apis)

        return compute_perspective_scores(apis=apis, comment_text=comment_text, which_api=next_api,
                                          retry_rate=retry_rate, max_tries=max_tries, current_tries=current_tries+1,
                                          verbose=verbose)

    # also handle ConnectionResetError -- try again with same API without counting the try
    except ConnectionResetError as e:
        time.sleep(retry_rate)

        if verbose:
            print(f'Handled connection reset error -- API key {which_api}')

        return compute_perspective_scores(apis=apis, comment_text=comment_text, which_api=which_api,
                                          retry_rate=retry_rate, max_tries=max_tries, current_tries=current_tries,
                                          verbose=verbose)


def add_perspective_scores_to_json(file, which_api=0, comments_per_write=50, verbose=True):
    """
    Add keys for each comment in the JSON file with the toxicity and severe toxicity scores. This function might take a
    very long time to process all comments, so the JSON file is written periodically to avoid losing progress if it
    crashes.

    :param file: comment file path
    :param which_api: which API from the list to use first
    :param comments_per_write: number of comments to process before writing file.
    :param verbose: if True, print some status messages

    :return: the API that was used last (so we can start with the next one for the next comment file)
    """

    # get comments by reading the JSON file for the video ID
    comments = json.load(open(file, 'r'))

    n_without_scores = sum([('commentText' in comment) and ('perspective_toxicity' not in comment)
                            for comment in comments])

    if verbose:
        print(f'{len(comments)} ({n_without_scores} without scores)', flush=True)

    i = 0

    for comment in comments:

        # get scores from Perspective API if the comment has text and we haven't already computed the scores
        if 'commentText' in comment:
            if ('perspective_toxicity' not in comment) \
                    or (comment['perspective_toxicity'] == np.nan) \
                    or ('perspective_severe_toxicity' not in comment) \
                    or (comment['perspective_severe_toxicity'] == np.nan):

                tox_score, sev_tox_score, which_api = compute_perspective_scores(apis=api_list,
                                                                                 comment_text=comment['commentText'],
                                                                                 which_api=which_api,
                                                                                 verbose=verbose)
                comment['perspective_toxicity'] = tox_score
                comment['perspective_severe_toxicity'] = sev_tox_score

                # increment the counter
                i += 1
        else:
            comment['perspective_toxicity'] = np.nan
            comment['perspective_severe_toxicity'] = np.nan

        # print progress indicators if verbose is set
        if verbose:
            if i % 1000 == 0 and i > 0:
                print(i, flush=True)
            elif i % 100 == 0 and i > 0:
                print('.', end=' ', flush=True)

        # after processing the specified number of comments, write the JSON file
        if i % comments_per_write == 0 and i > 0:
            json.dump(comments, open(file, 'w'), indent=2)

    # write the JSON file after processing all comments
    json.dump(comments, open(file, 'w'), indent=2)

    if verbose and i > 0:
        print('')

    # return the api that was last used so we know which one to start with for the next row
    return which_api


# loop through guest CSV file
#  - first, add Perspective API scores to each JSON file
#  - then calculate mean scores for each guest and save to CSV file
for i, row in guest_df.iterrows():

    # don't do anything if there's no video ID or the comments haven't been scraped
    if row['video_id'] == '':
        if verbose:
            print(f"Skipping {row['guest']} -- missing video_id")
        continue
    elif row['done'] not in [1, '1']:
        if verbose:
            print(f"Skipping {row['guest']} -- comments not scraped")
        continue

    if verbose:
        start = time.time()
        print(f"\nstarting {row['guest']} -- ", end='')

    # get comment file add the Perspective API scores to each comment
    video_id = row['video_id']
    comment_file = os.path.join(utils.comment_dir, f'comments-{video_id}.json')
    which_api = add_perspective_scores_to_json(comment_file, which_api=which_api, verbose=verbose)

    # get the average Perspective API scores
    comments = json.load(open(comment_file, 'r'))
    mean_tox = np.nanmean([comment['perspective_toxicity'] for comment in comments])
    mean_sev_tox = np.nanmean([comment['perspective_severe_toxicity'] for comment in comments])
    var_tox = np.nanvar([comment['perspective_toxicity'] for comment in comments])
    var_sev_tox = np.nanvar([comment['perspective_severe_toxicity'] for comment in comments])

    # get the average scores for the first 1000 comments
    comments_1000 = comments[-1000:]
    mean_tox_1000 = np.nanmean([comment['perspective_toxicity'] for comment in comments_1000])
    mean_sev_tox_1000 = np.nanmean([comment['perspective_severe_toxicity'] for comment in comments_1000])
    var_tox_1000 = np.nanvar([comment['perspective_toxicity'] for comment in comments_1000])
    var_sev_tox_1000 = np.nanvar([comment['perspective_severe_toxicity'] for comment in comments_1000])

    # add the mean scores to the dataframe
    guest_df.loc[i, 'mean_toxicity'] = mean_tox
    guest_df.loc[i, 'mean_severe_toxicity'] = mean_sev_tox
    guest_df.loc[i, 'var_toxicity'] = var_tox
    guest_df.loc[i, 'var_severe_toxicity'] = var_sev_tox
    guest_df.loc[i, 'mean_toxicity_1000'] = mean_tox_1000
    guest_df.loc[i, 'mean_severe_toxicity_1000'] = mean_sev_tox_1000
    guest_df.loc[i, 'var_toxicity_1000'] = var_tox_1000
    guest_df.loc[i, 'var_severe_toxicity_1000'] = var_sev_tox_1000

    utils.save_guest_list_file(guest_df)

    if verbose:
        end = time.time()
        str = f"done with {row['guest']} -- mean_tox = {round(mean_tox, 3)}, mean_sev_tox = {round(mean_sev_tox, 3)}"
        str += f", time = {round(end - start, 0)} seconds"
        print(str)
