"""
prepare training data(clarity scores,thresohlds etc,.)
for training to predict stopping score
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

from myUtility.misc import Stopword_Handler

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster


def get_f_point_five(recall,precision):
    if recall == .0:
        return .0
    return (0.5*0.5 + 1)*precision*recall / (0.5*0.5*precision + recall)

def get_f1(recall,precision):
    if recall == .0:
        return .0
    return 2.0*precision*recall / (precision + recall)






def get_clarity(clarity_dir,judged_qids):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in judged_qids:
            clarities[date][qid] = date_clarity[qid]

    return clarities





def compute_performance(results,date,qrel,sema_cluster,
                        performance_method,existed_clusters):
    precision = qrel.precision(results)
    if precision <= 0.2:
        return .0
    if performance_method == "precision":
        return precision
    elif performance_method == "f0.5":
        recall = sema_cluster.day_cluster_recall(results,date)
        f_point_five = get_f_point_five(recall,precision)
        return f_point_five
    elif performance_method == "f1":
        recall = sema_cluster.day_cluster_recall(results,date)
        f1 = get_f1(recall,precision)
        return f1
    elif performance_method == "ndcg10":
        ndcg10 = qrel.day_dcg10(date,results,existed_clusters,sema_cluster)

    else:
        raise NotImplementedError("The performance method %s is not implemented!"
                %performance_method)


def get_date_info(date_result_file,date,
                  qrel,sema_cluster,judged_qids,
                  limit,performance_method,existed_clusters):
    date_threshold = {}
    docids = {}
    date_score_list = {}
    num_of_docs = {}
    num_of_rel = {}
    stop = {}
    with open(date_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid not in judged_qids:
                    continue
                else:

                    if qid not in date_threshold:
                        date_threshold[qid] = .0
                        docids[qid] = []
                        date_score_list[qid] = []
                        num_of_rel[qid] = [] 
                        num_of_docs[qid] = 0
                        stop[qid] = False

                    if stop[qid]:
                        continue
                    
                        
                    docid = parts[2]
                    score = float(parts[4])

                    if num_of_docs[qid] == limit:
                        stop[qid] = True
                        continue

                    date_score_list[qid].append(score)
                    docids[qid].append(docid)
                    num_of_docs[qid] += 1

                    if qrel.is_relevant(qid,docid):
                        if num_of_rel[qid]:
                            num_of_rel[qid].append(num_of_rel[qid][-1]+1)
                        else:
                            num_of_rel[qid].append(1)
                    else:
                        if num_of_rel[qid]:
                            num_of_rel[qid].append(num_of_rel[qid][-1])
                        else:
                            num_of_rel[qid].append(0)
                        
    max_performance = {}
    for qid in docids:
        max_performance[qid] = .0
        pos = -1

        # remain silent
        
        temp_doc = {
                qid: []
        }
        max_performance[qid] = compute_performance(temp_doc,date,qrel,sema_cluster,performance_method,existed_clusters)
        date_threshold[qid] = date_score_list[qid][0]
        #print "silent performance: %.04f" %(max_performance[qid])
        # result number != 0
        for i in range(len(docids[qid])-1):
            score_now = date_score_list[qid][i]
            score_next = date_score_list[qid][i+1]
            if score_next == score_now:
                if i+1 == limit:
                    score_next -= 0.001
                else:
                    continue
            #precision_now = num_of_rel[qid][i]*1.0/(i+1)
            
            temp_doc = {
                qid: docids[qid][:i+1]
            } 
            performance_now = compute_performance(temp_doc,date,qrel,sema_cluster,performance_method,existed_clusters)
            # if performance_now != precision_now:
            #     print "didnt agree for %s %s: %f, %f" %(date,qid,performance_now, precision_now)
            #     sys.exit(0)
            # else:
            #     print "Good!"
            if performance_now >= max_performance[qid] :
                if performance_method == "precision" and max_performance[qid]==0:
                    continue
                #print "performance imporved!"
                max_performance[qid] = performance_now
                
                date_threshold[qid] = score_next
                pos = i
        if performance_method == "precision":
            if max_performance[qid] == .0:
                date_threshold[qid] =  date_score_list[qid][0]
                pos = -1
        #print "pos is %d for query %s" %(pos,qid)

    score_diff = {}
    for qid in date_score_list:
        score_diff[qid] = []
        score_diff[qid].append(date_score_list[qid][0])
        for i in range(len(date_score_list[qid])-1):
            score_now = date_score_list[qid][i]
            score_next = date_score_list[qid][i+1]
            score_diff[qid].append(score_next-score_now)

    return date_threshold , score_diff           
           


def get_features(result_dir,qrel,sema_cluster,
                 judged_qids,limit,
                 performance_method,days):

    thresholds = {}
    score_lists = {}
    existed_clusters = {}
    for date in days:
        date_result_file = os.path.join(result_dir,date)
        date_threshold,date_score_list = get_date_info(
                                            date_result_file,
                                            date,qrel,sema_cluster,
                                            judged_qids,limit,
                                            performance_method,
                                            existed_clusters)

        thresholds[date] = date_threshold
        score_lists[date] = date_score_list

    return thresholds,score_lists

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


def write_to_disk(feature_vector,threshold_vector,dest_dir,judged_qids,test_qid_file):
    with open(os.path.join(dest_dir,"features"),'w') as f:
        f.write(json.dumps(feature_vector))


    with open(os.path.join(dest_dir,"thresholds"),'w') as f:
        f.write(json.dumps(threshold_vector))

    if test_qid_file:
        with open(os.path.join(dest_dir,"query_ids"),'w') as f:
            f.write(json.dumps(judged_qids))




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--eval_topics","-ef",default="/infolab/node4/lukuang/2015-RTS/2015-data/eval_topics")
    parser.add_argument("--index_dir","-id",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual")
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--test_qid_file","-t",action="store_const",const="/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/query_prediction/threshold_with_lm_difference/data/test_qids")
    parser.add_argument("--limit","-lm",type=int,default=10)
    parser.add_argument("--performance_method","-pm",choices=["precision","f0.5","f1","ndcg10"],default="ndcg10")
    parser.add_argument("--difference_files","-df",nargs="*")
    parser.add_argument("result_dir")
    parser.add_argument("clarity_dir")
    parser.add_argument("dest_dir")

    args=parser.parse_args()

    # if use difference features
    # skip the first day. Otherwise,
    # include the first day.
    print "performance measurement %s" %args.performance_method
    if not args.test_qid_file:
        print "WARNING: NO TEST!"

    days = map(str,range(21,30))
    if not args.difference_files:
        days = ["20"]+days[:]
    else:
        print "Use difference file:\n%s" %(" ".join(args.difference_files))

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)
    qrel = Qrel(args.qrel_file)
    
    
    eval_topics = json.load(open(args.eval_topics))
    judged_qids = eval_topics
    if args.test_qid_file:
        # import random
        # size = len(judged_qids)/2

        # judged_qids = random.sample(judged_qids,size)
        judged_qids = []
        temp_qids = json.load(open(args.test_qid_file))
        for qid in temp_qids:
            if qid in eval_topics:
                judged_qids.append(qid)

    print "get clarity"
    clarities = get_clarity(args.clarity_dir,judged_qids)
    
    
    print "get score features, thresholds"
    thresholds,score_lists = get_features(args.result_dir,
                                qrel,sema_cluster,
                                judged_qids,args.limit,
                                args.performance_method,days)

    if args.difference_files:
        print "get language model difference fearures"
        difference_features = get_lm_differences(args.difference_files)
        #print difference_features

    feature_vector = []
    threshold_vector = []

    for date in days:
        for qid in clarities[date]:
            single_feature_vector = []
            single_feature_vector.append(clarities[date][qid])
            single_feature_vector += score_lists[date][qid]
            
            if args.difference_files:
                try:
                    single_feature_vector += difference_features[qid][date]
                except KeyError:
                    single_feature_vector += [.0]*len(args.difference_files)
            feature_vector.append(single_feature_vector)
            threshold_vector.append(thresholds[date][qid])

    print "write data"
    write_to_disk(feature_vector,threshold_vector,args.dest_dir,judged_qids,args.test_qid_file)


if __name__=="__main__":
    main()

