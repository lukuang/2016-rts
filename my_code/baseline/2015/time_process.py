"""
measure time of generating a run
"""

import os
import json
import sys
import re
import argparse
import codecs
import shutil
from run_query import run_query
from datetime import datetime, timedelta


def show_time_now():
    now = datetime.now()
    print now.isoformat(" ")
    return now


#compute time different between start and end in minutes
def compute_time_diff(start,end):
    return (end-start).total_seconds()/60.0

def compute_all_time_diff(time_stamps):
    
    time_diff = []
    for i in range(len(time_stamps)):
        if i != 0:
            time_diff.append(compute_time_diff(time_stamps[i-1],time_stamps[i]))

    max_time_diff = max(time_diff)
    avergae_time_diff = sum(time_diff)*1.0/len(time_stamps)

    return max_time_diff,avergae_time_diff

def do_simulation(index_para_dir,index_method,query_para_dir,
                  expansion_method,runquery_script,suffix,
                  temp_dir,debug,time_stamps):

    temp_index_para_file = os.path.join(temp_dir,"index_para")
    temp_index_dir = os.path.join(temp_dir,"index")
    temp_result_file = os.path.join(temp_dir,"result")
    for date in range(20,30):

        index_para_file = os.path.join(index_para_dir,index_method,"%d" %date)

        with open(temp_index_para_file,"w") as of:
            with open(index_para_file,"r") as f:
                for line in f:
                    if re.search("<index>.+</index>",line):
                        line = "<index>%s</index>\n" %temp_index_dir
                    of.write(line)



        if debug:
            print "IndriBuildIndex %s" %temp_index_para_file
        else:    
            os.system("IndriBuildIndex %s" %temp_index_para_file)
        
        query_file = os.path.join(query_para_dir,index_method,expansion_method,
                                  "%d%s" %(date,suffix)) 
        run_query(runquery_script,query_file,temp_result_file,debug)

        now = show_time_now()
        time_stamps.append(now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index_para_dir")
    parser.add_argument("query_para_dir")
    parser.add_argument("index_method",choices=["individual","incremental"])
    parser.add_argument(
            "expansion_method",type=int,choices=[0,1,2,3],
            help="""methodes for expansion. Options:
                    original,
                    snippet,
                    wiki,
                    pseudo 
                """)
    parser.add_argument("suffix")
    parser.add_argument("temp_dir")
    parser.add_argument("--runquery_script","-rq",default="IndriRunQuery")
    parser.add_argument("--debug","-de",action="store_true")
    
    args=parser.parse_args()

    METHODS = [
        "original",
        "snippet",
        "wiki",
        "pseudo"
    ]
    expansion_method = METHODS[args.expansion_method]

    time_stamps= []
    time_diff = []

    print "start"
    start = show_time_now()
    time_stamps.append(start)

    
    do_simulation(args.index_para_dir,args.index_method,
                  args.query_para_dir,expansion_method,
                  args.runquery_script,args.suffix,
                  args.temp_dir,args.debug,time_stamps)


    print "end"

    max_time_diff, avergae_time_diff  = \
            compute_all_time_diff(time_stamps)
    print "average time used: %f minutes" \
                %(avergae_time_diff)
    print "maximun time used: %f minutes" \
                %(max_time_diff)    
    print "total time used: %f minnutes for %d queries" \
        %(compute_time_diff(start,time_stamps[-1]), len(time_stamps)-1 ) 



if __name__=="__main__":
    main()

