"""
esitmate average idf baseline
"""

import os
import json
import sys
import re
import argparse
import codecs


from myUtility.misc import Stopword_Handler
from misc import compute_stat_from_list,compute_idf_avg,compute_scq_avg  
from data import *
from estimate_sd import process_query


def get_real_ap(data_dir,result_file):
    real_ap = {}
    script = os.path.join(data_dir,"trec_eval.8.1","trec_eval")
    qrel_file = os.path.join(data_dir,"small_web.qrels")
    run_command = "%s -q %s %s | grep map" %(script,qrel_file,result_file)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[1]
            if qid!="all":
                real_ap[qid] = float(parts[2])

        else:
            break
    return real_ap

def to_list(qids,ap_list):
    return [ap_list[qid] for qid in qids]


def kendal_ltau(estimated_aupr,real_ap_list):
    tau, p_value = kendalltau(estimated_aupr, real_ap_list)
    return tau

def pearson_r(estimated_aupr,real_ap_list):
    r,p_value = pearsonr(estimated_aupr, real_ap_list)
    return r

def rmse(estimated_aupr,real_ap_list):
    raise RuntimeError("not implemented!")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("original_query_file")
    parser.add_argument("result_file")
    parser.add_argument("--no_stopwords","-ns",action='store_true')
    parser.add_argument("--method","-m",type=int,choices=[0,1,2],default=0)
    args=parser.parse_args()

    method_names = [
        "Kendall's tau",
        "Pearsonr",
        "rmse"
    ]

    methods = {
        "Kendall's tau": kendal_ltau,
        "Pearsonr": pearson_r,
        "rmse":rmse
    }


    method_name = method_names[args.method]
    method =  methods[method_name]

    stat_dir = os.path.join(args.data_dir,"stat")
    index_stats = IndexStats(stat_dir)
    run = Run(args.result_file)
    real_ap = get_real_ap(args.data_dir,args.result_file)
    qids = real_ap.keys()
    real_ap_list = to_list(qids,real_ap)

    if args.no_stopwords:

        stopword_handler = Stopword_Handler()
        long_queries = process_query(args.original_query_file,stopword_handler)
    else:
        long_queries = process_query(args.original_query_file)

    average_idf = {}
    for qid in long_queries:
        average_idf[qid] = compute_idf_avg(index_stats,long_queries[qid])
    

    estimated = to_list(qids,average_idf)
    eval_value = method(real_ap_list, estimated)
    print "\tFor %s: %f" %(method_name,eval_value)




if __name__=="__main__":
    main()

