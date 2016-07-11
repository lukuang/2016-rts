"""
generate queries for 2015
"""

import os
import json
import sys
import re
import argparse
import codecs
sys.path.append("../../")

from myUtility.indri import IndriQueryFactory
from myUtility.corpus import Query,ExpandedQuery

def get_original_queries(original_query_file):
    data = json.load(original_query_file)
    queries = {}
    for q in data:
        qid = q["topid"]
        q_text = q["title"]
        queries[qid] = Query(qid,q_text)

    return queries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("top_index_dir")
    parser.add_argument("top_query_para_dir")
    parser.add_argument("index_method",choices=["individual","incremental"])
    parser.add_argument("--retrieval_method","-rm",default="f2exp")
    parser.add_argument("--result_count","-rc",type=int,default=10)
    parser.add_argument("--fbDocs","-fd",type=int,default=10)
    parser.add_argument("--fbTerms","-ft",type=int,default=10)
    parser.add_argument("--fbOriWeight","-fw",type=float,default=0.5)
    parser.add_argument("--expansion_method","-em",type=int,choices=[0,1,2,3],
            default=0,
            help="""methodes for expansion. Options:
                    original,
                    snippet,
                    wiki,
                    pseudo 
                """)
    args=parser.parse_args()

    METHODS = [
        "original",
        "snippet",
        "wiki",
        "pseudo"
    ]

    dates = range(20,30)

    expansion_method = METHODS[args.expansion_method]
    
    index_dir = os.path.join(args.top_index_dir,args.index_method)
    original_queries =  get_original_queries(args.original_query_file)


    query_root_dir =  os.path.join(
                            args.top_query_para_dir,
                            args.index_method,args.expansion_method)
    if not os.path.exists(query_root_dir):    
        os.makedirs(query_root_dir)


    for date in dates:
        date = str(date)
        query_file = os.path.join(query_root_dir,date)




        if expansion_method == "original" or "pseudo":
            queries = build_raw_query(queries)
            if expansion_method == "original":

                query_builder = IndriQueryFactory(count=args.result_count,
                    rule=args.retrieval_method,use_stopper=False,
                    date_when="datebetween",psr=False)

                query_builder.gene_query_with_date_filter(query_file,
                    original_queries,index_dir,date)
            else:
                query_builder = IndriQueryFactory(count=args.result_count,
                    rule=args.retrieval_method,use_stopper=False,
                    date_when="datebetween",psr=True)

                query_builder.gene_query_with_date_filter(query_file,
                    original_queries,index_dir,date,args.fdDocs,
                    args.fbTerms,fbOriWeight)
        else:
            raise RuntimeError("method not implemented yet!")




if __name__=="__main__":
    main()

