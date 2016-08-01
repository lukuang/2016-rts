"""
check the performance of the threshold cutting model
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel


def load_data(training_data_dir,qrel_file,test):
    qrels = Qrel(qrel_file)
    coeff = json.load(open(os.path.join(training_data_dir,"coeff")))
    if test:
        training_qids = json.load(open(os.path.join(training_data_dir,"query_ids")))
        judged_qids = []
        for qid in qrels.qids:
            if qid not in training_qids:
                judged_qids.append(qid)
    else:
        judged_qids = qrels.qids
    return judged_qids,qrels,coeff



def get_clarity(show_clarity_file,original_query_file,
                index_dir,judged_qids,clarity_file):
    if os.path.exists(clarity_file):
        if os.stat(clarity_file).st_size !=0:
            clarities = json.load(open(clarity_file))

    else:
        clarities = {}

        for date in os.walk(index_dir).next()[1]:
            clarities[date] = {}
            date_index_dir = os.path.join(index_dir,date)
            date_clarity = compute_clarity(show_clarity_file,date_index_dir,original_query_file)
            for qid in judged_qids:
                clarities[date][qid] = date_clarity[qid]

        with open(clarity_file,'w') as f:
            f.write(json.dumps(clarities))

    return clarities


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


def generate_new_results(temp_result_dir,
                         original_result_dir,
                         clarities,coeff,judged_qids,limit,
                         use_diff):
    
    first = True
    threshold = {}
    scores = {}
    temp_result = {} 
    new_result = {}
    num_return = {}
    temp_result_file = os.path.join(temp_result_dir,'temp_result')
    new_result_file = os.path.join(temp_result_dir,'new_result')

    tf = open(temp_result_file,'w')
    nf = open(new_result_file,'w')

    for date in sorted(os.walk(original_result_dir).next()[2]):
        
        date_result_file = os.path.join(original_result_dir,date)
        print "process file %s" %date_result_file
        scores[date] = {}
        next_date = str(int(date)+1)
        threshold[next_date] = {}
        
        num_return[date] = {}

        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]
                if qid not in judged_qids:
                    continue
                else:
                    #print "good qid %s" %qid
                    #print "write %sto temp" %(line)
                    if qid not in temp_result:
                        temp_result[qid] = []
                        new_result[qid] = []
                    
                    if qid not in num_return[date]:
                        num_return[date][qid] = 0


                    docid = parts[2]
                    score = float(parts[4])
                    temp_result[qid].append(docid)
                    tf.write(line)
                    if qid not in scores[date]:
                        scores[date][qid] = []
                    
                    scores[date][qid].append(score)
                    if first:
                        if num_return[date][qid] == limit:
                            continue
                        new_result[qid].append(docid)

                        nf.write(line)
                        num_return[date][qid] += 1
                    else:
                        if score > threshold[date][qid]:
                            if num_return[date][qid]==limit:
                                continue
                            new_result[qid].append(docid)
                            nf.write(line)
                            num_return[date][qid] += 1

                        
        for qid in scores[date]:
            if use_diff:
                threshold[next_date][qid] = coeff[0]*clarities[date][qid]
                threshold[next_date][qid] += coeff[1]*scores[date][qid][0]
                #for i in range(len(scores[date][qid])):
                for i in range(len(scores[date][qid])-1):
                    try:
                        threshold[next_date][qid] += coeff[i+2]*(scores[date][qid][i+1]-scores[date][qid][i])
                    except IndexError:
                        print i,len(coeff),len(scores[date][qid])
                        sys.exit(0)
            else:   
                threshold[next_date][qid] = coeff[0]*clarities[date][qid]
                #for i in range(len(scores[date][qid])):
                for i in range(len(coeff)-1):
                    try:
                        threshold[next_date][qid] += coeff[i+1]*scores[date][qid][i]
                    except IndexError:
                        print i,len(coeff),len(scores[date][qid])
                        sys.exit(0)


        for qid in num_return[date]:
            print "return %d for %s" %(num_return[date][qid],qid)

        
        first = False

    tf.close()
    nf.close() 

    return temp_result,new_result


def get_real_perfromance(code_file,qrel_file,
                         result_file,performance_measure,
                         debug):

    real_perfromance = {}
    #script = os.path.join(code_dir,"trec_eval.8.1","trec_eval")
    #qrel_file = os.path.join(data_dir,"small_web.qrels")
    run_command = "%s -q %s %s | grep '%s '" %(code_file,qrel_file,result_file,performance_measure)
    print run_command
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

def compare_new_results(qrels,temp_result,new_result):
    
    

    new_eval = qrels.precision(new_result)
    temp_eval = qrels.precision(temp_result)
    print "the performances are:"
    print "original: %f" %temp_eval
    print "new: %f" %new_eval


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code_file",'-cf',default="/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/additional_data/trec_eval.8.1/trec_eval")
    parser.add_argument("--show_clarity_file","-scf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("--index_dir","-id",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--clarity_file","-clf")
    #parser.add_argument("--debug","-de",action='store_true')
    parser.add_argument("--limit","-lm",type=int,default=10)
    parser.add_argument("--use_diff","-ud",action="store_true")
    parser.add_argument("--test","-t",action='store_true')
    #parser.add_argument("--performance_measure","-pms",default="P100")
    parser.add_argument("original_result_dir")
    parser.add_argument("original_query_file")
    parser.add_argument("training_data_dir")
    parser.add_argument("temp_result_dir")
    args=parser.parse_args()

    print "load necessary data"
    judged_qids,qrels,coeff = load_data(args.training_data_dir,args.qrel_file,args.test)
    print judged_qids
    print "compute clarity scores for all queries/dates"
    clarities = get_clarity(args.show_clarity_file,
                            args.original_query_file,
                            args.index_dir,judged_qids,
                            args.clarity_file)

    print "generate result files"
    temp_result,new_result = generate_new_results(
                                args.temp_result_dir,
                                args.original_result_dir,
                                clarities,coeff,judged_qids,args.limit,
                                args.use_diff)

    print "compare performances"
    compare_new_results(qrels,temp_result,new_result)
    
    #real_perfromance = get_real_perfromance(args.code_file,args.qrel_file,args.temp_result_file,args.performance_measure,args.debug)


if __name__=="__main__":
    main()

