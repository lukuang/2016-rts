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

def get_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\d+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>(.+)",line)
                if mt is not None:
                    title_queries[qid] = mt.group(1)
                else:
                    md = re.search("<desc> Description:",line)
                    if md is not None:
                        in_desc = True
                        continue
                    else:
                        ma = re.search("<narr> Narrative:",line)
                        if ma is not None:
                            in_desc = False
            
            if in_desc:
                desc_queries[qid] += line+"\n"
    return title_queries,desc_queries


def write_query_to_file(queries,query_file,index,count):
    rules = {
        "f2exp":"method:f2exp,s:0.5",
        "pivoted":"method:pivoted,s:0.2",
        "BM25":"method:okapi,k1:1.2,b:0.75",
        "JM":"method:jm,lambda:0.2"

        }

    for method in rules:
        file_path = query_file + "_" + method
        run_id = method
        gene_indri_query_file(file_path,queries,index,count=count,
                              run_id=run_id,rule=rules[method],
                              use_stopper=True)


def main():
    base_dir = os.path.split(os.path.abspath(__file__))[0]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title_query_file")
    parser.add_argument("desc_query_file")
    parser.add_argument(
        "--original_file","-or", default =\
        os.path.join(base_dir,"additional_data/topics.401-450"))
    
    parser.add_argument("index")
    parser.add_argument("--count","-c",type=int,default = 1000)

    args=parser.parse_args()

    title_queries,desc_queries = get_queries(args.original_file)
    write_query_to_file(title_queries,args.title_query_file,args.index,args.count)
    write_query_to_file(desc_queries,args.desc_query_file,args.index,args.count)
    #print title_queries
    #print desc_queries

if __name__=="__main__":
    main()

