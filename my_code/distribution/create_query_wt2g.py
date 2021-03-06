"""
create trec query file for w2tg queries
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.misc import gene_indri_query_file
from misc import get_wt2g_queries



def write_query_to_file(queries,query_file,index,count,use_stopper):
    rules = {
        "f2exp":"method:f2exp,s:0.5",
        "pivoted":"method:pivoted,s:0.2",
        "BM25":"method:okapi,k1:1.2,b:0.75",
        "JM":"method:jm-smoothing,lambda:0.2"

        }

    for method in rules:
        file_path = query_file + "_" + method
        run_id = method
        gene_indri_query_file(file_path,queries,index,count=count,
                              run_id=run_id,rule=rules[method],
                              use_stopper= use_stopper)


def main():
    base_dir = os.path.split(os.path.abspath(__file__))[0]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title_query_file")
    parser.add_argument("desc_query_file")
    parser.add_argument(
        "--original_file","-or", default =\
        os.path.join(base_dir,"additional_data/topics.401-450"))
    
    parser.add_argument("index")
    parser.add_argument(
        "--use_stopper","-us", action='store_true')
    
    parser.add_argument("--count","-c",type=int,default = 1000)

    args=parser.parse_args()

    title_queries,desc_queries = get_wt2g_queries(args.original_file)
    write_query_to_file(title_queries,args.title_query_file,args.index,args.count,args.use_stopper)
    write_query_to_file(desc_queries,args.desc_query_file,args.index,args.count,args.use_stopper)
    #print title_queries
    #print desc_queries

if __name__=="__main__":
    main()

