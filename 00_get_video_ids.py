###
#
# This script uses the YouTube API to get the video ID and URL for each guest in the
# guest list CSV file. It adds the video ID and URL to the CSV file.
#
###

from googleapiclient import discovery
import pandas as pd
from googleapiclient.errors import HttpError
import utils  # utils.py file


# access YouTube API
api_service_name = 'youtube'
api_version = 'v3'
api_key = open(utils.youtube_api_key_file).read().strip()
youtube = discovery.build(api_service_name, api_version, developerKey=api_key)

# read the CSV
guest_df = utils.load_guest_list_file()

# loop through guests with no URLs first, then the ones that haven't been manually verified
incomplete = guest_df.loc[guest_df['video_id'] == '', 'guest']
unverified = guest_df.loc[~guest_df['url_status'].str.contains('verified'), 'guest']

# skip guests if indicated in url_status column
skip = guest_df.loc[guest_df['url_status'].str.contains('skip'), 'guest']
incomplete = incomplete[~incomplete.isin(skip)]
unverified = unverified[~unverified.isin(skip)]

# loop through dataframe, query for guest name, then record info for first video result
max_results = 3
for guest in pd.concat([incomplete, unverified]).drop_duplicates():

    # query for "hot ones [guest name]" and select the first result
    request = youtube.search().list(
        part='snippet',
        maxResults=max_results,  # just pull the first result
        q='hot ones ' + guest
    )

    # try to get the search results and quit the loop if the API quota is exceeded (or some other API error)
    try:
        response = request.execute()
    except HttpError as e:
        if b'quota' in e.content:
            print('Quota exceeded on', guest, '--', e)
        else:
            print('HttpError on ', guest, '--', e)
        break

    # check the results one at a time until finding one that's a video (not a channel)
    i = 0
    video_id, video_url, video_title, channel_title = '', '', '', ''
    while i < max_results:
        item = response['items'][i]  # just check the first result

        # if the result is a video it will have these keys
        if 'id' in item and 'videoId' in item['id']:
            i = max_results  # quit out of the while loop after this one
            video_id = item['id']['videoId']
            video_url = 'https://www.youtube.com/watch?v=' + video_id

            if 'snippet' in item:
                if 'title' in item['snippet']:
                    video_title = item['snippet']['title']
                if 'channelTitle' in item['snippet']:
                    channel_title = item['snippet']['channelTitle']

        else:
            i += 1  # check the next result

    # fill in the columns in the dataframe
    guest_df.loc[guest_df['guest'] == guest, 'video_id'] = video_id
    guest_df.loc[guest_df['guest'] == guest, 'video_url'] = video_url
    guest_df.loc[guest_df['guest'] == guest, 'video_title'] = video_title
    guest_df.loc[guest_df['guest'] == guest, 'channel_title'] = channel_title

# after looping through all guests in the file, overwrite the CSV with the added info
utils.save_guest_list_file(guest_df)

# check which videos have had their comments downloaded and update the CSV
utils.check_if_downloaded()
