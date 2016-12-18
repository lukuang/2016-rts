"""
test whether can compute day cluster recall correctly
"""

import os
import json
import sys
import re
import argparse
import codecs

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster



def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")

    #parser.add_argument("result_file")
    args=parser.parse_args()

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)
    qrel = Qrel(args.qrel_file)

    date = '20'
    results = {
        "MB324":["623014387402543108","622951330240266240","622951330240266240","623026064340742144","623786646845161472","623941353752383490"]
        } 
    for i in range(len(results["MB324"])):
        print sema_cluster._day_cluster[date]["MB324"]
        sub_result = {"MB324":results["MB324"][:i+1]}
        recall = sema_cluster.day_cluster_recall(sub_result,date)
        print "now recall is %f" %recall
        ndcg10 = qrel.day_dcg10_no_pre(date,sub_result,sema_cluster)
        print "ndcg10 is %f" %(ndcg10)
        ndcg10 = qrel.raw_ndcg10(date,sub_result,sema_cluster)
        print "ndcg10 is %f" %(ndcg10)


if __name__=="__main__":
    main()

