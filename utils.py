import pandas as pd
import os
import string


# define some file and directory names
guest_list_file = './guest_list.csv'
comment_dir = './comments'
data_dir = './data'
youtube_api_key_file = './youtube_api_key.txt'
perspective_api_key_file = './perspective_api_key.txt'
perspective_api_key_file_2 = './perspective_api_key_2.txt'


def load_guest_list_file(file=guest_list_file, apply_filters=False):
    """
    Read the guest list CSV file into a pandas dataframe.

    :param file: file path for guest list CSV file
    :param apply_filters: if True, remove unscraped and special videos (holiday special, Colbert)
    :return: pandas dataframe
    """
    df = pd.read_csv(file).fillna('')
    
    if apply_filters:
        df = df[(df['video_id'] != '') &
                (df['done'].isin([1, '1'])) &
                (~df['guest'].isin(['holiday special', 'Stephen Colbert']))
               ]
    
    return df


def save_guest_list_file(df, file=guest_list_file):
    """
    Overwrite the guest list CSV file with the contents of a pandas dataframe.

    :param df: pandas dataframe to save
    :param file: file path for guest list CSV file
    """
    df.to_csv(file, index=False)


def check_if_downloaded(file=guest_list_file, comment_dir=comment_dir):
    """
    Loop through all rows of the log CSV file check if the comments have been scraped, and update the CSV file. Also
    remove duplicate versions of files before checking.

    :param file: path of CSV file with guest and video data
    :param comment_dir: directory containing downloaded comments
    """
    # read the CSV
    guest_df = pd.read_csv(file).fillna('')

    # remove duplicate files
    remove_duplicate_files(comment_dir)

    # check if scraping is done (if file exists in comments directory)
    for i, row in guest_df.iterrows():
        if os.path.isfile(os.path.join(comment_dir, 'comments-' + row['video_id'] + '.json')):
            guest_df.loc[i, 'done'] = 1
        else:
            guest_df.loc[i, 'done'] = ''

    # write the updated CSV
    save_guest_list_file(guest_df, file)


def remove_duplicate_files(comment_dir=comment_dir):
    """
    If 'file.json' already exists, Chrome will download it as 'file (1).json'. This function will loop through all
    files with '(#)' in the file name and overwrite the original file. It's not perfect but it generally will keep the
    most recent file.

    :param dir: directory containing the downloaded .json files
    """
    # find the files that are duplicates
    dup_files = [file for file in os.listdir(comment_dir) if ' (' in file]

    # sort so the numbers are in ascending order -- e.g., (1) comes before (2), and so on (this fails starting with 10)
    dup_files.sort()

    # loop through duplicate files in order and rename to the original
    for file in dup_files:
        os.rename(os.path.join(comment_dir, file),
                  os.path.join(comment_dir, file.split(' (')[0] + file.split(')')[-1]))


def scrub_names(df, comments_col='comments', name_token='<name>'):
    """
    For each guest, replace the guest's name with a generic '<name>' token. Tokens to replace for each guest are
    specfied in the 'name_filter' column of the input CSV file.

    :param df: guest dataframe with a column containing concatenated comments (a string)
    :return: same dataframe with names substituted in the comments
    """
    if comments_col not in df:
        raise KeyError("Dataframe must have a 'comments' column")

    for i, row in df.iterrows():
        # look for tokens specified in CSV, plus those tokens including some basic punctuation
        raw_names = [row['guest'].lower()] + row['name_filter'].split(', ')
        names = raw_names + [x + "'s" for x in raw_names]
        names += [x + y for y in string.punctuation for x in raw_names]
        names += [y + x for y in string.punctuation for x in raw_names]

        comments = row[comments_col]
        scrubbed_comments = comments.split(' ')
        scrubbed_comments = [name_token if x.lower() in names else x for x in scrubbed_comments]
        scrubbed_comments = ' '.join(scrubbed_comments)

        df.loc[i, comments_col] = scrubbed_comments

    return df
