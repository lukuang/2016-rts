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
from datetime import timedelta
import logging
import logging.handlers


from myUtility.misc import gene_indri_index_para_file

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.broker_communication import BrokerCommunicator

class Run(object):
    """run class
    """
    def __init__(self,run_name,coeff_file,index_dir,threshold_dir,posted_result_dir):
        self._run_name, self._coeff_file,self._index_dir=\
            run_name,coeff_file,index_dir
        self._posted_result_dir = posted_result_dir
        self._posted_result_file = os.path.join(self._posted_result_dir,self._run_name)
        self._threshold_file = os.path.join(threshold_dir,run_name)
        self._results = {}
        self._posted_results = {}
        if os.path.exists(self._posted_result_file):
            self._posted_results = json.load(open(self._posted_result_file))
        self._scores = {}
        self._threshold = {}
        self._dates = ["NO"]
        self._get_coeff()
        self._load_threshold()


    def _get_coeff(self):
        self._coeff =  json.load(open(self._coeff_file))

    def _load_threshold(self):
        if os.path.exists(self._threshold_file):
            self._threshold = json.load(open(self._threshold_file))
        dates = self._threshold.keys()
        dates = map(int,dates)
        last_month_dates = []
        this_month_dates = []
        for d in dates:
            if d >10:
                print "add last month date %d" %d
                last_month_dates.append(d)
            else:
                print "add this month date %d" %d
                this_month_dates.append(d)
        last_month_dates.sort()
        this_month_dates.sort()
        for d in last_month_dates:
            d = str(d)
            self._dates.append(d)
        for d in this_month_dates:
            d = str(d)
            self._dates.append(d)
        print "loaded dates:\n%s" %self._dates
        print "loaded thresholds:\n%s" %self._threshold



    def process_new_results(self,new_results,date,
                            previous_results):
        date_index_dir = os.path.join(self._index_dir,date)
        previous_date = self._dates[-1]
        self._dates.append(date)
        self._results[date] = {}
        self._scores[date] = {}
        for qid in new_results:
            self._results[date][qid] = []
            self._scores[date][qid] = []
            for tid,score in new_results[qid]:
                self._scores[date][qid].append(score)
                
                #check threshold
                if previous_date == self._dates[0]:
                    threshold = -1000
                else:
                    threshold = self._threshold[previous_date][qid]
                if score > threshold:
                    #check redundancy
                    t_text = get_text(date_index_dir,tid)
                    if not previous_results.is_redundant(t_text,self._run_name,qid):
                        self._results[date][qid].append(tid)
    

    def results_to_post(self,date,qid):
        return self._results[date][qid]

    def compute_new_threshold(self,day_clarities,date):
        self._threshold[date] = {}
        for qid in day_clarities:
            self._threshold[date][qid] = day_clarities[qid]*self._coeff[0]
            self._threshold[date][qid] += self._scores[date][qid][0]*self._coeff[1]
            for i in range(len(self._coeff)-2):
                try:
                    self._threshold[date][qid] += self._coeff[i+2]*(self._scores[date][qid][i+1] - self._scores[date][qid][i]) 
                except IndexError:
                    print i,len(self._coeff),len(self._scores[date][qid])
        
        with open(self._threshold_file,"w") as f :
            f.write(json.dumps(self._threshold))            

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


def compute_day_clarities(show_clarity_file,date_index_dir,date_clarity_query_file):

    day_clarities = {}
    run_command = "%s %s %s" %(show_clarity_file,date_index_dir,date_clarity_query_file)
    #print "command being run:\n%s" %(run_command)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            day_clarities[qid] = float(parts[1])
            

        else:
            break 
    return day_clarities


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






def run_query(query_file_name,query_dir,*result_files):
    
    query_file = os.path.join(query_dir,query_file_name)

    run_results = {}

    p = subprocess.Popen(["IndriRunQuery", query_file],  stdout=subprocess.PIPE)
    output = p.communicate()[0]

    # write to result files
    for rf in result_files:
        with open(rf,"a") as of:
            of.write(output)



    count = 0
    sentences  =  output.split("\n")
    for s in sentences:
        if len(s)==0:
            continue
        parts = s.split()
        qid = parts[0]
        tid = parts[2]
        score = float(parts[4])
        if qid not in run_results:
            run_results[qid] = []
        run_results[qid].append( (tid,score) )

    return run_results

