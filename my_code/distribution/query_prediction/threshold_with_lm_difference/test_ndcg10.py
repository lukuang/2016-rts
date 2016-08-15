"""
test the computation of ndcg10
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.misc import Stopword_Handler

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster



def load_result(result_file):
    results = {}
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            day_string = parts[0]
            qid = parts[1]
            tid = parts[3]
            m = re.search("201507(\d+)",day_string)
            day = m.group(1)
            if day not in results:
                results[day] = {}
            if qid not in results[day]:
                results[day][qid] = []
            results[day][qid].append(tid)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_file")
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
 
    args=parser.parse_args()

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)
    qrel = Qrel(args.qrel_file)
    results = load_result(args.result_file)
    ndcg10 = qrel.ndcg10(results,sema_cluster)
    print "%.04f" %ndcg10

if __name__=="__main__":
    main()

