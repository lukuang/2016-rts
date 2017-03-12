"""
calculate predictors
"""

import os
import json
import sys
import re
import argparse
import codecs
from abc import ABCMeta,abstractmethod
import subprocess
import numpy as np

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,Year

class PredictorUsingOnlyIndri(object):
    """
    base class for predictor using Indri code
    """
    __metaclass__ = ABCMeta

    def __init__(self,qrel,top_index_dir,query_dir,bin_file):
        self._qrel, self._top_index_dir, self._query_dir = qrel,top_index_dir,query_dir
        self._bin_file = bin_file
        self._judged_qids = self._qrel.qids
        self._values = {}


    def _get_values(self):
        for day in sorted(os.walk(self._query_dir).next()[2]):
            day_index_dir = os.path.join(self._top_index_dir,day)
            day_query_file = os.path.join(self._query_dir,day)
            daily_value = self._compute_daily_value(day_index_dir,day_query_file)       
            self._values[day] = daily_value

    @abstractmethod
    def _compute_daily_value(day_index_dir,day_query_file):
        pass

    @property
    def values(self):
        if not self._values:
            self._get_values()

        return self._values

    def show(self):
        print self.values


class PredictorUsingOnlyResult(object):
    """ 
    base class of performance predictor
    using only the results
    """
    __metaclass__ = ABCMeta

    def __init__(self,qrel,result_dir):
        self._qrel, self._result_dir = qrel, result_dir
        self._judged_qids = self._qrel.qids
        self._days = self._qrel.days

        self._values = {}


    def _get_values(self):
        for day in sorted(os.walk(self._result_dir).next()[2]):
            day_result_file = os.path.join(self._result_dir,day)
            daily_value = self._compute_daily_value(day_result_file)       
            self._values[day] = daily_value

    @abstractmethod
    def _compute_daily_value(day_result_file):
        pass

    @property
    def values(self):
        if not self._values:
            self._get_values()

        return self._values

    def show(self):
        print self.values


class Clarity(PredictorUsingOnlyIndri):
    """
    Clarity score
    """

    def _compute_daily_value(self,day_index_dir,day_query_file):
        day_clarity = {}
        run_command = "%s -index=%s -query=%s -rule=\"method:f2exp,s:0.1\"" %(self._bin_file,day_index_dir,day_query_file)
        # print "command being run:\n%s" %(run_command)
        p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
        
        while True:
            line = p.stdout.readline()
            if line != '':
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid not in self._judged_qids:
                    continue
                day_clarity[qid] = float(parts[1])
                

            else:
                break 
        return day_clarity


class AverageIDF(PredictorUsingOnlyIndri):
    """
    avarge idf score of queries
    """
        
    def _compute_daily_value(self,day_index_dir,day_query_file):
        day_average_idf = {}
        run_command = "%s -index=%s -query=%s " %(self._bin_file,day_index_dir,day_query_file)
        # print "command being run:\n%s" %(run_command)
        p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
        
        while True:
            line = p.stdout.readline()
            if line != '':
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid not in self._judged_qids:
                    continue
                day_average_idf[qid] = float(parts[1])
                

            else:
                break 
        return day_average_idf

class StandardDeviation(PredictorUsingOnlyResult):
    """
    standard deviation of top 10 document scores
    """

    def _compute_daily_value(self,day_result_file):
        scores = {}
        daily_value = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in self._judged_qids:
                    if qid not in scores:
                        scores[qid] = []
                    if len(scores[qid]) >=10 :
                        continue
                    single_score = float( parts[4] )
                    scores[qid].append(single_score)

        for qid in scores:
            daily_value[qid] = np.std(scores[qid], dtype=np.float64)

        return daily_value

class NormalizedStandardDeviation(PredictorUsingOnlyResult):
    """
    standard deviation of top 10 document scores
    """

    def _compute_daily_value(self,day_result_file):
        scores = {}
        top_score = {}
        daily_value = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in self._judged_qids:
                    if qid not in scores:
                        scores[qid] = []
                        top_score[qid] = float( parts[4] )
                    if len(scores[qid]) >=10 :
                        continue
                    single_score = float( parts[4] )
                    if single_score >= 0.5*top_score[qid]:
                        scores[qid].append(single_score)

        for qid in scores:
            daily_value[qid] = np.std(scores[qid], dtype=np.float64)

        return daily_value

class TopScore(PredictorUsingOnlyResult):
    """
    standard deviation of top 10 document scores
    """

    def _compute_daily_value(self,day_result_file):
        daily_value = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in self._judged_qids:
                    if qid not in daily_value:
                        daily_value[qid] = float( parts[4] )
                    


        return daily_value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin_file","-bf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("--index_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed/")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/static/")
    parser.add_argument("--predictor_choice","-pc",choices=range(4),default=0,type=int,
        help="""
            Choose the predictor:
                0: clarity
                1: average idf
                2: DEV
                3: NDEV
        """)
    args=parser.parse_args()

    qrel_file = "/infolab/node4/lukuang/2015-RTS/src/2016/eval/qrels.txt"
    qrel = Qrel(qrel_file,is_16=True)
    if args.predictor_choice == 0:
        predictor = Clarity(qrel,args.index_dir,args.query_dir,args.bin_file)
    elif args.predictor_choice == 1:
        predictor = AverageIDF(qrel,args.index_dir,args.query_dir,args.bin_file)
    predictor.show()
    

if __name__=="__main__":
    main()

