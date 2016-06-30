"""
Some utility functions
"""

import numpy as np


def compute_stat_from_list(score_list):
    temp = np.array(score_list)
    mean = np.mean(temp)
    var = np.var(temp)
    return mean,var