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

def get_clarity(show_clarity_file,original_query_file ,index_dir,judged_qids):
    clarities = {}
    for date in os.walk(index_dir).next()[1]:
        clarities[date] = {}
        date_index_dir = os.path.join(index_dir,date)
        date_clarity = compute_clarity(show_clarity_file,date_index_dir,original_query_file)
        for qid in judged_qids:
            clarities[date][qid] = date_clarity[qid]

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

def compute_performance(results,date,qrel,sema_cluster,performance_method):
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
    else:
        raise NotImplementedError("The performance method %s is not implemented!"
                %performance_method)


def get_date_info(date_result_file,date,
                  qrel,sema_cluster,judged_qids,
                  limit,performance_method,use_diff):
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
        pos = 0
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
            performance_now = compute_performance(temp_doc,date,qrel,sema_cluster,performance_method)
            # if performance_now != precision_now:
            #     print "didnt agree for %s %s: %f, %f" %(date,qid,performance_now, precision_now)
            #     sys.exit(0)
            # else:
            #     print "Good!"
            if performance_now >= max_performance[qid] and performance_now!=0:
                
                max_performance[qid] = performance_now
                
                date_threshold[qid] = score_next
                pos = i
        
        if max_performance[qid] == .0:
            date_threshold[qid] =  date_score_list[qid][0]
            pos = 0
        print "pos is %d for query %s" %(pos,qid)
    if use_diff:
        score_diff = {}
        for qid in date_score_list:
            score_diff[qid] = []
            score_diff[qid].append(date_score_list[qid][0])
            for i in range(len(date_score_list[qid])-1):
                score_now = date_score_list[qid][i]
                score_next = date_score_list[qid][i+1]
                score_diff[qid].append(score_next-score_now)

        return date_threshold , score_diff           
    else:                
        return date_threshold , date_score_list            


def get_features(result_dir,qrel,sema_cluster,
                 judged_qids,limit,performance_method,
                 use_diff):

    thresholds = {}
    score_lists = {}
    for date in os.walk(result_dir).next()[2]:
        date_result_file = os.path.join(result_dir,date)
        date_threshold,date_score_list = get_date_info(date_result_file,
                                            date,qrel,sema_cluster,
                                            judged_qids,limit,
                                            performance_method,use_diff)

        thresholds[date] = date_threshold
        score_lists[date] = date_score_list

    return thresholds,score_lists


def write_to_disk(feature_vector,threshold_vector,dest_dir,judged_qids,test):
    with open(os.path.join(dest_dir,"features"),'w') as f:
        f.write(json.dumps(feature_vector))


    with open(os.path.join(dest_dir,"thresholds"),'w') as f:
        f.write(json.dumps(threshold_vector))

    if test:
        with open(os.path.join(dest_dir,"query_ids"),'w') as f:
            f.write(json.dumps(judged_qids))




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--show_clarity_file","-scf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("--index_dir","-id",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual")
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--no_stopwords","-ns",action='store_true')
    parser.add_argument("--test","-t",action='store_true')
    parser.add_argument("--limit","-lm",type=int,default=10)
    parser.add_argument("--performance_method","-pm",choices=["precision","f0.5","f1"])
    parser.add_argument("--use_diff","-ud",action="store_true")
    parser.add_argument("original_query_file")
    parser.add_argument("result_dir")
    parser.add_argument("dest_dir")

    args=parser.parse_args()


    # if args.no_stopwords:

    #         stopword_handler = Stopword_Handler()
    #         simple_queries = read_simple_queries(args.original_query_file,stopword_handler)
    #     else:
    #         simple_queries = read_simple_queries(args.original_query_file)
    
    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)
    qrel = Qrel(args.qrel_file)
    
    

    judged_qids = qrel.qids
    if args.test:
        # import random
        # size = len(judged_qids)/2

        # judged_qids = random.sample(judged_qids,size)
        judged_qids = json.load(open("/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/query_prediction/data/threshold/precision_oriented/query_ids"))
    print "get clarity for each query/index"
    clarities = get_clarity(args.show_clarity_file,
                            args.original_query_file,
                            args.index_dir,judged_qids)
    
    
    print "get score list and thresholds"
    thresholds,score_lists = get_features(args.result_dir,
                                qrel,sema_cluster,
                                judged_qids,args.limit,
                                args.performance_method,
                                args.use_diff)

    feature_vector = []
    threshold_vector = []

    for date in clarities:
        for qid in clarities[date]:
            single_feature_vector = []
            single_feature_vector.append(clarities[date][qid])
            single_feature_vector += score_lists[date][qid]
            feature_vector.append(single_feature_vector)
            threshold_vector.append(thresholds[date][qid])

    print "write data"
    write_to_disk(feature_vector,threshold_vector,args.dest_dir,judged_qids,args.test)


if __name__=="__main__":
    main()

