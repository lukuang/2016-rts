"""
generate query file for snippets
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.indri import IndriQueryFactory

sys.path.append("../../")

from process_query import read_query_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("query_type",choices=["2015_mb","json_mb","wt2g"])
    parser.add_argument("query_field",choices=["title","desc","combine"])
    parser.add_argument("index_path")
    parser.add_argument("query_para_file")
    parser.add_argument("--result_count","-rc",type=int,default=10000)
    parser.add_argument("--retrieval_method","-rm",default="method:f2exp")
    args=parser.parse_args()


    queries = read_query_file(args.original_query_file,args.query_type,args.query_field)

    query_builder = IndriQueryFactory(count=args.result_count,
                            rule=args.retrieval_method)

    query_builder.gene_normal_query(args.query_para_file,queries,args.index_path)

if __name__=="__main__":
    main()

