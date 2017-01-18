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
                        performance_method,existed_cluster):
    precision = qrel.precision(results)
    # if precision <= 0.2:
    #     return .0
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
        # ndcg10 = qrel.day_dcg10_no_pre(date,results,sema_cluster)
        raw_ndcg10 = qrel.raw_ndcg10(date,results,sema_cluster)
        # if ndcg10 ==.0 or raw_ndcg10 == .0:
        #     if ndcg10 != raw_ndcg10:
        #         qid = results.keys()[0]
        #         print "ndcg does not agree!"
        #         print "ndcg10: %f, raw_ndcg10 %f" %(ndcg10,raw_ndcg10)
        #         print "date %s, qid: %s" %(date,qid)
        #         print sema_cluster._day_cluster[date][qid]
        #         print results
        #         sys.exit(-1)
        return raw_ndcg10
    else:
        raise NotImplementedError("The performance method %s is not implemented!"
                %performance_method)


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



def get_date_info(date_result_file,date,
                  qrel,sema_cluster,judged_qids,
                  limit,performance_method,existed_cluster,
                  silent_day_choice):
    date_threshold = {}
    date_silent_qids = {}
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
        max_performance[qid] = .0
        date_threshold[qid] = date_score_list[qid][0]
        #print "silent performance: %.04f" %(max_performance[qid])
        # result number != 0
        for i in range(len(docids[qid])):
            score_now = date_score_list[qid][i]
            # score_next = date_score_list[qid][i+1]
            # if score_next == score_now:
            #     if i+1 == limit:
            #         score_next -= 0.001
            #     else:
            #         continue
            #precision_now = num_of_rel[qid][i]*1.0/(i+1)
            
            temp_doc = {
                qid: docids[qid][:i+1]
            } 
            performance_now = compute_performance(temp_doc,date,qrel,sema_cluster,performance_method,existed_cluster)
            # if date == '20' and qid == 'MB324':
            #     performance_now = compute_performance(temp_doc,date,qrel,sema_cluster,performance_method,existed_cluster)

            #     print "performance now is %s" %performance_now
            # if performance_now != precision_now:
            #     print "didnt agree for %s %s: %f, %f" %(date,qid,performance_now, precision_now)
            #     sys.exit(0)
            # else:
            #     print "Good!"
            if performance_now > max_performance[qid] :

                max_performance[qid] = performance_now
                
                date_threshold[qid] = score_now
                pos = i
        # if max_performance[qid] == .0:
        #     date_threshold.pop(qid,None)
        #     date_silent_qids[qid] = 0
        #     pos = -1
        #     if sema_cluster.day_cluster_recall({qid: docids[qid][:10]},date)!=0:
        #         print "ndcg is 0 but recall is not!"
        #         print "date %s, qid: %s" %(date,qid)
        #         print sema_cluster._day_cluster[date][qid]
        #         print docids[qid][:10]
        #         print i
        #         sys.exit(-1)
        # else:
        #     print "query %s is not silent!" %(qid)
        is_silent_day = False
        if silent_day_choice == 0:
            is_silent_day = qrel.is_irrelevant_day(qid,date,sema_cluster,{qid:docids[qid][:10]})
            # if the initial result does not contain any relevant tweets
            # it is still considered as a irrelevant day
            is_silent_day = (is_silent_day or max_performance[qid] == .0)
            
        elif silent_day_choice == 1:
            is_silent_day = qrel.is_redundant_day(qid,date,existed_cluster,sema_cluster)
        elif silent_day_choice == 2:
            is_silent_day = qrel.is_silent_day(qid,date,existed_cluster,sema_cluster,{qid:docids[qid][:10]})
        else:
            raise NotImplementedError("Did not implement %d silent day choice" %(silent_day_choice))
            
        if is_silent_day:
            date_threshold.pop(qid,None)
            date_silent_qids[qid] = 0
            pos = -1
        
        #update the existed_cluster
        else:
            #the result after thresholding
            returned_result = docids[qid][:pos+1]
            update_existed_cluster(existed_cluster,sema_cluster,qid,returned_result)

        
        print "pos is %d for query %s" %(pos,qid)

    threshold_score_diff = {}
    silent_score_diff = {}
    for qid in date_score_list:
        score_diff = []
        score_diff.append(date_score_list[qid][0])
        for i in range(len(date_score_list[qid])-1):
            score_now = date_score_list[qid][i]
            score_next = date_score_list[qid][i+1]
            score_diff.append(score_next-score_now)
        if qid in date_threshold:
            threshold_score_diff[qid] = score_diff
        else:
            silent_score_diff[qid] = score_diff


    return date_threshold ,date_silent_qids, threshold_score_diff, silent_score_diff          
           


