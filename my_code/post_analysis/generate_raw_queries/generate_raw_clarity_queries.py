"""
generate raw clarity queries for 2016
"""

import os
import json
import sys
import re
import argparse
import codecs

def load_2016_queries(topic_file):
    queries = {}
    #communicator.poll_topics()
    topics = json.load(open(topic_file))
    for a_topic in topics:
        qid = a_topic["topid"]
        q_string = a_topic['title']
        q_string = re.sub("[^\w]"," ",q_string)
        
        queries[qid] = q_string
    return queries

def generate_raw_queries(queries,dest_dir):

    for i in range(1,12):
        date = str(i)
        dest_file = os.path.join(dest_dir,date)
        with open(dest_file,"w") as f:
            for qid in queries:
                f.write("%s:%s\n" %(qid,queries[qid]))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic_file","-tf",default='/infolab/headnode2/lukuang/2016-rts/data/communication/topics')
    parser.add_argument("dest_dir")
    args=parser.parse_args()
    queries = load_2016_queries(args.topic_file)
    generate_raw_queries(queries,args.dest_dir)



if __name__=="__main__":
    main()
