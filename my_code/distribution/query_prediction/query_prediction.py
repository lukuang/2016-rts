"""
esitmate average idf baseline
"""

import os
import json
import sys
import re
import math
import argparse
import codecs
import subprocess
from scipy.stats import pearsonr, kendalltau
import matplotlib 
matplotlib.use('agg') 
import matplotlib.pyplot as plt



from myUtility.misc import Stopword_Handler

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/distribution")
from misc import compute_stat_from_list,compute_idf_avg,compute_scq_avg  
from data import *

def read_simple_queries(original_query_file,stopword_handler=None):
    simple_queries = {}
    content = ""
    with open(original_query_file) as f:
        for line in f:
            line = line.rstrip()
            if line:
                m = re.search("^(.+?):(.+)$",line)
                if m:
                    qid = m.group(1)
                    text = m.group(2)
                    if stopword_handler is not None:
                        text = stopword_handler.remove_stopwords(text)
                    words = re.findall("\w+",text)
                    word_set = set(words)
                    simple_queries[qid] = list(word_set)

    return simple_queries


def get_real_perfromance(code_file,qrel_file,result_file,performance_measure,debug):
    real_perfromance = {}
    #script = os.path.join(code_dir,"trec_eval.8.1","trec_eval")
    #qrel_file = os.path.join(data_dir,"small_web.qrels")
    run_command = "%s -q %s %s | grep '%s '" %(code_file,qrel_file,result_file,performance_measure)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    while True:
        line = p.stdout.readline()
        if debug:
            print line
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[1]
            if qid!="all":
                real_perfromance[qid] = float(parts[2])

        else:
            break
    return real_perfromance



def compute_clarity(show_clarity_file,index_dir,original_query_file):
    clarity = {}
    run_command = "%s %s %s" %(show_clarity_file,index_dir,original_query_file)
    #print "command being run:\n%s" %(run_command)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            clarity[qid] = float(parts[1])
            

        else:
            break 
    return clarity
    
def compute_std(result_file):
    stds = {}
    scores = {}
    with open(result_file) as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            parts = line.split()
            qid = parts[0]
            score = float(parts[4])
            if qid not in scores:
                scores[qid] = []
            scores[qid].append(score)
    for qid in scores:
        mean,var = compute_stat_from_list(scores[qid])
        std = math.sqrt(var)
        stds[qid] = std

    return stds

def compute_ndev(result_file):
    ndev = {}
    scores = {}

    with open(result_file) as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            parts = line.split()
            qid = parts[0]
            score = float(parts[4])
            if qid not in scores:
                scores[qid] = []
            scores[qid].append(score)

    for qid in scores:
        max_score = scores[qid][0]
        stop_score = max_score/2.0
        boundary = 0
        for score in scores[qid]:
            if score < stop_score:
                break
            else:
                boundary += 1
        print "boundary is: %d" %boundary
        mean,var = compute_stat_from_list(scores[qid][:boundary])
        std = math.sqrt(var)
        ndev[qid] = std

    return ndev


def compute_prediction_measure(index_stats,simple_queries,show_clarity_file,index_dir,original_query_file,result_file,predict_method):
    if predict_method == 0:
        #use average idf
        idf_avg = {}

        for qid in simple_queries:
            idf_avg[qid] = compute_idf_avg(index_stats,simple_queries[qid])
        return idf_avg
    elif predict_method == 1:
        return compute_clarity(show_clarity_file,index_dir,original_query_file)

    elif predict_method == 2:
        return compute_std(result_file)

    elif predict_method == 3:
        return compute_ndev(result_file)
    else:
        raise NotImplementedError("the query prediction method with id %d is not implemented!" %predict_method)

def to_list(qids,ap_list):
    return [ap_list[qid] for qid in qids]


def kendal_ltau(estimated_aupr,real_ap_list):
    tau, p_value = kendalltau(estimated_aupr, real_ap_list)
    return tau

def pearson_r(estimated_aupr,real_ap_list):
    r,p_value = pearsonr(estimated_aupr, real_ap_list)
    return r

def rmse(estimated_aupr,real_ap_list):
    raise NotImplementedError("rmse not implemented!")

def plot_corr(all_performance,all_estimates,plot_dir,prediction_method,qids):
    """Plot the correlation between the real performance and the
    prediction
    """
    for date in all_performance:
        dest_file = os.path.join(plot_dir,date)
        queries = range(len(all_performance[date]))
        plt.plot(queries, all_performance[date], 'ro',queries,all_estimates[date],'bo')
        plt.xticks(queries, qids, rotation='vertical')
        plt.title("Performance %s Correlation" %(prediction_method))
        plt.xlabel("Queries")
        plt.ylabel("Performance")
        plt.legend()
        plt.savefig("%s.png" %(dest_file))
        plt.clf()



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stat_dir")
    parser.add_argument("--code_file",'-cf',default="/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/additional_data/trec_eval.8.1/trec_eval")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--show_clarity_file","-scf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("--index_dir","-id",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual")
    parser.add_argument("original_query_file")
    parser.add_argument("result_dir")
    parser.add_argument("--no_stopwords","-ns",action='store_true')
    parser.add_argument("--debug","-de",action='store_true')
    parser.add_argument("--performance_measure","-pms")
    parser.add_argument("--method","-m",type=int,choices=[0,1,2],default=0)
    parser.add_argument("--predict_method","-pmt",type=int,choices=[0,1,2,3],default=0,
            help="""
                choose query predict method:
                    0: average_idf
                    1: clarity
                    2: std
                    3: NDEV
            """)
    parser.add_argument("--plot_dir","-pr")
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

    eval_value = 0.0
    all_performance = {}
    all_estimates = {}
    qids = []
    for date in range(20,30):
        date = str(date)
        stat_dir = os.path.join(args.stat_dir,date)
        index_stats = IndexStats(stat_dir)
        index_dir = os.path.join(args.index_dir,date)
        result_file = os.path.join(args.result_dir,date)
        run = Run(result_file)

        if args.debug:
            print "result file %s" %result_file
            print "stat dir %s" %stat_dir
            print "index dir %s" %index_dir

        real_perfromance = get_real_perfromance(args.code_file,args.qrel_file,result_file,args.performance_measure,args.debug)
        if not qids:
            qids = real_perfromance.keys()
        real_perfromance_list = to_list(qids,real_perfromance)
        if args.no_stopwords:

            stopword_handler = Stopword_Handler()
            simple_queries = read_simple_queries(args.original_query_file,stopword_handler)
        else:
            simple_queries = read_simple_queries(args.original_query_file)

        
        estimated_value = compute_prediction_measure(
                                    index_stats,simple_queries,
                                    args.show_clarity_file,index_dir,
                                    args.original_query_file,
                                    result_file,
                                    args.predict_method)
        #estimated_value[qid] = compute_idf_avg(index_stats,simple_queries[qid])
    

        estimated = to_list(qids,estimated_value)
        all_estimates[date] = estimated
        all_performance[date] = real_perfromance_list
        eval_value += method(real_perfromance_list, estimated)/10.0

    print "\tFor %s: %f" %(method_name,eval_value)

    if args.plot_dir:
        print "plot!"
        all_prediction_methods = {
                    0: 'average_idf',
                    1: 'clarity',
                    2: 'std',
                    3: 'NDEV'
                }
        prediction_method = all_prediction_methods[args.predict_method]
        plot_corr(all_performance,all_estimates,args.plot_dir,prediction_method,qids)



if __name__=="__main__":
    main()

