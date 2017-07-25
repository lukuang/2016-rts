"""
build index and run queries and send result to broker
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
import subprocess
import requests
import cPickle
from datetime import timedelta
import logging
import logging.handlers


from myUtility.misc import gene_indri_index_para_file

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.broker_communication import BrokerCommunicator

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis")
from predictor import *
from plot_silentDay_predictor import *

class FakeQrel(object):
    def __init__(self,qids):
        self.qids = qids
        self.days = None

class Models(object):
    def __init__(self,sub_model_dir):
        single_term_model_file = os.path.join(sub_model_dir,"single_term")
        multi_term_model_file = os.path.join(sub_model_dir,"multi_term")
        self.single_term_model = cPickle.load(open(single_term_model_file))
        self.multi_term_model = cPickle.load(open(multi_term_model_file))

class Detector(object):
    def __init__(self,models,single_term_qids,
                 single_term_feature_list,multi_term_qids,
                 multi_term_feature_list):

        self._models = models
        self._single_term_qids = single_term_qids
        self._multi_term_qids = multi_term_qids

        self.single_feature_order = get_feature_order(single_term_feature_list)
        self.multi_feature_order = get_feature_order(multi_term_feature_list)


    def make_descision(self,single_term_predictor_values,muti_term_predictor_values):
        descisions = {}
        single_X = []
        for qid in self._single_term_qids:
            single_feature_vector = []
            for feature in self.single_feature_order:
                try:
                    single_feature_vector.append(single_term_predictor_values[feature][qid])
                except KeyError:
                    print "Key Error:"
                    print "%s,%s" %(qid,feature.name)
                    single_feature_vector.append(.0)
            single_X.append(single_feature_vector)

        single_y = self._models.single_term_model.predict(single_X)

        for i in range(len(self._single_term_qids)): 
            qid = self._single_term_qids[i]
            is_silent = single_y[i]
            descisions[qid] = is_silent

        multi_X = []
        for qid in self._multi_term_qids:
            single_feature_vector = []
            for feature in self.multi_feature_order:
                try:
                    single_feature_vector.append(muti_term_predictor_values[feature][qid])
                except KeyError:
                    print "Key Error:"
                    print "%s,%s" %(qid,feature.name)
                    single_feature_vector.append(.0)
            multi_X.append(single_feature_vector)

        multi_y = self._models.multi_term_model.predict(multi_X)

        for i in range(len(self._multi_term_qids)): 
            qid = self._multi_term_qids[i]
            is_silent = multi_y[i]
            descisions[qid] = is_silent
        return descisions





class Run(object):
    """run class
    """
    def __init__(self,run_name,index_dir,posted_result_dir):
        self._run_name, self._index_dir, self._posted_result_dir=\
            run_name, index_dir, posted_result_dir
        self._posted_result_file = os.path.join(self._posted_result_dir,self._run_name)
        self._results = {}
        self._posted_results = {}
        if os.path.exists(self._posted_result_file):
            self._posted_results = json.load(open(self._posted_result_file))




  



    def process_new_results(self,new_results,date,
                            previous_results,decisions):

        date_index_dir = os.path.join(self._index_dir,date)
        self._results[date] = {}
        for qid in new_results:
            self._results[date][qid] = []
                
            if decisions[qid]==0:
                #check redundancy
                for tid in new_results[qid]:
                    t_text = get_text(date_index_dir,tid)
                    if not previous_results.is_redundant(t_text,self._run_name,qid):
                        self._results[date][qid].append(tid)
                        #stop posting tweets for a query if 1 tweets already
                        #posted
                        if len(self._results[date][qid]) == 1:
                            break


    def results_to_post(self,date,qid):
        try:
            posting_results = self._results[date][qid]
        except KeyError:
            posting_results = []
        return posting_results

   

    def store_posted_results(self,posted_results,date):
        self._posted_results[date] = posted_results

        with open(self._posted_result_file,"w") as f:
            f.write(json.dumps(self._posted_results))


class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,previous_result_file,debug=False):
        self._previous_result_file = previous_result_file
        self._debug = debug
        self._load_previous_results()
        

    def _load_previous_results(self):
        self._previous_results = {}
        if os.path.exists(self._previous_result_file):
            f_size = os.stat(self._previous_result_file).st_size
            if f_size!=0:
                self._previous_results =\
                    json.load(open(self._previous_result_file))


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
        if term_diff >= 0.500000:
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


    def store_previous(self):
        with open(self._previous_result_file,'w') as f:
            f.write(json.dumps(self._previous_results))


def get_feature_order(feature_list):
    name_feature_map = {}
    feature_order = []
    for feature in feature_list:
        name = feature.name
        name_feature_map[name] = feature

    for name in sorted(name_feature_map.keys()):
        feature_order.append(name_feature_map[name])

    return feature_order

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

def separate_qids(topic_file):
    single_term_qids = []
    multi_term_qids = []

    topics = json.load(open(topic_file))
    for a_topic in topics:
        qid = a_topic["topid"]
        q_string = a_topic['title']
        if len(re.findall("\w+",q_string)) == 1:
            single_term_qids.append(qid)
        else:
            multi_term_qids.append(qid)

        
    return single_term_qids, multi_term_qids


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) 

def need_wait():
    # compute how many secs need to wait before next run for next
    # da. Run it everyday 23:00
    time_struct =  time.gmtime() 
    if time_struct.tm_hour == 23:
        wait_hours = 23
    else:
        wait_hours = 22 - time_struct.tm_hour
    
    wait_minutes = 60 - time_struct.tm_min
    
    total_secs = timedelta(hours=wait_hours,minutes=wait_minutes).total_seconds()
    
    print "now is %s" %(now())
    print "need to wait %d hours %d minutes, which is %f seconds" %(wait_hours,wait_minutes,total_secs)
    return int(total_secs)


def get_day_hour_from_file_name(hour_text_file):
    if hour_text_file == "status.log":
        return 0,0
    m = re.search("\d+\-\d+\-(\d+)_(\d+)",hour_text_file)
    if m is None:
        raise ValueError("file name %s not supported!" %(hour_text_file))
    else:
        return m.group(1),m.group(2)


def check_file_time(hour_text_file,date):

    file_date,file_hour = get_day_hour_from_file_name(hour_text_file)
    #print file_date,date
    if int(file_date) == int(date):
        return True
    return False

def get_file_list(text_dir,date):
    all_files = os.walk(text_dir).next()[2]
    all_files.sort() # solely for debuging purpose
    file_list = []
    for hour_text_file in all_files:
        #print hour_text_file
        if check_file_time(hour_text_file,date):
            
            file_list.append(os.path.join(text_dir,hour_text_file))
    
    return file_list
    


def build_index(index_dir,para_dir,text_dir,date):
    file_list = get_file_list(text_dir,date)
    if len(file_list)!= 23:
        print "wait 10 miniutes since the text files are not all ready(probably missing 22)"
        time.sleep(600)
    file_list = get_file_list(text_dir,date)
    if len(file_list)!= 23:
        print "Warning: there are still %d files!" %(len(file_list))
        print file_list
    index_para_file = os.path.join(para_dir,date)
    index_path = os.path.join(index_dir,date)

    gene_indri_index_para_file(file_list,index_para_file,
                    index_path)

    os.system("IndriBuildIndex %s" %index_para_file)


def run_single_query(query_file,result_file):
    results = {}
    print "run query file %s" %(query_file)
    p = subprocess.Popen(["IndriRunQuery", query_file],  stdout=subprocess.PIPE)
    output = p.communicate()[0]

    # write to result files
    with open(result_file,"w") as of:
        of.write(output)

    sentences  =  output.split("\n")
    for s in sentences:
        if len(s)==0:
            continue
        parts = s.strip().split()
        qid = parts[0]
        tid = parts[2]
        if qid not in results:
            results[qid] = []
        results[qid].append( tid )

    return results


def run_query(date,query_dir,result_dir):
    
    raw_query_file = os.path.join(query_dir,"raw_%s" %(date))
    expanded_query_file = os.path.join(query_dir,"expanded_%s" %(date))
    raw_result_file = os.path.join(result_dir,"raw",date)
    expanded_result_file = os.path.join(result_dir,"expanded",date)


    raw_results = run_single_query(raw_query_file,raw_result_file)
    expanded_results = run_single_query(expanded_query_file,expanded_result_file)
    # expanded_results = {}
    return raw_results, expanded_results



def get_predictor_values(date,qids,feature_list,query_dir,result_dir,index_dir):
    predictor_values = {}
    for feature_name in feature_list:
        bin_file = BIN_FILES[feature_name]
        fake_qrel = FakeQrel(qids)
        link_dir = None
        predictor = gene_predictor(feature_name,fake_qrel,
                   index_dir,query_dir,result_dir,
                   bin_file,link_dir,"/tmp/kuang_rts_feature",
                   0,RetrievalMethod.f2exp)
        day_value = predictor.get_day_value(date)
        predictor_values[feature_name] = day_value

    return predictor_values
    


def generate_output(raw_results,expanded_results,date,
                    communicator,logger,runs,all_qids,
                    with_result_decisions,without_result_decisions,
                    previous_results):
    

    print "process UDInfoBL results"
    runs["UDInfoBL"].process_new_results(raw_results,date,
                            previous_results,without_result_decisions)
    print "process UDInfoSDWR results"
    runs["UDInfoSDWR"].process_new_results(raw_results,date,
                            previous_results,with_result_decisions)
    print "process UDInfoEXP results"
    runs["UDInfoEXP"].process_new_results(expanded_results,date,
                            previous_results,without_result_decisions)


    print "post results"
    for run_name in runs:
        rejected = {}
        count = 0
        posted_results = {}
        for qid in all_qids:
            posted_results[qid]  = []        
            for tid in runs[run_name].results_to_post(date,qid):
        
                return_url, status_code = communicator.post_tweet(run_name,qid,tid)
                if status_code == requests.codes.no_content:

                    count += 1
                    posted_results[qid].append(tid)
                    
                    
                else:
                    error_code = status_code
                    if error_code not in rejected:
                        rejected[error_code] = 0
                    rejected[error_code] += 1

        print "post %d tweets for run %s" %(count,run_name)
        runs[run_name].store_posted_results(posted_results,date)
        if rejected:
            for e_code in rejected:
                error_message = "%s:\nrejected %d tweets with error code: %s for run %s" %(now(),rejected[e_code],e_code,run_name)
                print error_message
                logger.warn(error_message+"\n")

    
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2017-rts/data/index")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2017-rts/data/queries")
    parser.add_argument("--text_dir","-tr",default="/infolab/headnode2/lukuang/2017-rts/data/raw/first/text")
    parser.add_argument("--result_dir","-rr",default="/infolab/headnode2/lukuang/2017-rts/data/result")
    parser.add_argument("--para_dir","-pr",default="/infolab/headnode2/lukuang/2017-rts/data/para")
    parser.add_argument("--posted_result_dir","-prr",default="/infolab/headnode2/lukuang/2017-rts/data/posted_results")
    parser.add_argument("--clarity_query_dir","-cqr",default="/infolab/headnode2/lukuang/2017-rts/data/clarity_queries")
    parser.add_argument("--model_dir","-mr",default="/infolab/headnode2/lukuang/2017-rts/data/models")
    parser.add_argument("--previous_result_file","-prf",default="/infolab/headnode2/lukuang/2017-rts/data/previous_results")
    parser.add_argument("--coeff_dir","-cor",default="/infolab/headnode2/lukuang/2017-rts/data/threshold_coeff")
    parser.add_argument("--threshold_dir","-thr",default="/infolab/headnode2/lukuang/2017-rts/data/threshold")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2017-rts/data/communication")
    args=parser.parse_args()

    #('average_idf:raw', 'scq:raw', 'var:raw', 'max_pmi:raw', 'avg_pmi:raw', 'dev:raw', 'ndev:raw', 'nqc:raw', 'wig:raw', 'top_score:raw', 'clarity:raw', 'qf:raw')
    
    
    # prepare warning log
    logger = logging.getLogger('runLogger')
    warningHandler = logging.FileHandler('run_warning.log')
    warningHandler.setLevel(logging.WARN)
    logger.addHandler(warningHandler)
    logging.captureWarnings(True);

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.WARN)
    logger.addHandler(consoleHandler)

    logger.setLevel(logging.WARN)

    print "Start at %s" %now()

    print "Set up communicator"
    basic_file = os.path.join(args.communication_dir,"basic")
    run_name_file = os.path.join(args.communication_dir,"runs")
    topic_file = os.path.join(args.communication_dir,"topics")

    
    communicator = BrokerCommunicator(basic_file,
                        run_name_file,topic_file)

    print "Register/setup runs:"


    runs = {
        "UDInfoBL":Run("UDInfoBL",args.index_dir,args.posted_result_dir ),
        "UDInfoSDWR":Run("UDInfoSDWR",args.index_dir,args.posted_result_dir),
        "UDInfoEXP":Run("UDInfoEXP",args.index_dir,args.posted_result_dir)
    }

    for name in runs:
        communicator.register_run(name)

    print "Setup previous results"
    previous_results = PreviousResults(args.previous_result_file) 

    print "Find single term queries and setup predictor info"
    single_term_qids, multi_term_qids = separate_qids(topic_file) 
    all_qids = single_term_qids + multi_term_qids

    single_term_with_result_feature_list = [
        PredictorName.average_idf, 
        PredictorName.scq, 
        PredictorName.dev
    ]

    single_term_without_result_feature_list = [
        PredictorName.average_idf, 
        PredictorName.scq, 
        PredictorName.dev, 
        PredictorName.ndev, 
        PredictorName.nqc, 
        PredictorName.qf
    ]

    multi_term_feature_list = [
        PredictorName.coherence_average,
        PredictorName.coherence_binary,
        PredictorName.coherence_max,
        PredictorName.pwig
    ]

    print "load pre-trained models for silent day detection"
    with_result_models = Models(os.path.join(args.model_dir,"with"))
    without_result_models = Models(os.path.join(args.model_dir,"without"))

    with_result_detector = Detector(with_result_models,single_term_qids,
                                    single_term_with_result_feature_list,multi_term_qids,
                                    multi_term_feature_list)

    without_result_detector = Detector(without_result_models,single_term_qids,
                                    single_term_without_result_feature_list,multi_term_qids,
                                    multi_term_feature_list)


    print "wait till 23:00 today first!"
    total_secs = need_wait()    
    time.sleep(total_secs)


    while True:
        #try:
        start = now()
        print "start processing at %s" %start
        date = str(time.gmtime().tm_mday)
        #date='23'
        print "date is %s" %date
        print "build index"
        build_index(args.index_dir,args.para_dir,args.text_dir,date)

        print "run queries"
        raw_results, expanded_results = run_query(date,args.query_dir,args.result_dir)

        print "get predictor values"
        result_dir = os.path.join(args.result_dir,"raw")
        single_term_with_result_predictor_values = get_predictor_values(date,single_term_qids,
                                                            single_term_with_result_feature_list,
                                                            args.clarity_query_dir,
                                                            result_dir,args.index_dir)
        
        single_term_without_result_predictor_values = get_predictor_values(date,single_term_qids,
                                                            single_term_without_result_feature_list,
                                                            args.clarity_query_dir,
                                                            result_dir,args.index_dir)

        muti_term_predictor_values = get_predictor_values(date,multi_term_qids,
                                                            multi_term_feature_list,
                                                            args.clarity_query_dir,
                                                            result_dir,args.index_dir)

        # print single_term_with_result_predictor_values
        # print single_term_without_result_predictor_values
        # print muti_term_predictor_values

        print "make silent day decisions"
        with_result_decisions = with_result_detector.make_descision(
                                        single_term_with_result_predictor_values,
                                        muti_term_predictor_values)
        without_result_decisions = without_result_detector.make_descision(
                                        single_term_without_result_predictor_values,
                                        muti_term_predictor_values)

        # print with_result_decisions
        # print without_result_decisions
        print "generate output"


        generate_output(raw_results,expanded_results,date,
                    communicator,logger,runs,all_qids,
                    with_result_decisions,without_result_decisions,previous_results)
        end = now()

        print "store previous results:"
        previous_results.store_previous()


        print "process of date %s ended" %date
        print "start at:%s\nand end at%s" %(start,end)
        print "-"*20

        total_secs = need_wait()    
        time.sleep(total_secs)
        

        

if __name__=="__main__":
    main()

