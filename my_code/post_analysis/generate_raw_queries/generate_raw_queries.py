"""
generate raw queries for 2016
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.indri import IndriQueryFactory


def load_2016_queries(topic_file):
    queries = {}
    #communicator.poll_topics()
    topics = json.load(open(topic_file))
    for a_topic in topics:
        qid = a_topic["topid"]
        q_string = a_topic['title']
        q_string = re.sub("\&"," ",q_string)
        
        queries[qid] = q_string
    return queries

def generate_raw_queries(queries,dest_dir,index_dir):

    for i in range(1,12):
        date = str(i)
        date_query_builder = IndriQueryFactory(count=100,
                                    rule="method:f2exp,s:0.1")
        date_index = os.path.join(index_dir,date)
        dest_file = os.path.join(dest_dir,date)
        date_query_builder.gene_normal_query(dest_file,
                            queries,date_index)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic_file","-tf",default='/infolab/headnode2/lukuang/2016-rts/data/communication/topics')
    parser.add_argument("dest_dir")
    parser.add_argument("--index_dir","-id",default='/infolab/headnode2/lukuang/2016-rts/data/full_index/')
    args=parser.parse_args()
    queries = load_2016_queries(args.topic_file)
    generate_raw_queries(queries,args.dest_dir,args.index_dir)



if __name__=="__main__":
    main()

