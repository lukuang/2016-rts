"""
for naacl 2018 submission. Generate result and apply silent day detection
using model trained on MB2011&2012
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
import subprocess
import requests
import cPickle
from datetime import timedelta
import logging
import logging.handlers


from myUtility.misc import gene_indri_index_para_file

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/2017/scenario_a")
from run import get_file_list,get_predictor_values,Models,Detector,separate_qids

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis")
from predictor import *
from plot_silentDay_predictor import *


def build_index(index_dir,para_dir,text_dir,date):
    file_list = get_file_list(text_dir,date)
    
    index_para_file = os.path.join(para_dir,date)
    index_path = os.path.join(index_dir,date)

    gene_indri_index_para_file(file_list,index_para_file,
                    index_path)

    os.system("IndriBuildIndex %s" %index_para_file)

def run_single_query(query_file,result_file):
    results = {}
    print "run query file %s" %(query_file)
    p = subprocess.Popen(["IndriRunQuery", query_file],  stdout=subprocess.PIPE)
    output = p.communicate()[0]

    # write to result files
    with open(result_file,"w") as of:
        of.write(output)

    sentences  =  output.split("\n")
    for s in sentences:
        if len(s)==0:
            continue
        parts = s.strip().split()
        qid = parts[0]
        tid = parts[2]
        if qid not in results:
            results[qid] = []
        results[qid].append( s )

    return results

def run_query(date,query_dir,result_dir):
    
    raw_query_file = os.path.join(query_dir,"raw_%s" %(date))
    raw_result_file = os.path.join(result_dir,"raw",date)
    raw_results = run_single_query(raw_query_file,raw_result_file)
    return raw_results


def generate_output(raw_results,date,decisions,dest_dir):
    
    dest_file = os.path.join(dest_dir,date)
    tids = set()

    silent_count = 0
    with open(dest_file,"w") as f:
        for qid in raw_results:
            if decisions[qid]==0:
                for line in raw_results[qid]:
                    f.write(line+"\n")

                    # prepare tids
                    parts = line.strip().split()
                    tid = parts[2]
                    tids.add(tid)
            else:
                silent_count += 1
    print "%d out of %d queries are silent" %(silent_count,len(raw_results))

    return tids


def get_text_for_tid(index_dir,tid):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tid)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None


def get_text(index_dir,date,tids,all_text):
    index_path = os.path.join(index_dir,date)
    for tid in tids:
        if tid not in all_text:
            single_text = get_text_for_tid(index_path,tid)
            all_text[tid] = single_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2017-rts/data/index")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2017-rts/data/queries")
    parser.add_argument("--text_dir","-tr",default="/infolab/headnode2/lukuang/2017-rts/data/raw/first/text")
    parser.add_argument("--result_dir","-rr",default="/infolab/headnode2/lukuang/2017-rts/data/result")
    parser.add_argument("--para_dir","-pr",default="/infolab/headnode2/lukuang/2017-rts/data/para")
    parser.add_argument("--clarity_query_dir","-cqr",default="/infolab/headnode2/lukuang/2017-rts/data/clarity_queries")
    parser.add_argument("--model_dir","-mr",default="/infolab/headnode2/lukuang/2017-rts/data/models")
    parser.add_argument("--dest_dir","-dr",default="/infolab/headnode2/lukuang/2017-rts/data/raw_result_with_sd")
    parser.add_argument("--all_text_file","-atf",default="/infolab/headnode2/lukuang/2017-rts/code/2017/scenario_b/2017_all_text")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2017-rts/data/communication")
    args=parser.parse_args()

    print "load all text"
    all_text = {}
    if os.path.exists(args.all_text_file):
        all_text = json.load(open(args.all_text_file))

    topic_file = os.path.join(args.communication_dir,"topics")
    single_term_qids, multi_term_qids = separate_qids(topic_file) 
    all_qids = single_term_qids + multi_term_qids

    single_term_with_result_feature_list = [
        PredictorName.average_idf, 
        PredictorName.scq, 
        PredictorName.dev
    ]


    multi_term_feature_list = [
        PredictorName.coherence_average,
        PredictorName.coherence_binary,
        PredictorName.coherence_max,
        PredictorName.pwig
    ]

    print "load pre-trained models for silent day detection"
    with_result_models = Models(os.path.join(args.model_dir,"with"))

    with_result_detector = Detector(with_result_models,single_term_qids,
                                    single_term_with_result_feature_list,multi_term_qids,
                                    multi_term_feature_list)


    days = ["29","30","31","1","2","3","4","5"]

    for date in days:

        # print "build index"
        # build_index(args.index_dir,args.para_dir,args.text_dir,date)
        
        print "run queries"
        raw_results = run_query(date,args.query_dir,args.result_dir)

        print "get predictor values"
        result_dir = os.path.join(args.result_dir,"raw")
        single_term_with_result_predictor_values = get_predictor_values(date,single_term_qids,
                                                            single_term_with_result_feature_list,
                                                            args.clarity_query_dir,
                                                            result_dir,args.index_dir)
        
        muti_term_predictor_values = get_predictor_values(date,multi_term_qids,
                                                            multi_term_feature_list,
                                                            args.clarity_query_dir,
                                                            result_dir,args.index_dir)

        print "make silent day decisions"
        with_result_decisions = with_result_detector.make_descision(
                                        single_term_with_result_predictor_values,
                                        muti_term_predictor_values)   
             
        print "generate output"
        tids = generate_output(raw_results,date,with_result_decisions,args.dest_dir)

        print "get text"
        get_text(args.index_dir,date,tids,all_text)

    print "store text"
    with codecs.open(args.all_text_file,"w",'utf-8') as f:
        f.write(json.dumps(all_text))

if __name__=="__main__":
    main()