def merge_two_dicts(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z

def generate_output(query_dir,result_dir,date,communicator,logger,runs,previous_results):
    MB_static_query_name = os.path.join(query_dir,"MB_static_%s" %date) 
    RTS_static_query_name = os.path.join(query_dir,"RTS_static_%s" %date) 
    RTS_dynamic_query_name = os.path.join(query_dir,"RTS_dynamic_%s" %date) 

    static_result = os.path.join(result_dir,"static_%s" %date)
    dynamic_result = os.path.join(result_dir,"dynamic_%s" %date)

    if os.path.exists(static_result):
        os.system("rm %s" %static_result)

    if os.path.exists(dynamic_result):
        os.system("rm %s" %dynamic_result)

    print "run queries!"
    MB_static_results = run_query(MB_static_query_name,query_dir,static_result,dynamic_result)
    RTS_static_results = run_query(RTS_static_query_name,query_dir,static_result)
    RTS_dynamic_results = run_query(RTS_dynamic_query_name,query_dir,dynamic_result)

    print "get results for each run"

    print "process UDInfoSPP results"
    static_results = merge_two_dicts(MB_static_results,RTS_static_results)
    runs["UDInfoSPP"].process_new_results(static_results,date,
                            previous_results)
    print "process UDInfoSFP results"
    runs["UDInfoSFP"].process_new_results(static_results,date,
                            previous_results)
    print "process UDInfoDFP results"
    runs["UDInfoDFP"].process_new_results(merge_two_dicts(MB_static_results,RTS_dynamic_results),date,
                            previous_results)

    #print "process RTS queries"
    #runs["UDInfoSPP"].process_new_results(RTS_static_results,date,
    #                        previous_results)
    #runs["UDInfoSFP"].process_new_results(RTS_static_results,date,
    #                        previous_results)
    #runs["UDInfoDFP"].process_new_results(RTS_dynamic_results,date,
    #                        previous_results)

    print "post results"
    for run_name in runs:
        rejected = {}
        count = 0
        posted_results = {}
        for qid in static_results:
            posted_results[qid]  = []        
            for tid in runs[run_name].results_to_post(date,qid):
        
                return_url, status_code = communicator.post_tweet(run_name,qid,tid)
                if status_code == requests.codes.no_content:

                    count += 1
                    posted_results[qid].append(tid)
                    #stop posting tweets for a query if 10 tweets already
                    #posted
                    if len(posted_results[qid]) == 10:
                        break
                else:
                    error_code = status_code
                    if error_code not in rejected:
                        rejected[error_code] = 0
                    rejected[error_code] += 1

        print "post %d tweets for run %s" %(len(posted_results[qid]),run_name)
        runs[run_name].store_posted_results(posted_results,date)
        if rejected:
            for e_code in rejected:
                error_message = "%s:\nrejected %d tweets with error code: %s for run %s" %(now(),rejected[e_code],e_code,run_name)
                print error_message
                logger.warn(error_message+"\n")

    
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2016-rts/data/index")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/data/queries")
    parser.add_argument("--text_dir","-tr",default="/infolab/headnode2/lukuang/2016-rts/data/raw/first/text")
    parser.add_argument("--result_dir","-rr",default="/infolab/headnode2/lukuang/2016-rts/data/result")
    parser.add_argument("--para_dir","-pr",default="/infolab/headnode2/lukuang/2016-rts/data/para")
    parser.add_argument("--posted_result_dir","-prr",default="/infolab/headnode2/lukuang/2016-rts/data/posted_results")
    parser.add_argument("--clarity_query_dir","-cqr",default="/infolab/headnode2/lukuang/2016-rts/data/clarity_queries")
    parser.add_argument("--previous_result_file","-prf",default="/infolab/headnode2/lukuang/2016-rts/data/previous_results")
    parser.add_argument("--show_clarity_file","-scf",default="/infolab/headnode2/lukuang/2016-rts/code/2016/show_clarity")
    parser.add_argument("--coeff_dir","-cor",default="/infolab/headnode2/lukuang/2016-rts/data/threshold_coeff")
    parser.add_argument("--threshold_dir","-thr",default="/infolab/headnode2/lukuang/2016-rts/data/threshold")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2016-rts/data/communication")
    args=parser.parse_args()



    
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

    precision_coeff_file = os.path.join(args.coeff_dir,"p_coeff")
    f1_coeff_file = os.path.join(args.coeff_dir,"f1_coeff")

    runs = {
        "UDInfoSPP":Run("UDInfoSPP",precision_coeff_file,args.index_dir,args.threshold_dir,args.posted_result_dir ),
        "UDInfoSFP":Run("UDInfoSFP",f1_coeff_file,args.index_dir,args.threshold_dir,args.posted_result_dir),
        "UDInfoDFP":Run("UDInfoDFP",f1_coeff_file,args.index_dir,args.threshold_dir,args.posted_result_dir)
    }

    for name in runs:
        communicator.register_run(name)

    print "Setup previous results"
    previous_results = PreviousResults(args.previous_result_file) 

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

        print "generate output"
        generate_output(args.query_dir,args.result_dir,date,
                        communicator,logger,runs,previous_results)
        end = now()

        print "store previous results:"
        previous_results.store_previous()

        print "compute threshold for next day"

        date_index_dir = os.path.join(args.index_dir,date)
        
        
        static_clarity_query_file = os.path.join(args.clarity_query_dir,"static_%s" %date)
        static_day_clarities = compute_day_clarities(args.show_clarity_file,date_index_dir,static_clarity_query_file)
        
        dynamic_clarity_query_file = os.path.join(args.clarity_query_dir,"dynamic_%s" %date)
        dynamic_day_clarities = compute_day_clarities(args.show_clarity_file,date_index_dir,dynamic_clarity_query_file)


        runs["UDInfoSPP"].compute_new_threshold(static_day_clarities,date)
        runs["UDInfoSFP"].compute_new_threshold(static_day_clarities,date)
        runs["UDInfoDFP"].compute_new_threshold(dynamic_day_clarities,date)

        print "process of date %s ended" %date
        print "start at:%s\nand end at%s" %(start,end)
        print "-"*20

        total_secs = need_wait()    
        time.sleep(total_secs)
        # except Exception as ex:
        #     now_time = now()
        #     logger.warn("%s: %s\n" %(now_time,str(ex)) )

        

if __name__=="__main__":
    main()

