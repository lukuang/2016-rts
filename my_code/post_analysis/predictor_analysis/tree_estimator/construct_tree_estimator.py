"""
construct tree estimator
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle
import numpy as np
import random
from copy import deepcopy
from scipy.stats import kendalltau


from forest import Forest

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis")
from plot_silentDay_predictor import R_DIR, Expansion,RetrievalMethod

# R_DIR = {
#     Year.y2015:{},
#     Year.y2016:{}, 
#     Year.y2011:{} 
# }

# R_DIR[Year.y2015] = {
#     Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/results",
#     Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/threshold_with_lm_difference/data/results/original"
# }

# R_DIR[Year.y2016] = {
#     Expansion.raw:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/results",
#     Expansion.static:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/results/static",
#     Expansion.dynamic:"/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/results/dynamic"
# }

# R_DIR[Year.y2011] = {
#     Expansion.raw:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/results",
#     Expansion.static:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/static/results"
# }



class EvalData(object):
    """
    base class for eval data
    """

    def __init__(self,year):
        self._year = year

        self._silent_days = {}

        if self._year == Year.y2015:
            self._prefix = "201507"
            self._eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"clusters-2015.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels.txt")
            self._topic_file = None
     
        elif self._year == Year.y2016:
            self._prefix = "201608"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"rts2016-batch-tweets2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"rts2016-batch-clusters.json")
            self._qrel_file = os.path.join(self._eval_dir,"qrels.txt")
            self._topic_file = None

        elif self._year == Year.y2011:
            self._prefix_mon = "201101"
            self._prefix_feb = "201102"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2day")
            self._cluster_file = os.path.join(self._eval_dir,"cluster.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels")
            self._topic_file = os.path.join(self._eval_dir,"topics")

        else:
            raise NotImplementedError("Year %s is not implemented!" %(self._year.name))

        self._t2day = T2Day(self._tweet2day_file,year=self._year)
        self._sema_cluster = SemaCluster(self._cluster_file,self._t2day,self._year)
        self._days = Days(self._qrel_file,self._year,self._topic_file).days
        self._qrel = Qrel(self._qrel_file,self._days,year=self._year)
        self._judged_qids = self._qrel.qids


    def ndcg(self,day,day_results):
        return self._qrel.raw_ndcg10(day.zfill(2),day_results,self._sema_cluster)

    @property
    def days(self):
        return self._days
    


def read_results(result_dir,eval_data):
    results = {}
    all_days = set()
    for qid in eval_data._days:
        for day in eval_data._days[qid]:
            all_days.add(day)

    for day in os.walk(result_dir).next()[2]:
        if day not in all_days:
            continue
        day_result_file = os.path.join(result_dir,day)
        results[day] = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in eval_data._judged_qids:
                    if qid not in results[day]:
                        results[day][qid] = []
                    docid = parts[2]
                    if (len(results[day][qid])<10):
                        results[day][qid].append(docid)


    return results

def evaluate_kt(ndcgs,predicted_values):
    real = []
    predicted = []
    for day_qid in ndcgs:
        real.append(ndcgs[day_qid])
        predicted.append(predicted_values[day_qid])
    
    # print real
    # print predicted

    return kendalltau(real,predicted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year","-y",choices=list(map(int, Year)),default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
        """)
    parser.add_argument("--tree_estimator_directory","-td",default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/predictor_data/post/tree_estimator")
    parser.add_argument("--number_of_iterations","-ni",type=int,default=50)
    parser.add_argument("--error_threshold","-et",type=int,default=50)
    parser.add_argument("--expansion","-e",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("dest_file")
    args=parser.parse_args()

    # if args.error_threshold >= 50:
    #     raise ValueError("Threshold cannot be greater than 50!")

    args.year = Year(args.year)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    args.expansion = Expansion(args.expansion)


    eval_data = EvalData(args.year)
    result_dir = R_DIR[args.year][args.expansion][args.retrieval_method]
    results = read_results(result_dir,eval_data)
    query_data_file = os.path.join(args.tree_estimator_directory,args.year.name,args.expansion.name,args.retrieval_method.name)
    query_data_file = os.path.join(query_data_file,"data")
    print "get value pair %s" %(query_data_file)
    values = json.load(open(query_data_file))

    # print results

    # create query_data
    query_data = []
    ndcgs = {}
    for qid in eval_data.days:
        for day in eval_data.days[qid]:
            day_qid = "%s_%s" %(day,qid)
            # print day_qid
            # print results[day]
            if qid in results[day]:
                day_results = {qid: results[day][qid]}
                day_query_ndcg = eval_data.ndcg(day,day_results)
            else:
                day_query_ndcg = .0
            ndcgs[day_qid] = day_query_ndcg
            
            single_data = {}
            single_data["day_qid"] = day_qid
            single_data["ndcg"] = day_query_ndcg
            single_data["values"] = values[day][qid]
            query_data.append(single_data)

    # print ndcgs

    forest = Forest(query_data,args.error_threshold,args.number_of_iterations)
    
    forest.start_training()

    predicted_values = forest.output_result(query_data)

    # print predicted_values
    kt = evaluate_kt(ndcgs,predicted_values)
    print kt
    # print "The predicted kendall's tau is %f" %(kt)

    with open(args.dest_file,'w') as f:
        cPickle.dump(forest, f, protocol=cPickle.HIGHEST_PROTOCOL)


    




if __name__=="__main__":
    main()

