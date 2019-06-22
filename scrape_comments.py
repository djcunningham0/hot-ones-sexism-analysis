from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException
import time
import os
import utils  # utils.py file


## Parameters
verbose = True  # set to True to output progress messages, False to only show main messages

# update CSV with the videos that are done so we know which URLs to scrape
utils.check_if_downloaded()

# read the CSV
guest_df = utils.load_guest_list_file()

# quit if there aren't any that need scraping
if guest_df[(guest_df['done'] != 1) & (guest_df['done'] != '1') & (guest_df['video_url'] != '')].shape[0] == 0:
    print('All videos have had comments scraped.')
    raise SystemExit()

# set Chrome download directory
chrome_options = webdriver.ChromeOptions()
prefs = {'download.default_directory': os.path.abspath(utils.comment_dir)}
chrome_options.add_experimental_option('prefs', prefs)

# start Chrome driver
print("Starting driver.")
driver = webdriver.Chrome('/usr/local/bin/chromedriver', chrome_options=chrome_options)


# define function for downloading the scraped comments
def click_download(driver, retry_rate=10, max_minutes=120, current_wait=0, verbose=False):
    """
    Recursive function for attempting to download scraped comments. Attempt to download the results. If scraping is
    not complete, wait the specified number of seconds and try again. The comm

    :param driver: Chrome driver
    :param retry_rate: number of seconds to wait between attempts to click the download button
    :param max_minutes: maximum number of minutes to spend on a single video before aborting
    :param current_wait: number of seconds that have elapsed so far
    :param verbose: True to output progress messages

    :return: comment count string if downloaded successfully; None otherwise
    """
    # if it's taken too long, return -1 so we know the file wasn't downloaded
    if current_wait / 60 > max_minutes:
        return None

    # otherwise try downloading and retry if it fails
    else:
        # find the download button, save JSON button, and progress bar
        download_button = driver.find_element_by_id('save-dropdown')
        save_json_button = driver.find_element_by_id('save-json')
        progress_bar = driver.find_element_by_css_selector("div[role = 'progressbar']")

        # attempt to click download button; return comment count if successful
        try:
            download_button.click()
            save_json_button.click()
            time.sleep(30)  # allow some time to make sure the file downloads

            # return comment count (format = '#### comments')
            comment_count = driver.find_element_by_class_name('comment-count')
            return comment_count.text

        # if download button isn't visible yet, wait and try again
        except ElementNotVisibleException:
            if verbose:
                msg = f'Download not ready. {current_wait} seconds elapsed.'
                msg += f' Retrying in {retry_rate} seconds. Progress: {progress_bar.text}'
                print(msg)

            # update elapsed wait time, wait, and then try again
            current_wait += retry_rate
            time.sleep(retry_rate)
            return click_download(driver, retry_rate, max_minutes, current_wait, verbose)


# loop through all videos and scrape the comments
for i, row in guest_df.iterrows():
    # skip if comments are already scraped or we don't have a video URL
    if row['done'] == 1 or row['video_url'] == '':
        continue

    print(f"Starting {row['guest']}: {row['video_url']}")

    # go to comment scraper web app
    driver.get('http://ytcomments.klostermann.ca')

    # enter the video URL into the search box and click the search button
    input_box = driver.find_element_by_id('yt-url')
    input_box.send_keys(f"{row['video_url']}")
    search_button = driver.find_element_by_id('scrape-btn')
    search_button.click()

    # continue to attempt to download the results and report the outcome when it succeeds or times out
    result = click_download(driver, verbose=verbose)
    if result is None:
        print(f"Timed out on guest {row['guest']}")
    else:
        print(f"Finished {row['guest']}. {result}.")

print("Done with all URLs. Closing driver.")
driver.close()

# update CSV with the videos that are done after scraping so we update the results
utils.check_if_downloaded()
