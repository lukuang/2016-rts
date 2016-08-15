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
import cPickle

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster


def load_data(training_data_dir,qrel_file,test_qid_file,eval_topics):
    qrels = Qrel(qrel_file)
    coeff = json.load(open(os.path.join(training_data_dir,"coeff")))
    if test_qid_file:
        training_qids = json.load(open(test_qid_file))
        judged_qids = []
        for qid in qrels.qids:
            if qid not in training_qids:
                if eval_topics:
                    if qid in eval_topics:
                        judged_qids.append(qid)
                else:
                    judged_qids.append(qid)
    else:
        if eval_topics:
            judged_qids = eval_topics
        else:
            judged_qids = qrels.qids
    regr_file = os.path.join(training_data_dir,"regr")        
    f = open(regr_file, 'rb')
    regr = cPickle.load(f)
    f.close()

    return judged_qids,qrels,coeff,regr



def get_clarity(clarity_dir,judged_qids):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in judged_qids:
            clarities[date][qid] = date_clarity[qid]

    return clarities





def generate_new_results(test_result_dir,
                         original_result_dir,
                         clarities,coeff,judged_qids,limit,
                         difference_features,days,prefix,regr=None):
    
    threshold = {}
    scores = {}
    num_return = {}
    processed_original_result_file = os.path.join(test_result_dir,'original_result')
    new_result_file = os.path.join(test_result_dir,'new_result')

    prf = open(processed_original_result_file,'w')
    nf = open(new_result_file,'w')

    for date in days:
        
        date_result_file = os.path.join(original_result_dir,date)
        print "process file %s" %date_result_file
        scores[date] = {}
        next_date = str(int(date)+1)
        threshold[date] = {}
        
        num_return[date] = {}

        
        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]
                if qid not in judged_qids:
                    continue
                else:
                   

                    score = float(parts[4])
                     
                    if qid not in scores[date]:
                        scores[date][qid] = [] 
                    scores[date][qid].append(score)

        for qid in scores[date]:
            if regr:
                single_feature_vector = []
                single_feature_vector = [clarities[date][qid],scores[date][qid][0]]
                #for i in range(len(scores[date][qid])):
                for i in range(limit-1):
                    try:
                        single_feature_vector.append(scores[date][qid][i+1]-scores[date][qid][i])
                    except IndexError:
                        print i,len(scores[date][qid])
                        sys.exit(0)
                if difference_features:
                    for i in range(limit+1,len(coeff)):
                        try:
                            
                            single_feature_vector.append(difference_features[qid][date][i-limit-1] )
                        except KeyError:
                            single_feature_vector.append(.0)
                X = [single_feature_vector]
                threshold[date][qid] = regr.predict(X)[0]

            else:
                threshold[date][qid] = coeff[0]*clarities[date][qid]
                threshold[date][qid] += coeff[1]*scores[date][qid][0]
                #for i in range(len(scores[date][qid])):
                for i in range(limit-1):
                    try:
                        threshold[date][qid] += coeff[i+2]*(scores[date][qid][i+1]-scores[date][qid][i])
                    except IndexError:
                        print i,len(coeff),len(scores[date][qid])
                        sys.exit(0)
                if difference_features:
                    for i in range(limit+1,len(coeff)):
                        try:
                            
                            threshold[date][qid] += coeff[i]*difference_features[qid][date][i-limit-1] 
                        except KeyError:
                            threshold[date][qid] += .0

        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]
                if qid not in judged_qids:
                    continue
                else:
                    #print "good qid %s" %qid
                    #print "write %sto temp" %(line)
                   
                    
                    if qid not in num_return[date]:
                        num_return[date][qid] = 0


                    tid = parts[2]

                    score = float(parts[4])
                    rank = parts[3]
                    runtag = parts[5]
                    
                    line = "%s%s %s Q0 %s %s %f %s\n" %(prefix,date.zfill(2),qid,tid,rank,score,runtag)
                    prf.write(line)
                    
                    
                    if score > threshold[date][qid]:
                        if num_return[date][qid]==limit:
                            continue
                        nf.write(line)
                        num_return[date][qid] += 1

                        


        for qid in num_return[date]:
            print "return %d for %s" %(num_return[date][qid],qid)

        

    prf.close()
    nf.close() 







def get_lm_differences(difference_files):
    difference_features = {}
    for difference_file in difference_files:
        single_difference_feature = json.load(open(difference_file))
        for qid in single_difference_feature:
            if qid not in difference_features:
                difference_features[qid] = {}
            for day in single_difference_feature[qid]:
                if day not in difference_features[qid]:
                    difference_features[qid][day] = []
                difference_features[qid][day].append(single_difference_feature[qid][day])
    
    return difference_features




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--eval_topics","-ef",default="/infolab/node4/lukuang/2015-RTS/2015-data/eval_topics")
    parser.add_argument("--test_qid_file","-t",action="store_const",const="/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/query_prediction/threshold_with_lm_difference/data/test_qids")
    parser.add_argument("--is_2016","-st",action="store_true")
    parser.add_argument("--use_regr","-ur",action="store_true")
    parser.add_argument("--limit","-lm",type=int,default=10)
    #parser.add_argument("--performance_measure","-pms",default="P100")
    parser.add_argument("original_result_dir")
    parser.add_argument("clarity_dir")
    parser.add_argument("training_data_dir")
    parser.add_argument("test_result_dir")
    parser.add_argument("--difference_files","-df",nargs="*")
    args=parser.parse_args()


    # if use difference features
    # skip the first day. Otherwise,
    # include the first day.

    if not args.test_qid_file:
        print "WARNING: NO TEST!"

    days = map(str,range(21,30))
    if not args.difference_files:
        days = ["20"]+days[:]
    else:
        print "Use difference file:\n%s" %(" ".join(args.difference_files))


    

    if args.is_2016:
        prefix = "201608"
        eval_topics = None
    else:
        prefix = "201507"
        eval_topics = json.load(open(args.eval_topics))
    print "load necessary data"
    t2day = T2Day(args.tweet2day_file)
    judged_qids,qrels,coeff,regr = load_data(args.training_data_dir,args.qrel_file,args.test_qid_file,
                                        eval_topics)
    print judged_qids
    print "get clarity"
    clarities = get_clarity(args.clarity_dir,judged_qids)
    
    difference_features = {}
    if args.difference_files:
        print "get language model difference fearures"
        difference_features = get_lm_differences(args.difference_files)

    print "generate result files"
    if args.use_regr:
        generate_new_results(
            args.test_result_dir,
            args.original_result_dir,
            clarities,coeff,judged_qids,args.limit,
            difference_features,days,prefix,regr)
    else:
        generate_new_results(
            args.test_result_dir,
            args.original_result_dir,
            clarities,coeff,judged_qids,args.limit,
            difference_features,days,prefix)

    #compare_new_results(qrels,temp_result,new_result)
    
    #real_perfromance = get_real_perfromance(args.code_file,args.qrel_file,args.temp_result_file,args.performance_measure,args.debug)


if __name__=="__main__":
    main()

