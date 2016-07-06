"""
various way of evaluating the SD's of a ranking
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess
from scipy.stats import pearsonr, kendalltau


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

def to_ranking(ap_dict):
    ap_ranking = {}
    sorted_ap = sorted(ap_dict.items(),key=lambda x:x[1], reverse=True)
    i=1
    for qid,score in sorted_ap:
        ap_ranking[qid] = i
        i+=1
    return ap_ranking

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

def get_aupr(aupr_file):
    return json.load(open(aupr_file))


def get_kendall_tau(estimated_aupr,real_ap,method):
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
    parser.add_argument("aupr_file")
    parser.add_argument("data_dir")
    parser.add_argument("result_file")
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

    estimated_aupr = get_aupr(args.aupr_file)
    real_ap = get_real_ap(args.data_dir,args.result_file)
    qids = real_ap.keys()
    real_ap_list = to_list(qids,real_ap)
    print real_ap_list
    print "-"*20
    print method_name + ":"
    for lambda_choice in estimated_aupr:

        estimated = to_list(qids,estimated_aupr[lambda_choice])
        print estimated
        eval_value = method(real_ap_list, estimated)
        print "\tFor %s: %f" %(lambda_choice,eval_value)
    print "-"*20

if __name__=="__main__":
    main()

