"""
Some utility functions
"""

import numpy as np
import re
import math

def compute_idf_avg(stats,query):
    idf_avg = .0
    for w in query:
        try:
            idf_avg += math.log( stats.idf[w] )
        except ValueError:
            idf_avg += 0

    idf_avg /= len(query)
    return idf_avg


def compute_scq_avg(stats,query):
    scq_avg = .0
    for w in query:
        if stats.cf[w] == 0:
            scq_avg += 1
        else:
            scq_avg += 1+ math.log(stats.cf[w])*math.log( 1 + stats.idf[w] )

    scq_avg /= len(query)
    return scq_avg

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

def get_mb_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    in_title = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\w+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>",line)
                if mt is not None:
                    in_title = True
                    continue
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
            elif in_title:
                title_queries[qid] = line+"\n"
                in_title = False
    return title_queries,desc_queries