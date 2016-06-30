"""
estimate score distribution from a ranking list
and compare estimated-ap to real ap
"""
from __future__ import division
import os
import json
import sys
import re
import argparse
import codecs
import math
import subprocess
from scipy.stats import kendalltau
from lxml import etree
from myUtility.misc import Stopword_Handler

from data import *
from sd import LognormalSD,GammaSD



def process_query(original_query_file,stopword_handler):
    queries = {}
    content = ""
    with open(original_query_file) as f:
        content = f.read()
    root = etree.fromstring(content)
    for child in root.iter("query"):
        qid = child.find("number").text
        text = child.find("text").text.lower()
        text = stopword_handler.remove_stopwords(text)
        words = re.findall("\w+",text)
        word_set = set(words)
        queries[qid] = list(word_set)

    return queries 


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

def get_linear_correlations(estimated_aupr,real_ap):
    qids = real_ap.keys()
    real_ap_list = to_list(qids,real_ap)
    print "-"*20
    print "Kendall's tau:"
    for lambda_choice in estimated_aupr:
        estimated = to_list(qids,estimated_aupr[lambda_choice])
        tau, p_value = kendalltau(real_ap_list, estimated)
        print "\tFor %s, tau is %f" %(lambda_choice,tau)
    print "-"*20

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("original_query_file")
    parser.add_argument("result_file")
    parser.add_argument("--method","-m",type=int,choices=[0,1],default=0)
    #parser.add_argument("qrel_file")
    args = parser.parse_args()

    all_methods = ["gamma","lognormal"]
    method = all_methods[args.method]
    
    #qrel = Qrel(args.qrel_file)
    stat_dir = os.path.join(args.data_dir,"stat")
    index_stats = IndexStats(stat_dir)
    run = Run(args.result_file)
    real_ap = get_real_ap(args.data_dir,args.result_file)
    print real_ap

    stopword_handler = Stopword_Handler()
    long_queries = process_query(args.original_query_file,stopword_handler)
    

    if method == "gamma":
        sd = GammaSD(run)
    else:
        sd = LognormalSD(run)

    sd.estimate_distribution(index_stats,long_queries)
    sd.predict_aupr()
    sd.show_aupr()
    estimated_aupr = sd.aupr()
    get_linear_correlations(estimated_aupr,real_ap)



if __name__=="__main__":
    main()

