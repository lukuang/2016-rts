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


def load_data(training_data_dir):
    
    regr_file = os.path.join(training_data_dir,"regr")        
    f = open(regr_file, 'rb')
    regr = cPickle.load(f)
    f.close()

    clf_file = os.path.join(training_data_dir,"clf")        
    f = open(clf_file, 'rb')
    clf = cPickle.load(f)
    f.close()

    return regr,clf



def get_clarity(clarity_dir):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in date_clarity:
            clarities[date][qid] = date_clarity[qid]

    return clarities





def generate_new_results(test_result_dir,
                         original_result_dir,
                         clarities,limit,
                         difference_features,days,prefix,regr,clf):
    
    threshold = {}
    scores = {}
    num_return = {}
    processed_original_result_file = os.path.join(test_result_dir,'original_result')
    new_result_file = os.path.join(test_result_dir,'new_result')

    prf = open(processed_original_result_file,'w')
    nf = open(new_result_file,'w')
    print days
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

                   

                score = float(parts[4])
                 
                if qid not in scores[date]:
                    scores[date][qid] = [] 
                scores[date][qid].append(score)

        for qid in scores[date]:
            
            single_feature_vector = []
            single_feature_vector = [clarities[date][qid],scores[date][qid][0]]
            #for i in range(len(scores[date][qid])):
            for i in range(limit-1):
                try:
                    single_feature_vector.append(scores[date][qid][i+1]-scores[date][qid][i])
                except IndexError:
                    print "Warning: query %s does not have enough results" %(qid)
                    single_feature_vector.append(.0)
            if difference_features:
                for i in range(2):
                    try:
                        print difference_features[qid][date]
                        print qid,date
                        single_feature_vector.append(difference_features[qid][date][i] )
                    except KeyError:
                        print "Error: query %s does not have difference feature!" %(qid)
                        sys.exit(-1)
                        #single_feature_vector.append(.0)
            X = [single_feature_vector]
            if clf.predict(X) == 0:

                threshold[date][qid] = regr.predict(X)[0]
            else:
                threshold[date][qid] = 10000
        

        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]

                   
                    
                if qid not in num_return[date]:
                    num_return[date][qid] = 0


                tid = parts[2]

                score = float(parts[4])
                rank = parts[3]
                runtag = parts[5]
                
                line = "%s%s %s Q0 %s %s %f %s\n" %(prefix,date.zfill(2),qid,tid,rank,score,runtag)
                prf.write(line)
                
                
                if score >= threshold[date][qid]:
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


    days = map(str,range(3,12))
    print days
    if not args.difference_files:
        days = ["2"]+days[:]
    else:
        print "Use difference file:\n%s" %(" ".join(args.difference_files))


    


    prefix = "201608"

    print "load necessary data"
    regr,clf = load_data(args.training_data_dir)

    print "get clarity"
    clarities = get_clarity(args.clarity_dir)
    
    difference_features = {}
    if args.difference_files:
        print "get language model difference fearures"
        difference_features = get_lm_differences(args.difference_files)

    print "generate result files"

    generate_new_results(
        args.test_result_dir,
        args.original_result_dir,
        clarities,args.limit,
        difference_features,days,prefix,regr,clf)


    #compare_new_results(qrels,temp_result,new_result)
    
    #real_perfromance = get_real_perfromance(args.code_file,args.qrel_file,args.temp_result_file,args.performance_measure,args.debug)


if __name__=="__main__":
    main()

