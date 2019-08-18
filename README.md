# Hot Ones YouTube Comment Analysis

This repository contains code used to analyze YouTube comments on *Hot Ones* YouTube videos. I looked 
for evidence of sexism in comments on videos featuring women.  

## Results

I think there is moderate evidence of sexism. I wrote a summary of my findings in a post on Medium: 
https://towardsdatascience.com/are-hot-ones-viewers-sexist-2a1373b6b69

The `data_for_writeup.ipynb` Jupyter notebook contains most of the data and visualizations from the
Medium post.

## Repository contents

The `guest_list.csv` file is where most of the data is stored and updated. I started by manually adding
the guest names for each *Hot Ones* episode and a few additional columns. The `guest_list_starter.csv` 
file shows what the file looked like before scraping comments and computing metrics.

The five numbered Python scripts pull the data used for analysis:
* `00_get_video_ids.py` gets YouTube video IDs and URLs for each episode and adds them to the CSV file.
* `01_scrape_comments.py` downloads the comments for each video and stores them in the `comments/` directory
(separate JSON file for each video).
* `02_compute_sentiments.py` adds VADER sentiment score to each comment in the JSON files and adds some 
summary metrics to each row of the CSV file.
* `03_get_perspective_scores.py` uses the Google Perspective API to add toxicity scores to each comment in
the JSON files and some summary metrics to the CSV file.
* `04_feature_analysis_gender.py` runs a Bayesian classification model and writes the feature importance 
results to the `data/` directory

The `utils.py`, `models.py`, and `nlp_utils.py` files define some functions and classes that are used by the 
other Python scripts.
