"""
get assessment each day on 9:00 pm, which is 00:00 UTC
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
from datetime import timedelta
import subprocess
import datetime

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.broker_communication import BrokerCommunicator

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) 

def need_wait():
    # compute how many secs need to wait before next run for next
    # da. Run it everyday 00:00
    time_struct =  time.gmtime() 
    if time_struct.tm_hour == 0:
        wait_hours = 23
    else:
        wait_hours = 23 - time_struct.tm_hour
    
    wait_minutes = 60 - time_struct.tm_min
    
    total_secs = timedelta(hours=wait_hours,minutes=wait_minutes).total_seconds()
    
    print "now is %s" %(now())
    print "need to wait %d hours %d minutes, which is %f seconds" %(wait_hours,wait_minutes,total_secs)
    return int(total_secs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assessment_dir","-cr",
        default="/infolab/headnode2/lukuang/2017-rts/data/communication/assessments")
    parser.add_argument("--run_name_file","-rf",default="/infolab/headnode2/lukuang/2017-rts/data/communication/runs")
    parser.add_argument("--basic_file","-bf",default="/infolab/headnode2/lukuang/2017-rts/data/communication/basic")
    parser.add_argument("--topic_file","-tf",default="/infolab/headnode2/lukuang/2017-rts/data/communication/topics")
    args=parser.parse_args()

    basic_info = json.load(open(args.basic_file)) 
    if basic_info is None:
        raise RuntimeError("Need to have a valid basic file %s" %basic_file)
    hostname =  basic_info["hostname"]


    topics = json.load(open(args.topic_file)) 
    qids = []
    for t in topics:
        qids.append( t["topid"] )

    run_info = json.load(open(args.run_name_file))
    clientid = run_info.values()[0]

    print "wait till 00:00 today first!"
    total_secs = need_wait()    
    time.sleep(total_secs)


    while True:
        start = now()
        print "start processing at %s" %start
        date = str(time.gmtime().tm_mday)
        #date='23'
        print "date is %s" %date

        day_assessments = []
        dest_file = os.path.join(args.assessment_dir,date)
        for qid in qids:
            assessment_request_url = "%s/assessments/%s/%s" %(hostname,qid,clientid)
            run_command = "curl -X POST -H 'Content-Type: application/json' %s " %(assessment_request_url)

            p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
            content = p.communicate()[0]
            q_assessment = json.loads(content)
            day_assessments.append(q_assessment)

        with open(dest_file,"w") as of:
            of.write(json.dumps(day_assessments,indent=4))

        end = now()

        print "getting assessments of date %s ended" %date
        print "start at:%s\nand end at%s" %(start,end)
        print "-"*20

        total_secs = need_wait()    
        time.sleep(total_secs)



if __name__=="__main__":
    main()

