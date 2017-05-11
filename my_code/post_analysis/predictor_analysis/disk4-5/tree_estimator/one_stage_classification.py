"""
test classification for one stage
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle
from copy import deepcopy
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.metrics import f1_score as f1

from forest import Forest
from construct_tree_estimator import EvalData,get_result_files

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/disk4-5")
from disk45_plot_silentDay_predictor import R_DIR, Expansion, IndexType, RetrievalMethod



def make_score_prediction_lists(predicted_values,silent_days):
    y_true = []
    y_score = []

    for day_qid in predicted_values:
        y_score.append( predicted_values[day_qid] )
            
        if silent_days[day_qid]:
            y_true.append(1)
        else:
            y_true.append(0)

    return y_true, y_score


def best_f1(y_true, y_score):
    best_f1_score = -1000
    sorted_scores = sorted(y_score)
    for threshold in sorted_scores:
        temp_y_predict = []
        for actual_score in y_score:
            if actual_score < threshold:
                temp_y_predict.append(1)
            else:
                temp_y_predict.append(0)
        now_f1 = f1(y_true,temp_y_predict)

        if (now_f1>best_f1_score):
            best_f1_score = now_f1


    return best_f1_score





def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree_estimator_directory","-td",default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/disk4-5/predictor_data/post/tree_estimator")
    parser.add_argument("--number_of_iterations","-ni",type=int,default=50)
    parser.add_argument("--error_threshold","-et",type=int,default=30)
    parser.add_argument("--silent_query_info_file","-sf",default="/infolab/node4/lukuang/2015-RTS/disk4-5/eval/silent_query_info")
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--use_auc","-ua",action="store_true")
    parser.add_argument("--metric_string","-ms",default="P_10")
    args=parser.parse_args()

    index_type = IndexType.processed
    eval_data = EvalData(index_type,args.metric_string)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    result_dir = R_DIR[index_type][args.retrieval_method]
    print "result dir %s" %(result_dir)
    result_files = get_result_files(result_dir)
    query_data_file = os.path.join(args.tree_estimator_directory,index_type.name,args.retrieval_method.name)
    query_data_file = os.path.join(query_data_file,"data")
    print "get value pair %s" %(query_data_file)
    values = json.load(open(query_data_file))

    all_metrics = {}
    for day in values:
        all_metrics[day] =  eval_data.get_metric(result_files[day])


    silent_query_info = json.load(open(args.silent_query_info_file))

    # print all_metrics
    query_data = []
    silent_judgments = []
    silent_days = {}
    day = "10"
    silent_list = {}
    for qid in values.values()[0].keys():
        # m = re.search("^(\d+)_",qid)
        # if m:
        #     q_num = int(m.group(1))
        #     if q_num > 650:
        #         continue
        # else:
        #     raise RuntimeError("Mal qid format %s" %(qid))
        day_qid = "10_%s" %(qid)
        # print day_qid
        
        
        # print results[day]

        if qid in all_metrics[day]:
            
            day_query_metric = all_metrics[day][qid]

            m = re.search("^(\d+)_",qid)
            if m:
                q_num = m.group(1)
            else:
                raise RuntimeError("Mal qid format %s" %(qid))
            
            if q_num in silent_query_info :
                silent_days[day_qid] = 1
                silent_judgments.append(1)
            else:
                if day_query_metric == .0:
                    silent_list[q_num] = 0
                silent_judgments.append(0)
                silent_days[day_qid] = 0
        
        else: 
            day_query_metric = .0
            silent_judgments.append(1)
            silent_days[day_qid] = 1

        single_data = {}
        single_data["day_qid"] = day_qid
        single_data["metric"] = day_query_metric
        single_data["values"] = values[day][qid]
        query_data.append(single_data)
        
            

    print "There are %d queries" %(len(query_data))
    print "%d of them are silent" %(sum(silent_judgments))
    print "There are %d queries with silent list" %(len(silent_list))
 
    skf = StratifiedKFold(n_splits=10)
    eval_metrics = []
    for training_index, test_index in skf.split(query_data, silent_judgments):
        training_data = []
        testing_data = []
        metrics = {}
        # print "%d training %d testing" %(len(training_index),len(test_index))
        for i in training_index:
            training_data.append( deepcopy(query_data[i]))

        for j in test_index:
            testing_data.append( deepcopy(query_data[j]))
            day_qid = query_data[j]["day_qid"]
            metrics[day_qid] = query_data[j]["metric"]

        # print training_data
        forest = Forest(training_data,args.error_threshold,args.number_of_iterations)
        
        forest.start_training()

        predicted_values = forest.output_result(testing_data)
        y_true, y_score = make_score_prediction_lists(predicted_values,silent_days)

        if args.use_auc:
            reversed_score = []
            for i in y_score:
                reversed_score.append(-1*i)
            score = roc_auc_score(y_true, reversed_score)
            print "the auc score is %f"  %(score)
            eval_metrics.append(score)
        else:
            best_f1_score = best_f1(y_true, y_score)
            print "the best f1 score is %f" %(best_f1_score)
            eval_metrics.append(best_f1_score)


    print "Average performance: %f" %(sum(eval_metrics)/(1.0*len(eval_metrics)))



if __name__=="__main__":
    main()

