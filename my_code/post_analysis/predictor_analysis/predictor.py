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



def get_query_terms(day_query_file):
    query_terms = {}
    with open(day_query_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("^(.+):(.+)$",line)
            if m:
                qid = m.group(1)
                query_string = m.group(2)
                query_string = re.sub("#weight\(","",query_string)
                all_words = re.findall("[a-zA-z_]+",query_string)
                query_terms[qid] = all_words
            else:
                message = "Wrong Format of file %s\n" %(day_query_file)
                message += "at line:\n%s\n" %(line)
                raise RuntimeError(message)

    return query_terms


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
    def _compute_daily_value(self,day_index_dir,day_query_file):
        pass

    @property
    def values(self):
        if not self._values:
            self._get_values()

        return self._values

    def show(self):
        print self.values

class PredictorUsingLink(object):
    """
    base class for predictor using Indri code
    """
    __metaclass__ = ABCMeta

    def __init__(self,qrel,top_index_dir,query_dir,link_dir,bin_file):
        self._qrel, self._top_index_dir, self._query_dir, self._link_dir=\
            qrel,top_index_dir,query_dir,link_dir
        self._bin_file = bin_file
        self._judged_qids = self._qrel.qids
        self._values = {}


    def _get_values(self):
        for day in sorted(os.walk(self._query_dir).next()[2]):
            day_index_dir = os.path.join(self._top_index_dir,day)
            day_query_file = os.path.join(self._query_dir,day)
            day_link_file = os.path.join(self._link_dir,day)
            daily_value = self._compute_daily_value(day_index_dir,day_query_file,day_link_file)       
            self._values[day] = daily_value

    @abstractmethod
    def _compute_daily_value(self,day_index_dir,day_query_file,day_link_file):
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

class PredictorUsingBoth(object):
    """
    base class for predictor using both Indri code
    and results
    """
    __metaclass__ = ABCMeta

    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir):
        self._qrel, self._top_index_dir, self._query_dir = qrel,top_index_dir,query_dir
        self._bin_file = bin_file
        self._result_dir = result_dir
        self._judged_qids = self._qrel.qids
        self._values = {}

    def _get_values(self):
        for day in sorted(os.walk(self._query_dir).next()[2]):
            day_index_dir = os.path.join(self._top_index_dir,day)
            day_query_file = os.path.join(self._query_dir,day)
            day_result_file = os.path.join(self._result_dir,day)
            daily_value = self._compute_daily_value(
                                    day_index_dir,day_query_file,
                                    day_result_file)       
            self._values[day] = daily_value



    @abstractmethod
    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        pass

    @property
    def values(self):
        if not self._values:
            self._get_values()

        return self._values

    def show(self):
        print self.values

class NQC(PredictorUsingBoth):
    """
    normalized standard deviation of top 10 document scores
    STD/collection_score(C)
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(NQC,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._tune_documents = tune_documents

    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        collection_score = {}

        run_command = "%s -index=%s -query=%s" %(self._bin_file,
                                                 day_index_dir,
                                                 day_query_file)

        

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
                collection_score[qid] = float(parts[1])
                

            else:
                break 

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
                    if len(scores[qid]) >=self._tune_documents :
                        continue
                    single_score = float( parts[4] )
                    scores[qid].append(single_score)

        for qid in self._judged_qids:
            if qid in scores:
                daily_value[qid] = np.std(scores[qid], dtype=np.float64)/collection_score[qid]
            else:
                daily_value[qid] = .0
        return daily_value





        return daily_value 


class TreeEstimator(PredictorUsingBoth):
    """
    class to prepare data for the tree-based
    performance estimator, according to the missing
    content paper
    """
    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        term_idf = {}

        run_command = "%s -index=%s -query=%s" %(self._bin_file,
                                                 day_index_dir,
                                                 day_query_file)

        

        # print "command being run:\n%s" %(run_command)
        p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
        
        while True:
            line = p.stdout.readline()
            if line != '':
                line = line.rstrip()
                parts = line.split()
                term = parts[0]
                term_idf[term] = int( parts[1] )
                

            else:
                break 

        results = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in self._judged_qids:
                    if qid not in results:
                        results[qid] = []
                    if len(results[qid]) >=10 :
                        continue
                    document_id = parts[2] 
                    results[qid].append(document_id)

        daily_value = {}


        query_terms = get_query_terms(day_query_file)

        for qid in query_terms:
            if qid not in self._judged_qids:
                continue

            query_value_pairs = []
            
            # print "terms of %s" %(qid)
            # print query_terms[qid]
            for term in query_terms[qid]:

                # ignore terms that are not computed idf (stopwords)
                if term not in term_idf:
                    continue

                over_lap_count = 0
                run_query_command = "IndriRunQuery -index=%s -query=%s -trecFormat=true -count=10 -rule=\"method:f2exp,s:0.1\" " %(day_index_dir,
                                                                                                                                   term)

        

                # print "command being run:\n%s" %(run_query_command)
                p = subprocess.Popen(run_query_command,stdout=subprocess.PIPE,shell=True)

                # if qid not in results, meaning no documents returned for
                # the query of the day, there will be no overlaps
                if qid in results:
                    while True:
                        line = p.stdout.readline()
                        if line != '':
                            line = line.rstrip()
                            parts = line.split()
                            did = parts[2]

                            if did in results[qid]:
                                over_lap_count += 1
                        else:
                            break

                query_value_pairs.append( [over_lap_count,term_idf[term]] )
            
            
            query_value_pairs = sorted(query_value_pairs,key=lambda x:x[1])

            daily_value[qid] = query_value_pairs

        return daily_value
             


class LinkTermRelatedness(PredictorUsingLink):
    """
    Using the link produced by stanford parser for queries
    to generate the term relatedness representation of the queries
    """
    def _compute_daily_value(self,day_index_dir,day_query_file,day_link_file):
        daily_value = {}

        run_command = "%s -index=%s -query=%s -link=%s" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_link_file)

        

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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value

class WIG(PredictorUsingBoth):
    """
    compute weighted information gain for query
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(WIG,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._tune_documents = tune_documents

    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        daily_value = {}

        run_command = "%s -index=%s -query=%s -result=%s -n=%d" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._tune_documents)

   

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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value 

