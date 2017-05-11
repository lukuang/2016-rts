"""
generate run based on the output of silent day classification
and the original raw retrieval results
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,RetrievalMethod

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

def convert_feature_string(feature_string):
    detail_finder_with_tn = re.search("^(\w+):(\w+):(\d+)$",feature_string)
    if detail_finder_with_tn:
        feature_string = detail_finder_with_tn.group(1)[:-1]+detail_finder_with_tn.group(3)
        feature_string += ":%s" %(detail_finder_with_tn.group(2) )
    feature_string = re.sub(":","_",feature_string)
    feature_string = feature_string[0].upper()+feature_string[1:]
    
    return feature_string

class EvalData(object):
    """
    base class for eval data
    """

    def __init__(self,year):
        self._year = year

        self._silent_days = {}

        if self._year == Year.y2015:
            self._prefix = "201507"
            self._eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"clusters-2015.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels.txt")
            self._topic_file = None
     
        elif self._year == Year.y2016:
            self._prefix = "201608"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"rts2016-batch-tweets2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"rts2016-batch-clusters.json")
            self._qrel_file = os.path.join(self._eval_dir,"qrels.txt")
            self._topic_file = None

        elif self._year == Year.y2011:
            self._prefix_mon = "201101"
            self._prefix_feb = "201102"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2day")
            self._cluster_file = os.path.join(self._eval_dir,"cluster.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels")
            self._topic_file = os.path.join(self._eval_dir,"topics")

        else:
            raise NotImplementedError("Year %s is not implemented!" %(self._year.name))

        self._t2day = T2Day(self._tweet2day_file,year=self._year)
        self._sema_cluster = SemaCluster(self._cluster_file,self._t2day,self._year)
        self._days = Days(self._qrel_file,self._year,self._topic_file).days
        self._qrel = Qrel(self._qrel_file,self._days,year=self._year)
        self._judged_qids = self._qrel.qids



    @property
    def days(self):
        return self._days
    


def read_results(result_dir,eval_data):
    results = {}
    all_days = set()
    for qid in eval_data._days:
        for day in eval_data._days[qid]:
            all_days.add(day)

    for day in os.walk(result_dir).next()[2]:
        if day not in all_days:
            continue
        day_result_file = os.path.join(result_dir,day)
        results[day] = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in eval_data._judged_qids:
                    if qid not in results[day]:
                        results[day][qid] = []
                    if (len(results[day][qid])<10):
                        results[day][qid].append(line)
    return results

class Classifier(object):
    """
    load the classifier and the feature data
    """


    def __init__(self,feature_descrption_list,
                 use_result,result_expansion,top_dest_dir,retrieval_method):
        self._feature_descrption_list = feature_descrption_list

        self._use_result,self._result_expansion = use_result,result_expansion

        self._top_dest_dir = top_dest_dir
        self._retrieval_method = retrieval_method


    
    def _find_dir(self):
        # according to the features, expansion, and whether to use result
        # to find the dir of the dir to load data
        dest_dir_name =  "_".join([convert_feature_string(i) for i in sorted(self._feature_descrption_list) ])
        if self._use_result:
            dest_dir_name += "_W_result"
        else:
            dest_dir_name += "_Wo_result"
        dest_dir_name += "_"+self._result_expansion.name.title()
        dest_dir = os.path.join(self._top_dest_dir,self._retrieval_method.name,dest_dir_name)
        
        


        self._testing_dir = os.path.join(dest_dir,"testing")
        self._training_dir = os.path.join(dest_dir,"training")

    def _load_data(self):
        feature_dict_file = os.path.join(self._testing_dir,"data","feature_dict")
        classifier_file = os.path.join(self._training_dir,"model","clf")
        
        self._feature_data = json.load(open(feature_dict_file))
        self._classifier = cPickle.load(open(classifier_file))

    def _get_year_day_qid_map(self):
        self._year_day_qid_map = {}
        years = self._feature_data.keys()

        

        for year in years:
            day_qid_map = {}
            one_feature_map = self._feature_data[year][self._feature_descrption_list[0]]
            for day in one_feature_map:
                day_qid_map[day] = one_feature_map[day].keys()
            self._year_day_qid_map[year] = day_qid_map


    def gene_classification_result(self):
        self._find_dir()
        self._load_data()
        self._get_year_day_qid_map()

        index = 0
        feature_vector = []
        feature_vector_index_map = {}
        for year in self._year_day_qid_map:
            feature_vector_index_map[year] = {}
            for day in self._year_day_qid_map[year]:
                feature_vector_index_map[year][day] = {}
                for qid in self._year_day_qid_map[year][day]:

                    single_vector = []
                    for feature in sorted(self._feature_descrption_list):
                        # print year, feature, day,qid
                        single_vector.append( self._feature_data[year][feature][day][qid] )
                    feature_vector.append(single_vector)
                    feature_vector_index_map[year][day][qid] = index
                    index += 1

        predicted_vector = self._classifier.predict(feature_vector)
        self._predicted_silent_days = {}

        for year in feature_vector_index_map:
            self._predicted_silent_days[year] = {}
            for day in feature_vector_index_map[year]:
                self._predicted_silent_days[year][day] = {}
                for qid in feature_vector_index_map[year][day]:
                    index = feature_vector_index_map[year][day][qid]
                    self._predicted_silent_days[year][day][qid] = (predicted_vector[index] == 1)
        # print self._predicted_silent_days
    def is_silent_day(self,year,day,qid):
        # print year,day,qid
        return self._predicted_silent_days[year][day][qid]




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use_result","-ur",action="store_true")
    parser.add_argument("--gene_original","-gn",action="store_true")
    parser.add_argument("--top_dest_dir","-td",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/predictor_analysis/sday_prediction_data")
    parser.add_argument("--result_expansion","-re",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
        """)
    parser.add_argument("--feature_descrption_list","-f",nargs='+')
    parser.add_argument("new_result_dir")
    args=parser.parse_args()

    args.result_expansion = Expansion(args.result_expansion)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)

    

    results = {}
    result_dir_2015 = R_DIR[Year.y2015][args.result_expansion][args.retrieval_method]
    eval_data_2015 = EvalData(Year.y2015)
    results[Year.y2015] = read_results(result_dir_2015,eval_data_2015)

    result_dir_2016 = R_DIR[Year.y2016][args.result_expansion][args.retrieval_method]
    eval_data_2016 = EvalData(Year.y2016)
    results[Year.y2016] = read_results(result_dir_2016,eval_data_2016)

    if not args.gene_original:
        print args.feature_descrption_list
        classifier = Classifier(
                            args.feature_descrption_list,args.use_result,
                            args.result_expansion,args.top_dest_dir,
                            args.retrieval_method)
        classifier.gene_classification_result()
    # print results
    for year in results:
        new_result_file = os.path.join(args.new_result_dir,year.name)
        with open(new_result_file,"w") as of:
            for day in sorted(results[year].keys()):
                for qid in results[year][day]:
                    is_silent = True
                    if args.gene_original:
                        is_silent = False
                    elif not classifier.is_silent_day("Year."+year.name,day,qid):
                        is_silent = False

                    if  not is_silent:  
                        if year==Year.y2016:
                            day_string = "201608%s" %(day.zfill(2))
                        else:
                            day_string = "201507%s" %(day.zfill(2))

                        for line in results[year][day][qid]:
                            of.write("%s %s\n" %(day_string,line))





if __name__=="__main__":
    main()

