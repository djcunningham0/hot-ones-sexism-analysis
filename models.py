import numpy as np
import pandas as pd
from scipy.sparse import issparse


def multinomial_dirichlet_model(counts, feature_names=None, prior='informative', alpha=1):
    """
    Implementation of the multinomial likelihood/Dirichlet prior model from the "Fightin Words" paper
    by Monroe et al. The model identifies difference in token (e.g., word or n-gram) usage by two
    different groups.
    
    Link to paper: http://languagelog.ldc.upenn.edu/myl/Monroe.pdf

    The Dirichlet prior can be informative or uniform, as described in the Monroe paper. If informative,
    the token counts across groups are used to set the prior weights. Otherwise, a uniform weights are used.
    The 'alpha' parameter controls the strength of the prior.

    Returns a pandas dataframe with log odds ratio, variance, and z-scores for each token. Positive z-score
    means the token is more likely to be used by group 0 and negative z-score means the word is more likely
    to be used by group 1.

    :param counts: 2xn numpy array of word counts: row 0 has counts for group 0, row 1 has counts for group 1
    :param feature_names: feature names (e.g., words or n-grams) corresponding to columns of counts matrix
    :param prior: 'informative' or 'uniform'
    :param alpha: strength of prior (default = 1)

    :return: a pandas dataframe with z-scores and other stats for each token
    """
    # if sparse matrix, convert to dense so later calculations result in numpy arrays rather than matrices
    if issparse(counts):
        counts = counts.toarray()

    # counts must be numpy array with two rows
    if not isinstance(counts, np.ndarray):
        raise TypeError('counts must by numpy array')
    if counts.shape[0] != 2:
        raise ValueError('counts must have two rows -- one for each set being compared')

    # set up prior
    if prior == 'informative':
        prior = alpha * counts.sum(0) / counts.sum()
    elif prior == 'uniform':
        prior = np.array([alpha for _ in range(counts.shape[1])])
    else:
        raise ValueError("prior must be 'informative' or 'uniform'")

    # compute log odds ratio, variance, and z_scores
    log_odds_ratio = (
        np.log(counts[0] + prior) -
        np.log(sum(counts[0]) + sum(prior) - counts[0] - prior) -
        np.log(counts[1] + prior) +
        np.log(sum(counts[1]) + sum(prior) - counts[1] - prior)
    )

    variance = (
        1 / (counts[0] + prior) +
        1 / (sum(counts[0]) + sum(prior) - counts[0] - prior) +
        1 / (counts[1] + prior) +
        1 / (sum(counts[1]) + sum(prior) - counts[1] - prior)
    )

    z_scores = log_odds_ratio / np.sqrt(variance)

    # put everything into a dataframe for easy use later
    if feature_names is None:
        feature_names = range(counts.shape[1])
    df = pd.DataFrame({
        'token': feature_names,
        'feature_index': range(counts.shape[1]),
        'count_0': counts[0],
        'count_1': counts[1],
        'freq_0': counts[0] / counts[0].sum(),
        'freq_1': counts[1] / counts[1].sum(),
        'log_odds_ratio': log_odds_ratio,
        'variance': variance,
        'z_score': z_scores
    })

    return df.sort_values('z_score').reset_index(drop=True)
