"""
construct tree estimator
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle
import numpy as np
import random
import subprocess
from copy import deepcopy
from scipy.stats import kendalltau
from sklearn.model_selection import KFold

from forest import Forest

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/disk4-5")
from disk45_plot_silentDay_predictor import R_DIR, Expansion, IndexType, RetrievalMethod





class EvalData(object):
    """
    base class for eval data
    """

    def __init__(self,index_type,metic_string):
        self._silent_days = {}
        self._index_type = index_type
        self._metic_string = metic_string

        self._eval_dir = "/infolab/node4/lukuang/2015-RTS/disk4-5/eval"

        if self._index_type == IndexType.full:
            
            self._qrel_file = os.path.join(self._eval_dir,"full_qrel")
     
        elif self._index_type == IndexType.processed:
            self._qrel_file = os.path.join(self._eval_dir,"processed_qrel")


        else:
            raise NotImplementedError("Index type %s is not implemented!" %(self._index_type.name))

        print "qrel file is %s" %(self._qrel_file)
        
                



    def get_metric(self,result_file):
        metrics = {}
        run_command = "trec_eval -q %s %s | grep \"^%s \"  " %(self._qrel_file,
                                                              result_file,
                                                              self._metic_string)

        p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
        
        while True:
            line = p.stdout.readline()
            if line != '':
                line = line.rstrip()
                parts = line.split()
                qid = parts[1]
                value = float( parts[2] )
                if qid != "all":

                    metrics[qid] = value
                

            else:
                break 
        return metrics

    # @property
    # def days(self):
    #     return self._days
    


def get_result_files(result_dir):
    result_files = {}
    

    for day in os.walk(result_dir).next()[2]:
        
        day_result_file = os.path.join(result_dir,day)
        result_files[day] = day_result_file
        


    return result_files

def evaluate_kt(metrics,predicted_values):
    real = []
    predicted = []
    for day_qid in metrics:
        real.append(metrics[day_qid])
        predicted.append(predicted_values[day_qid])
    
    # print real
    # print predicted

    return kendalltau(real,predicted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index_type","-it",choices=list(map(int, IndexType)),default=0,type=int,
        help="""
            Choose the index type:
                0:full
                1:processed
        """)
    parser.add_argument("--tree_estimator_directory","-td",default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/disk4-5/predictor_data/post/tree_estimator")
    parser.add_argument("--number_of_iterations","-ni",type=int,default=50)
    parser.add_argument("--error_threshold","-et",type=int,default=30)
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("dest_file")
    parser.add_argument("--metric_string","-ms",default="P_10")
    args=parser.parse_args()

    # if args.error_threshold >= 50:
    #     raise ValueError("Threshold cannot be greater than 50!")

    args.index_type = IndexType(args.index_type)
    eval_data = EvalData(args.index_type,args.metric_string)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    result_dir = R_DIR[args.index_type][args.retrieval_method]
    print "result dir %s" %(result_dir)
    result_files = get_result_files(result_dir)
    query_data_file = os.path.join(args.tree_estimator_directory,args.index_type.name,args.retrieval_method.name)
    query_data_file = os.path.join(query_data_file,"data")
    print "get value pair %s" %(query_data_file)
    values = json.load(open(query_data_file))

    all_metrics = {}
    for day in values:
        all_metrics[day] =  eval_data.get_metric(result_files[day])

    # print results
    print all_metrics
    # create query_data
    query_data = []
    day = "10"
    for qid in values.values()[0].keys():
        day_qid = "10_%s" %(qid)
        # print day_qid
        if "desc" in day_qid:
            # print "escape desc query"
            continue
        else:
            m = re.search("^(\d+)_title",qid)
            if m:
                qid_value = int(m.group(1))
                if qid_value > 650:
                    continue

            else:
                "Wrong qid format: %s" %(qid)
        # print results[day]

        if qid in all_metrics[day]:
            
            day_query_metric = all_metrics[day][qid]
        else:
            print "WARNING: %s metric not found!" %(qid)
            day_query_metric = .0
        
        single_data = {}
        single_data["day_qid"] = day_qid
        single_data["metric"] = day_query_metric
        single_data["values"] = values[day][qid]
        query_data.append(single_data)

    # print metrics
    print "There are %d queries" %(len(query_data))
    kf = KFold(n_splits=4,shuffle=True)
    kt = []

    for training_index, test_index in kf.split(query_data):

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

        # print predicted_values
        # print metrics
        single_kt = evaluate_kt(metrics,predicted_values)
        print single_kt
        # print single_kt[0]
        kt.append(single_kt[0])

    print "The average kendall's tau is %f" %(sum(kt)/(1.0*len(kt)))


    forest = Forest(query_data,args.error_threshold,args.number_of_iterations)
        
    forest.start_training()
    with open(args.dest_file,'w') as f:
        cPickle.dump(forest, f, protocol=cPickle.HIGHEST_PROTOCOL)


    




if __name__=="__main__":
    main()

