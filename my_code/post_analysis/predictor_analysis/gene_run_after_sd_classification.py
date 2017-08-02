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
import subprocess

from plot_silentDay_predictor import PredictorName,Expansion,R_DIR,RetrievalMethod

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year


FULL_IND_DIR = {
    Year.y2015:"/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29",
    Year.y2016:"/infolab/headnode2/lukuang/2016-rts/data/incremental_index"
}

def convert_feature_string(feature_string):
    detail_finder_with_tn = re.search("^(\w+):(\w+):(\d+)$",feature_string)
    if detail_finder_with_tn:
        feature_string = detail_finder_with_tn.group(1)[:-1]+detail_finder_with_tn.group(3)
        feature_string += ":%s" %(detail_finder_with_tn.group(2) )
    feature_string = re.sub(":","_",feature_string)
    feature_string = feature_string[0].upper()+feature_string[1:]
    
    return feature_string


def get_text(index_dir,tid):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tid)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,sim_treshold,debug=False):
        self._sim_treshold, self._debug = sim_treshold, debug
        self._previous_results = {}
        

    


    def _store_tweet(self,tweet_text,run_name,qid):
        if self._debug:
            print "store new tweet %s\nfor query %s run %s"\
                %(tweet_text,qid,run_name)
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
        
        if qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []
        
        self._previous_results[run_name][qid].append(tweet_text)


    def _term_diff(self,tweet_text,t_text):
        words1 = re.findall("\w+",tweet_text)
        words2 = re.findall("\w+",t_text)
        common = list(set(words1).intersection(words2))
        return len(common)*1.0/max(len(words1),len(words2))


    def _check_tweet_redundant(self,tweet_text,t_text):
        if self._debug:
            print "check diff between %s\nand %s" %(tweet_text,t_text)
        term_diff = self._term_diff(tweet_text,t_text)
        if self._debug:
            print "the metric is %f" %(term_diff)
        if term_diff >= self._sim_treshold:
            return True
        else:
            return False



    def is_redundant(self,tweet_text,run_name,qid):
        
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
            self._previous_results[run_name][qid] = []
            
        elif qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []

        
        else:

            for t_text in self._previous_results[run_name][qid]:
                if self._check_tweet_redundant(tweet_text,t_text):
                    if self._debug:
                        print "%s\n is redundant to\n%s" %(tweet_text,t_text)
                        print "-"*20
                    return True

        self._store_tweet(tweet_text,run_name,qid)
        return False


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
    


def read_results(result_dir,eval_data,treshold):
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
                    if (len(results[day][qid])<treshold):
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
        # dest_dir_name += "_"+self._result_expansion.name.title()
        dest_dir_name += "_Raw"
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
    parser.add_argument("--sd_only","-sdo",action="store_true")
    parser.add_argument("--gene_original","-gn",action="store_true")
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--treshold","-t",type=int,default=10)
    parser.add_argument("--sim_treshold","-st",type=float,default=0.5)
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

    print "The sim threshold is %f" %(args.sim_treshold)    

    results = {}
    if args.result_expansion != Expansion.raw:
        result_dir_2015 = R_DIR[Year.y2015][args.result_expansion]
    else:
        result_dir_2015 = R_DIR[Year.y2015][args.result_expansion][args.retrieval_method]
    # print result_dir_2015
    eval_data_2015 = EvalData(Year.y2015)
    results[Year.y2015] = read_results(result_dir_2015,eval_data_2015,args.treshold)

    if args.result_expansion != Expansion.raw:
        result_dir_2016 = R_DIR[Year.y2016][args.result_expansion]
    else:
        result_dir_2016 = R_DIR[Year.y2016][args.result_expansion][args.retrieval_method]
    eval_data_2016 = EvalData(Year.y2016)
    results[Year.y2016] = read_results(result_dir_2016,eval_data_2016,args.treshold)

    if not args.gene_original:
        print args.feature_descrption_list
        classifier = Classifier(
                            args.feature_descrption_list,args.use_result,
                            args.result_expansion,args.top_dest_dir,
                            args.retrieval_method)
        classifier.gene_classification_result()
    # print results
    for year in results:
        # if args.debug:
        print "for year %s" %(year.name)
        year_index_dir = FULL_IND_DIR[year]
        if not args.sd_only:
            previous_results = PreviousResults(args.sim_treshold,args.debug)
        new_result_file = os.path.join(args.new_result_dir,year.name)
        with open(new_result_file,"w") as of:
            for day in sorted(map(int,results[year].keys())):
                # if args.debug:
                day = str(day)
                print "\tprocess day %s" %(day)
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
                            parts = line.strip().split()
                            tid = parts[2]
                            if args.sd_only:
                                of.write("%s %s\n" %(day_string,line))
                            else:
                                t_text = get_text(year_index_dir,tid)
                                if not previous_results.is_redundant(t_text,year.name,qid):
                                    of.write("%s %s\n" %(day_string,line))





if __name__=="__main__":
    main()

