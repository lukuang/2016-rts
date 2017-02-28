"""
test silent day classification performance and break down
to irrelevant/redundant day classification accuracy using multi-class
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




def update_existed_cluster(existed_cluster,sema_cluster,qid,returned_result):
    """update the existed cluster
    """
    if qid not in existed_cluster:
        existed_cluster[qid] = set()

    for tid in returned_result:
        cluster_id = sema_cluster.get_cluster_id(qid,tid)
        if cluster_id is not None:
            if cluster_id not in existed_cluster[qid]:
                 existed_cluster[qid].add(cluster_id)


def test_accuracy(
                  original_result_dir,
                  clarities,limit,
                  difference_features,
                  days,prefix,regr,clf,
                  silent_days,sema_cluster,
                  qrel,use_days):
    

    scores = {}
    num_return = {}

    existed_cluster = {}
    if difference_features:
        first_day_result_file = os.path.join(original_result_dir,"2")
        num_of_docs = {}
        docids = {}
        with open(first_day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid not in silent_days:
                    continue
                else:
                    if qid not in num_of_docs:
                        docids[qid] = []
                        num_of_docs[qid] = 0
                    
                        
                    docid = parts[2]
                    score = float(parts[4])

                    if num_of_docs[qid] == limit:
                        
                        continue

                    docids[qid].append(docid)
                    num_of_docs[qid] += 1
        for qid in docids:

            update_existed_cluster(existed_cluster,sema_cluster,qid,docids[qid])

    true_count = {
        "all": {},
        "irr": {},
        "red": {}
    }
    
    class_num = {
            "irr": 0,
            "red": 0
    }
 
    predicted = {}
    threshold = {}
    

    for qid in silent_days:
        for c in  true_count:
            true_count[c][qid] = 0  

    for date in days:
        predicted[date] = {}

        date_result_file = os.path.join(original_result_dir,date)
        print "process file %s" %date_result_file
        scores[date] = {}
        next_date = str(int(date)+1)
        threshold[date] = {}
        
        num_return[date] = {}
        tids = {}
        
        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]

                score = float(parts[4])
                 
                if qid not in scores[date]:
                    tids[qid] = []
                    scores[date][qid] = [] 
                scores[date][qid].append(score)
                now_tid = parts[2]
                tids[qid].append(now_tid)


        for qid in scores[date]:
            #if a qid does not exists in qrels, ignore it
            if qid not in silent_days:
                continue

            if qid not in predicted[date]:
                predicted[date][qid] = {}

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
                single_feature_vector += difference_features[qid][date]
                # for i in range(2):
                #     try:
                #         print difference_features[qid][date]
                #         print qid,date
                #         single_feature_vector.append(difference_features[qid][date][i] )
                #     except KeyError:
                #         print "Error: query %s does not have difference feature!" %(qid)
                #         sys.exit(-1)
                #         #single_feature_vector.append(.0)
            if use_days:
                days_to_first = int(date) - int(days[0])
                single_feature_vector.append(days_to_first)

            X = [single_feature_vector]

            predicted[date][qid] = clf.predict(X)[0]
            
            if clf.predict(X) != 0:
                threshold[date][qid] = -10000
                # threshold[date][qid] = regr.predict(X)[0]
            else:
                
                threshold[date][qid] = 10000

           
        temp_result = {}
        with open(date_result_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]

                #if a qid does not exists in qrels, ignore it
                if qid not in silent_days:
                    continue

                if qid not in temp_result:
                    temp_result[qid] = []

                    
                if qid not in num_return[date]:
                    num_return[date][qid] = 0



                tid = parts[2]

                score = float(parts[4])
                rank = parts[3]
                runtag = parts[5]
                
                
                if score >= threshold[date][qid]:
                    if num_return[date][qid]==limit:
                        continue
                    num_return[date][qid] += 1
                    temp_result[qid].append(tid)

        
        for qid in temp_result:
            if qrel.is_irrelevant_day(qid,date.zfill(2),sema_cluster,{qid:tids[qid][:10]}):
                class_num["irr"] += 1
                if predicted[date][qid] == 1:
                    true_count["irr"][qid] += 1
                    true_count["all"][qid] += 1
            else:
                if predicted[date][qid] != 1:
                    true_count["irr"][qid] += 1
                    

            if qrel.is_redundant_day(qid,date.zfill(2),existed_cluster,sema_cluster):
                class_num["red"] += 1
                
                if predicted[date][qid] == 2:
                    true_count["red"][qid] += 1
                    true_count["all"][qid] += 1
            else:
                if predicted[date][qid] != 2:
                    true_count["red"][qid] += 1

            if not qrel.is_silent_day(qid,date.zfill(2),existed_cluster,sema_cluster,{qid:tids[qid][:10]}):
                if predicted[date][qid] == 0:
                    true_count["all"][qid] += 1
            # if qid == 'RTS10':
            #     print "Query RTS10:"
            #     print qrel.is_irrelevant_day(qid,date.zfill(2),sema_cluster,{qid:tids[qid][:10]})
            #     print  qrel.is_redundant_day(qid,date.zfill(2),existed_cluster,sema_cluster)
            #     print predicted[date][qid]
            
            
            update_existed_cluster(existed_cluster,sema_cluster,qid,temp_result[qid])


    total_count = len(silent_days) * len(days) * 1.0
    for t in true_count:
        accuracy = .0
        for qid in true_count[t]:
            q_accuracy = true_count[t][qid]*1.0 / len(days)
        
            # print "True count: %d, Total count: %d" %(true_count[t][qid],len(days))
            # print "for %s, %s accuracy is %f" %(qid, t, q_accuracy)
            accuracy += q_accuracy *1.0 / len(silent_days)
        # print "%d out of %d are %s" %(sum(true_count[t].values()),total_count,t)
        print "%s accuracy is %f" %(t, accuracy)

        print "-"*20

    for t in class_num:
        print "There are %d %s" %(class_num[t],t)
                        



        








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

def load_silent_day(eval_dir,days,prefix,query_choice):
    silent_days = {}
    non_silent_days = {}
    tweet2day_dt = {}

    file_tweet2day = os.path.join(eval_dir,'rts2016-batch-tweets2dayepoch.txt')
    qrels_file = os.path.join(eval_dir,'qrels.txt')
    
    for line in open(file_tweet2day).readlines():
        line = line.strip().split()
        tweet2day_dt[line[0]] = line[1]

    for line in open(qrels_file).readlines():
        parts = line.strip().split()
        qid = parts[0]
        tid = parts[2]
        score = int(parts[3])
        tweet_day = tweet2day_dt[tid]
        if qid not in non_silent_days:
            non_silent_days[qid] = set()
        if score > 0:
            non_silent_days[qid].add(tweet_day)

        else:
            continue

    for qid in non_silent_days:
        silent_days[qid] = []
        for date in days:
            day_string = "%s%s" %(prefix,date.zfill(2))
            if day_string not in non_silent_days[qid]:
                silent_days[qid].append(date)

    

    if query_choice == 0:
        for qid in silent_days.keys():
            if "RTS" in qid:
                silent_days.pop(qid,None)
    elif query_choice == 1:
        for qid in silent_days.keys():
            if "MB" in qid:
                silent_days.pop(qid,None)

    print "Show silent days:"
    print silent_days
    print "There are %d queries judged" %(len(silent_days))
    print "In total there are %d silent days" %(sum([len(silent_days[x]) for x in silent_days]))
    print "-"*20

    return silent_days


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit","-lm",type=int,default=10)
    parser.add_argument("--eval_dir","-ed",default='/infolab/node4/lukuang/2015-RTS/src/2016/eval')
    #parser.add_argument("--performance_measure","-pms",default="P100")
    parser.add_argument("original_result_dir")
    parser.add_argument("clarity_dir")
    parser.add_argument("training_data_dir")
    parser.add_argument("--silent_day_choice","-sc",choices=[0,1,2,3],type=int,
            help="""
                Choose what the classification should include:
                    0: only irrelevant day
                    1: only redundant day
                    2: both
                    3: only consider irrelevant day and include both negative/positive examples
            """)
    parser.add_argument("--query_choice","-qc",choices=[0,1,2],type=int,default=2,
            help="""
                Choose what the queries should include:
                    0: only old queries (2015)
                    1: only new queries (2016)
                    2: both
            """)
    parser.add_argument("--use_days","-ud",action="store_true", help="use # of days to first day as a feature")
   
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
    print "load silent days"
    silent_days = load_silent_day(args.eval_dir,days,prefix,args.query_choice)

    print "load cluster info"
    tweet2day_file = os.path.join(args.eval_dir,"rts2016-batch-tweets2dayepoch.txt")
    t2day = T2Day(tweet2day_file,is_16=True)

    cluster_file = os.path.join(args.eval_dir,"rts2016-batch-clusters.json")
    sema_cluster = SemaCluster(cluster_file,t2day,is_16=True)
    qrel_file = os.path.join(args.eval_dir,"qrels.txt")

    qrel = Qrel(qrel_file,is_16=True)


    print "load trained models"
    regr,clf = load_data(args.training_data_dir)

    print "get clarity"
    clarities = get_clarity(args.clarity_dir)
    
    difference_features = {}
    if args.difference_files:
        print "get language model difference fearures"
        difference_features = get_lm_differences(args.difference_files)

    print "calculate accuracy"

    test_accuracy(
        args.original_result_dir,
        clarities,args.limit,
        difference_features,days,
        prefix,regr,clf,silent_days,
        sema_cluster,qrel,args.use_days)


    #compare_oracle_results(qrels,temp_result,oracle_result)
    
    #real_perfromance = get_real_perfromance(args.code_file,args.qrel_file,args.temp_result_file,args.performance_measure,args.debug)


if __name__=="__main__":
    main()