def get_features(result_dir,qrel,sema_cluster,
                 judged_qids,limit,
                 performance_method,days,
                 silent_day_choice):

    thresholds = {}
    silent_qids = {}
    threshold_score_lists = {}
    silent_score_lists = {}
    existed_cluster = {}
    for date in days:
        date_result_file = os.path.join(result_dir,date)
        date_threshold ,date_silent_qids, date_threshold_score_diff, date_silent_score_diff\
                             = get_date_info(
                                            date_result_file,
                                            date,qrel,sema_cluster,
                                            judged_qids,limit,
                                            performance_method,
                                            existed_cluster,silent_day_choice)

        thresholds[date] = date_threshold
        silent_qids[date] = date_silent_qids
        threshold_score_lists[date] = date_threshold_score_diff
        silent_score_lists[date] = date_silent_score_diff

    return thresholds,silent_qids,threshold_score_lists,silent_score_lists

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


def write_to_disk(silent_feature_vector,threshold_feature_vector,threshold_vector,silent_classification_vector,dest_dir,judged_qids,test_qid_file):
    with open(os.path.join(dest_dir,"silent_feature_vector"),'w') as f:
        f.write(json.dumps(silent_feature_vector))

    with open(os.path.join(dest_dir,"threshold_feature_vector"),'w') as f:
        f.write(json.dumps(threshold_feature_vector))

    with open(os.path.join(dest_dir,"threshold_vector"),'w') as f:
        f.write(json.dumps(threshold_vector))


    with open(os.path.join(dest_dir,"silent_classification_vector"),'w') as f:
        f.write(json.dumps(silent_classification_vector))

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
    parser.add_argument("--use_days","-ud",action="store_true", help="use # of days to first day as a feature")
    parser.add_argument("--limit","-lm",type=int,default=10)
    parser.add_argument("--performance_method","-pm",choices=["precision","f0.5","f1","ndcg10"],default="ndcg10")
    parser.add_argument("--silent_day_choice","-sc",choices=[0,1,2],type=int,
            help="""
                Choose what the classification should include:
                    0: only irrelevant day
                    1: only redundant day
                    2: both
            """)
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
    print args.silent_day_choice
    thresholds,silent_qids,threshold_score_lists,silent_score_lists\
                = get_features(args.result_dir,
                               qrel,sema_cluster,
                               judged_qids,args.limit,
                               args.performance_method,days,
                               args.silent_day_choice)

    if args.difference_files:
        print "get language model difference fearures"
        difference_features = get_lm_differences(args.difference_files)
        #print difference_features

    silent_feature_vector = []
    threshold_feature_vector = []
    threshold_vector = []
    silent_classification_vector = []

    for date in days:
        for qid in clarities[date]:
            single_feature_vector = []
            single_feature_vector.append(clarities[date][qid])
            if qid in silent_qids[date]:
                single_feature_vector += silent_score_lists[date][qid]
            else:
                single_feature_vector += threshold_score_lists[date][qid]
            
            if args.difference_files:
                try:
                    single_feature_vector += difference_features[qid][date]
                except KeyError:
                    single_feature_vector += [.0]*len(args.difference_files)

            if args.use_days:
                days_to_first = int(date) - int(days[0])
                single_feature_vector.append(days_to_first)

            silent_feature_vector.append(single_feature_vector)
            if qid in silent_qids[date]:
                silent_classification_vector.append(1)
            else:
                silent_classification_vector.append(0)
                threshold_feature_vector.append(single_feature_vector)
                threshold_vector.append(thresholds[date][qid])


    print "write data"
    write_to_disk(silent_feature_vector,threshold_feature_vector,threshold_vector,silent_classification_vector,args.dest_dir,judged_qids,args.test_qid_file)


if __name__=="__main__":
    main()