class PWIG(PredictorUsingBoth):
    """
    compute wig only for phrases
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10,of_lambda=0.5):
        super(WIG,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._tune_documents = tune_documents
        self._of_lambda = of_lambda

    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        daily_value = {}

        run_command = "%s -index=%s -query=%s -result=%s -tune_documents=%d -of_lambda=%f" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._tune_documents,
                                                            self._of_lambda)

   

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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value 

class LocalTermRelatedness(PredictorUsingBoth):
    """
    compute loca term relatedness (pmi)
    """

    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,cu):
        super(LocalTermRelatedness,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._cu = cu

    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        daily_value = {}

        run_command = "%s -index=%s -query=%s -result=%s -cu=%s" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._cu)

   

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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value 

class LocalTermRelatednessAverage(LocalTermRelatedness):
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir):
        super(LocalTermRelatednessAverage,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"average")

class LocalTermRelatednessMax(LocalTermRelatedness):
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir):
        super(LocalTermRelatednessMax,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"max")



class LocalCoherenceWeigheted(PredictorUsingBoth):
    """
    Base class for computing weighted coherence
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,cu,weight,tn=None,tune_documents=10):
        super(LocalCoherenceWeigheted, self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._weight=weight
        self._cu=cu
        self._tn = tn
        self._tune_documents = tune_documents

    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        daily_value = {}

        run_command = "%s -index=%s -query=%s -result=%s -cu=%s -weight=%s -tune_documents=%d" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._cu,
                                                            self._weight,
                                                            self._tune_documents)

        if self._tn:
            run_command += " -tn=%d" %(self._tn)

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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value 

class LocalCoherenceWeighetedBinary(LocalCoherenceWeigheted):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,weight,tn=None,tune_documents=10):
        super(LocalCoherenceWeighetedBinary,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"binary",weight,tn=tn,tune_documents=tune_documents)


class LocalCoherenceWeighetedAverage(LocalCoherenceWeigheted):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,weight,tn=None,tune_documents=10):
        super(LocalCoherenceWeighetedAverage,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"average",weight,tn=tn,tune_documents=tune_documents)


class LocalCoherenceWeighetedMax(LocalCoherenceWeigheted):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,weight,tn=None,tune_documents=10):
        super(LocalCoherenceWeighetedMax,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"max",weight,tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedBinary(LocalCoherenceWeighetedBinary):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn=None,tune_documents=10):
        super(LocalCoherenceIDFWeighetedBinary,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"idf",tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedAverage(LocalCoherenceWeighetedAverage):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn=None,tune_documents=10):
        super(LocalCoherenceIDFWeighetedAverage,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"idf",tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedMax(LocalCoherenceWeighetedMax):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn=None,tune_documents=10):
        super(LocalCoherenceIDFWeighetedMax,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"idf",tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedBinaryN(LocalCoherenceIDFWeighetedBinary):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceIDFWeighetedBinaryN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedAverageN(LocalCoherenceIDFWeighetedAverage):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceIDFWeighetedAverageN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,tn=tn,tune_documents=tune_documents)


