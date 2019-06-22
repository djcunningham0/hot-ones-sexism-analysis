import pandas as pd
import os


# define some file and directory names
guest_list_file = './guest_list.csv'
comment_dir = './comments'
youtube_api_key_file = './youtube_api_key.txt'
perspective_api_key_file = './perspective_api_key.txt'
perspective_api_key_file_2 = './perspective_api_key_2.txt'


def load_guest_list_file(file=guest_list_file):
    """
    Read the guest list CSV file into a pandas dataframe.

    :param file: file path for guest list CSV file
    :return: pandas dataframe
    """
    return pd.read_csv(file).fillna('')


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
