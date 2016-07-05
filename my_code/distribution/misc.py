"""
Some utility functions
"""

import numpy as np
import re

def compute_stat_from_list(score_list):
    temp = np.array(score_list)
    mean = np.mean(temp)
    var = np.var(temp)
    return mean,var

def get_wt2g_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\d+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>(.+)",line)
                if mt is not None:
                    title_queries[qid] = mt.group(1)
                else:
                    md = re.search("<desc> Description:",line)
                    if md is not None:
                        in_desc = True
                        continue
                    else:
                        ma = re.search("<narr> Narrative:",line)
                        if ma is not None:
                            in_desc = False
            
            if in_desc:
                desc_queries[qid] += line+"\n"
    return title_queries,desc_queries