class LocalCoherenceIDFWeighetedMaxN(LocalCoherenceIDFWeighetedMax):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceIDFWeighetedMaxN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,tn=tn,tune_documents=tune_documents)




class LocalCoherencePMIWeighetedBinary(LocalCoherenceWeighetedBinary):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherencePMIWeighetedBinary,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"pmi",tn=2,tune_documents=tune_documents)


class LocalCoherencePMIWeighetedAverage(LocalCoherenceWeighetedAverage):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherencePMIWeighetedAverage,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"pmi",tn=2,tune_documents=tune_documents)


class LocalCoherencePMIWeighetedMax(LocalCoherenceWeighetedMax):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherencePMIWeighetedMax,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"pmi",tn=2,tune_documents=tune_documents)



###################

class LocalCoherenceUnweigheted(PredictorUsingBoth):
    """Compute unweigheted query local coherence.
    """

    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,cu,tune_documents=10):
        super(LocalCoherenceUnweigheted, self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._tune_documents = tune_documents
        self._cu=cu


    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        day_clarity = {}
        run_command = "%s -index=%s -query=%s -result=%s -cu=%s -tune_documents=%d" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._cu,
                                                            self._tune_documents)
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

class LocalCoherenceUnweighetedBinary(LocalCoherenceUnweigheted):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherenceUnweighetedBinary,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"binary",tune_documents=tune_documents)


class LocalCoherenceUnweighetedAverage(LocalCoherenceUnweigheted):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherenceUnweighetedAverage,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"average",tune_documents=tune_documents)


class LocalCoherenceUnweighetedMax(LocalCoherenceUnweigheted):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tune_documents=10):
        super(LocalCoherenceUnweighetedMax,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"max",tune_documents=tune_documents)

class LocalCoherenceUnweighetedN(PredictorUsingBoth):
    """Compute unweigheted query local coherence given the
    size of terms tn
    """

    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,cu,tn,tune_documents=10):
        super(LocalCoherenceUnweighetedN, self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir)
        self._cu = cu
        self._tn = tn
        self._tune_documents=tune_documents


    def _compute_daily_value(self,day_index_dir,day_query_file,
                             day_result_file):
        day_clarity = {}
        run_command = "%s -index=%s -query=%s -result=%s -cu=%s -tn=%d -tune_documents=%d" %(self._bin_file,
                                                            day_index_dir,
                                                            day_query_file,
                                                            day_result_file,
                                                            self._cu,
                                                            self._tn,
                                                            self._tune_documents)
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

class LocalCoherenceUnweighetedBinaryN(LocalCoherenceUnweighetedN):
    """local coherence with binary co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceUnweighetedBinaryN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"binary",tn,tune_documents=tune_documents)


class LocalCoherenceUnweighetedAverageN(LocalCoherenceUnweighetedN):
    """local coherence with average co-occurrence count
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceUnweighetedAverageN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"average",tn,tune_documents=tune_documents)


