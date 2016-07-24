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
    print file_date,date
    if file_date == date:
        return True
    return False

def get_file_list(text_dir,date):
    all_files = os.walk(text_dir).next()[2]
    all_files.sort() # solely for debuging purpose
    file_list = []
    for hour_text_file in all_files:
        print hour_text_file
        if check_file_time(hour_text_file,date):
            
            file_list.append(os.path.join(text_dir,hour_text_file))
    
    return file_list
    


def build_index(index_dir,para_dir,text_dir,date):
    # file_list = get_file_list(text_dir,date)
    # if len(file_list)!= 23:
    #     print "wait 10 miniutes since the text files are not all ready(probably missing 22)"
    #     time.sleep(600)
    file_list = get_file_list(text_dir,date)
    if len(file_list)!= 23:
        print "Warning: there are still %d files!" %(len(file_list))
        print file_list
    index_para_file = os.path.join(para_dir,date)
    index_path = os.path.join(index_dir,date)

    gene_indri_index_para_file(file_list,index_para_file,
                    index_path)

    os.system("IndriBuildIndex %s" %index_para_file)


def find_query_files(query_dir,date):
    all_query_files = os.walk(query_dir).next()[2]
    query_list = []
    for f in all_query_files:
        m = re.search("%s$" %date,f)
        if m:
            query_list.append(f)
    return query_list


def run_query(query_dir,result_dir,date,communicator):
    query_list = find_query_files(query_dir,date)

    for f in query_list:
        result_file = os.path.join(result_dir,f)
        query_file = os.path.join(query_dir,f)
        p = subprocess.Popen(["IndriRunQuery", query_file],  stdout=subprocess.PIPE)
        output = p.communicate()[0]

        # write to result files
        with open(result_file,"w") as of:
            of.write(output)

        #post to broker:
        run_name = ""
        rejected = {}
        count = 0
        sentences  =  output.split("\n")
        for s in sentences:
            if len(s)==0:
                continue
            parts = s.split()
            topic_id = parts[0]
            tweet_id = parts[2]
            run_name = parts[5]
            return_url, status_code = communicator.post_tweet(run_name,topic_id,tweet_id)
            if status_code == requests.codes.no_content:

                count += 1
            else:
                error_code = status_code
                if error_code not in rejected:
                    rejected[error_code] = 0
                rejected[error_code] += 1

        print "post %d tweets for run %s" %(count,run_name)
        if rejected:
            for e_code in rejected:
                print "rejected %d with error code: %s" %(e_code,rejected[e_code])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2016-rts/data/index")
    parser.add_argument("--query_dir","-qr",default="/infolab/headnode2/lukuang/2016-rts/data/queries")
    parser.add_argument("--text_dir","-tr",default="/infolab/headnode2/lukuang/2016-rts/data/raw/first/text")
    parser.add_argument("--result_dir","-rr",default="/infolab/headnode2/lukuang/2016-rts/data/result")
    parser.add_argument("--para_dir","-pr",default="/infolab/headnode2/lukuang/2016-rts/data/para")
    parser.add_argument(
        "--communication_dir","-cr",
        default="/infolab/headnode2/lukuang/2016-rts/data/communication")
    args=parser.parse_args()


    basic_file = os.path.join(args.communication_dir,"basic")
    run_name_file = os.path.join(args.communication_dir,"runs")
    topic_file = os.path.join(args.communication_dir,"topics")

    runs = [
        "UDInfoORI",
        "UDInfoSNI"
    ]

    communicator = BrokerCommunicator(basic_file,
                        run_name_file,topic_file)
    
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
    print "register runs:"
    for name in runs:
        communicator.register_run(name)


    print "wait till 23:00 today first!"
    total_secs = need_wait()    
    time.sleep(total_secs)

    while True:
        try:
            date = str(time.gmtime().tm_mday)
            #date='23'
            print "date is %s" %date
            print "build index"
            build_index(args.index_dir,args.para_dir,args.text_dir,date)
            print "run queries"
            run_query(args.query_dir,args.result_dir,date,communicator)
            total_secs = need_wait()    
            time.sleep(total_secs)
        except Exception as ex:
            now_time = now()
            logger.warn("%s: %s\n" %(now_time,str(ex)) )

        

if __name__=="__main__":
    main()

