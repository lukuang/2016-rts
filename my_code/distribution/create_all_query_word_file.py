"""
create all query word files from trec query file
"""

import os
import json
import sys
import re
import argparse
import codecs
from misc import get_wt2g_queries


def output(queries,dest_file):
    words  = set()
    for qid in queries:
        for w in re.findall("\w+",queries[qid]):
            words.add(w.lower())

    with codecs.open(dest_file,"w"."utf-8") as f:
        for w in words:
            f.write(w+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("dest_file")
    parser.add_argument("--query_type","-qt",type=int,choices=[0,1],default=0)

    args=parser.parse_args()
    queries = {}
    
    ## Query Type:
    ## 0: wt2g query file

    
    if args.query_type == 0:
        title_queries,desc_queries = get_wt2g_queries(original_query_file)
        for qid in title_queries:
            queries[qid] = title_queries[qid] +" " +desc_queries[qid]
    else:
        raise KeyError("Unsupported query type %d" %(args.query_type))

    output(queries,args.dest_file)

if __name__=="__main__":
    main()