class LocalCoherenceUnweighetedMaxN(LocalCoherenceUnweighetedN):
    """
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,result_dir,tn,tune_documents=10):
        super(LocalCoherenceUnweighetedMaxN,self).__init__(qrel,top_index_dir,query_dir,bin_file,result_dir,"max",tn,tune_documents=tune_documents)


class SCQ(PredictorUsingOnlyIndri):
    """
    SCQ score
    """

    def _compute_daily_value(self,day_index_dir,day_query_file):
        daily_value = {}
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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value

class VAR(SCQ):
    """
    compute the variance of the terms of query
    """
    pass


class Clarity(PredictorUsingOnlyIndri):
    """
    Clarity score
    """
    
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,tune_documents=10,tune_terms=5):
        super(Clarity,self).__init__(qrel,top_index_dir,query_dir,bin_file)
        self._tune_documents,self._tune_terms = tune_documents,tune_terms

    def _compute_daily_value(self,day_index_dir,day_query_file):
        day_clarity = {}
        run_command = "%s -index=%s -query=%s -rule=\"method:f2exp,s:0.1\" -documents=%d -terms=%d" %(self._bin_file,
                                                                                                      day_index_dir,
                                                                                                      day_query_file,
                                                                                                      self._tune_documents,
                                                                                                      self._tune_terms)
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


class MSTTermRelatedness(PredictorUsingOnlyIndri):
    """
    compute the mst based term relatedness
    """
        
    def _compute_daily_value(self,day_index_dir,day_query_file):
        daily_value = {}
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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value


class QueryLength(PredictorUsingOnlyIndri):
    """
    avarge idf score of queries
    """
        
    def _compute_daily_value(self,day_index_dir,day_query_file):
        daily_value = {}
        run_command = "%s -query=%s -index=%s" %(self._bin_file,day_query_file,day_index_dir)
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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value

class CandidateSize(QueryLength):
    """
    get the size of candidate documents(document with at least one
    query term)
    """
    pass

class TermRelatedness(PredictorUsingOnlyIndri):
    """
    term relatedness
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file,cu):
        super(TermRelatedness,self).__init__(qrel,top_index_dir,query_dir,bin_file)
        self._cu = cu
        
    def _compute_daily_value(self,day_index_dir,day_query_file):
        daily_value = {}
        run_command = "%s -index=%s -query=%s -cu=%s" %(self._bin_file,
                                                        day_index_dir,
                                                        day_query_file,
                                                        self._cu)
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
                daily_value[qid] = float(parts[1])
                

            else:
                break 
        return daily_value

class AvgPMI(TermRelatedness):
    """
    average pmi(term relatedness)
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file):
        super(AvgPMI,self).__init__(qrel,top_index_dir,query_dir,bin_file,"average")


class AvgIDFWeightedPMI(AvgPMI):
    """
    average idf weighted pmi(term relatedness)
    """
    pass

class MaxPMI(TermRelatedness):
    """
    average pmi(term relatedness)
    """
    def __init__(self,qrel,top_index_dir,query_dir,bin_file):
        super(MaxPMI,self).__init__(qrel,top_index_dir,query_dir,bin_file,"max")
 

class MaxIDFWeightedPMI(MaxPMI):
    """
    max idf weighted pmi(term relatedness)
    """
    pass 


class StandardDeviation(PredictorUsingOnlyResult):
    """
    standard deviation of top document scores
    """
    def __init__(self,qrel,result_dir,tune_documents=10):
        super(StandardDeviation,self).__init__(qrel,result_dir)
        self._tune_documents = tune_documents

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
                    if len(scores[qid]) >=self._tune_documents :
                        continue
                    single_score = float( parts[4] )
                    scores[qid].append(single_score)

        for qid in self._judged_qids:
            if qid in scores:
                daily_value[qid] = np.std(scores[qid], dtype=np.float64)
            else:
                daily_value[qid] = .0
        return daily_value

class NormalizedStandardDeviation(PredictorUsingOnlyResult):
    """
    normalized standard deviation of top document scores
    """
    def __init__(self,qrel,result_dir,tune_documents=10):
        super(NormalizedStandardDeviation,self).__init__(qrel,result_dir)
        self._tune_documents = tune_documents

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
                    if len(scores[qid]) >=self._tune_documents :
                        continue
                    single_score = float( parts[4] )
                    if single_score >= 0.5*top_score[qid]:
                        scores[qid].append(single_score)

        for qid in self._judged_qids:
            if qid in scores:
                daily_value[qid] = np.std(scores[qid], dtype=np.float64)
            else:
                daily_value[qid] = .0
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
                    
        for qid in self._judged_qids:
            if qid not in daily_value:
                daily_value[qid] = .0

        return daily_value


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin_file","-bf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("--index_dir","-id",default="/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed/")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/reparsed/clarity_queries/static/")
    parser.add_argument("--predictor_choice","-pc",choices=range(4),default=0,type=int,
        help="""
            Choose the predictor:
                0: clarity
                1: average idf
                2: dev
                3: ndev
                4: top_score
                5: coherence_binary
                6: coherence_average
                7: coherence_max
                8: coherence_binary_n
                9: coherence_average_n
                10: coherence_max_n 
                11: query_length
                12: avg_pmi
                13: max_pmi
                14: cidf_binary
                15: cidf_average
                16: cidf_max
                17: cidf_binary_n
                18: cidf_average_n
                19: cidf_max_n 
                20: cpmi_binary
                21: cpmi_average
                22: cpmi_max
                23: mst_term_relatedness
                24: link_term_relatedness
                25: scq
                26: var
                27: nqc
                28: wig
                29: pwig
                30: local_avg_pmi
                31: local_max_pmi
                32: aidf_pmi
                33: midf_pmi
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
    _main()

