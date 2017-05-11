"""
test classification for two stage
"""

import os
import json
import sys
import re
import argparse
import codecs
from copy import deepcopy
import cPickle
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.metrics import f1_score as f1

from forest import Forest
from construct_tree_estimator import EvalData,get_result_files,QueryPart

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


def get_best_f1_threshold(y_true, y_score):
    best_f1_score = -1000
    best_f1_threshold = .0
    sorted_scores = sorted(y_score)
    for threshold in sorted_scores:
        if threshold == 1000:
            continue
        temp_y_predict = []
        for actual_score in y_score:
            if actual_score < threshold:
                temp_y_predict.append(1)
            else:
                temp_y_predict.append(0)
        now_f1 = f1(y_true,temp_y_predict)

        if (now_f1>best_f1_score):
            best_f1_score = now_f1
            best_f1_threshold = threshold


    return best_f1_threshold,best_f1_score




def load_tree(tree_store_dir,query_part,retrieval_method,metric_string):
    tree_file = os.path.join(tree_store_dir,query_part.name,retrieval_method.name+"_"+metric_string)

    return cPickle.load(open(tree_file))


def get_threshold(title_predicted_values,desc_predicted_values,title_only):
    thresholds = []
    
    

    title_predicted_values.sort()
    desc_predicted_values.sort()

    # title_value_set = set(title_predicted_values)
    # desc_value_set = set(desc_predicted_values)
    # for t in title_value_set:
    #     for d in desc_value_set:
    #         single_threshold = {
    #             "title":t,
    #             "desc":d
    #         }
    #         thresholds.append(single_threshold)

    size = len(title_predicted_values)
    step = size/10
    for i  in range(1,10):
        single_threshold = { }
        single_threshold["title"] = title_predicted_values[i*step]
        if not title_only:
            single_threshold["desc"] = desc_predicted_values[i*step]
        thresholds.append(single_threshold)

    # thresholds.append({"title":1000,"desc":1000})

    return thresholds



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
    parser.add_argument("--title_only","-to",action="store_true")
    parser.add_argument("--metric_string","-ms",default="P_10")
    parser.add_argument("tree_store_dir")
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
    title_query_data = []
    desc_query_data = []
    query_data = []
    silent_judgments = []

    silent_days = {}
    day = "10"
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
        if args.title_only:
            if "title" not in qid:
                continue
        if qid in all_metrics[day]:
            
            day_query_metric = all_metrics[day][qid]

            m = re.search("^(\d+)_",qid)
            if m:
                q_num = m.group(1)
            else:
                raise RuntimeError("Mal qid format %s" %(qid))
            
            if q_num in silent_query_info :
                silent_days[day_qid] = 1
            else:
                silent_days[day_qid] = 0
        
        else: 
            print "%s query has no metric!" %(qid)
            day_query_metric = .0
            silent_days[day_qid] = 1

        single_data = {}
        single_data["day_qid"] = day_qid
        single_data["metric"] = day_query_metric
        single_data["values"] = values[day][qid]

        if "title" in qid:
            title_query_data.append(single_data)
        else:
            desc_query_data.append(single_data)

        query_data.append(single_data)
        silent_judgments.append( silent_days[day_qid] )
        
    title_tree = load_tree(args.tree_store_dir,QueryPart.title,args.retrieval_method,args.metric_string)
    title_predicted = title_tree.output_result(title_query_data)
    if not args.title_only:
        desc_tree = load_tree(args.tree_store_dir,QueryPart.desc,args.retrieval_method,args.metric_string)
        desc_predicted = desc_tree.output_result(desc_query_data)


    # print "There are %d queries" %(len(query_data))
    # print "%d of them are silent" %(sum(silent_judgments))


    print "There are %d samples" %(len(query_data))
    # print thresholds
        
    num_of_split = 10
    f1_macro_average = .0
    f1_average = .0
    skf = StratifiedKFold(n_splits=num_of_split,shuffle=True)
    for training_index, test_index in skf.split(query_data, silent_judgments):
        all_training_data = []
        training_title_query_data = []
        training_desc_query_data = []


        # print "%d training %d testing" %(len(training_index),len(test_index))
        for i in training_index:
            single_data = deepcopy(query_data[i])
            day_qid = single_data["day_qid"]
                    
            all_training_data.append(single_data )
            if "title" in day_qid:
                training_title_query_data.append(single_data)
            else:
                if not args.title_only:
                    training_desc_query_data.append(single_data)
        
        train_title_predicted = title_tree.output_result(training_title_query_data)
        if not args.title_only:
            train_desc_predicted = desc_tree.output_result(training_desc_query_data)
        else:
            train_desc_predicted = {0:0}
        thresholds = get_threshold(train_title_predicted.values(),train_desc_predicted.values(),args.title_only)
        best_tree_threshold = {}
        best_f1_score = -1000
        best_f1_threshold = .0
        for threshold in thresholds:
            sub_training_data = []
            training_pre_y_true = []
            training_pre_y_score = []
            for single_data in all_training_data:
                day_qid = single_data["day_qid"]
                if "title" in day_qid:
                    if (title_predicted[day_qid] <= threshold["title"]):
                        
                        sub_training_data.append(single_data )
                    else:
                        training_pre_y_score.append(1000)
                        training_pre_y_true.append(silent_days[day_qid])
                else:
                    if not args.title_only:
                        if (desc_predicted[day_qid]  <= threshold["desc"]):
                            sub_training_data.append(single_data) 
                        else:
                            training_pre_y_score.append(1000)
                            training_pre_y_true.append(silent_days[day_qid])


            forest = Forest(sub_training_data,args.error_threshold,args.number_of_iterations)
            forest.start_training()

            training_predicted_values = forest.output_result(sub_training_data)
            training_y_true, training_y_score = make_score_prediction_lists(training_predicted_values,silent_days)
            training_y_true  = training_pre_y_true + training_y_true
            training_y_score  = training_pre_y_score + training_y_score
            threshold_best_f1_threshold,theshold_best_f1_score = get_best_f1_threshold(training_y_true, training_y_score)
            if theshold_best_f1_score > best_f1_score:
               best_tree_threshold =  threshold
               best_f1_score = theshold_best_f1_score
               best_f1_threshold = threshold_best_f1_threshold
        
        print "best f1 threshold:%f, best f1 %f:" %(best_f1_threshold,best_f1_score)
        print best_tree_threshold

        testing_data = []
        testing_pre_y_true = []
        testing_pre_y_score = []

        for j in test_index:
            single_data = deepcopy(query_data[j])
            day_qid = single_data["day_qid"]
                    

            if "title" in day_qid:
                if (title_predicted[day_qid] <= best_tree_threshold["title"]):
                        
                    testing_data.append(single_data )
                else:
                    testing_pre_y_score.append(1000)
                    testing_pre_y_true.append(silent_days[day_qid])
            else:
                if not args.title_only:
                    if (desc_predicted[day_qid] <= best_tree_threshold["desc"]):
                            
                        testing_data.append(single_data )
                    else:
                        testing_pre_y_score.append(1000)
                        testing_pre_y_true.append(silent_days[day_qid])

        test_forest = Forest(testing_data,args.error_threshold,args.number_of_iterations)
        test_forest.start_training()

        test_predicted_values = forest.output_result(testing_data)
        testing_y_true, testing_y_score = make_score_prediction_lists(test_predicted_values,silent_days)
        testing_y_true  = testing_pre_y_true + testing_y_true
        testing_y_score  = testing_pre_y_score + testing_y_score
        test_y_predict = []
        for single_score in testing_y_score:
            if single_score < best_f1_threshold:
                test_y_predict.append(1)
            else:
                test_y_predict.append(0)
        f1_macro_average += f1(testing_y_true, test_y_predict,average="macro")/(1.0*num_of_split)
        f1_average += f1(testing_y_true, test_y_predict)/(1.0*num_of_split)

    

    print "Positive f1: %f" %(f1_average)
    print "Average f1: %f" %(f1_macro_average)
    print "-"*20


if __name__=="__main__":
    main()

