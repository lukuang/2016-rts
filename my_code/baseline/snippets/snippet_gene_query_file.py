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

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/")

from process_query import read_query_file


def get_judged_qid(qrel_file):
    judged_qids = []
    with open(qrel_file) as f:
        for line in f:
            parts= line.rstrip().split()
            qid = parts[0]
            if qid not in judged_qids:
                judged_qids.append(qid)
    return judged_qids

    

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("query_type",choices=["2015_mb","json_mb","wt2g","2011"])
    parser.add_argument("query_field",choices=["title","desc","combine"])
    parser.add_argument("index_path")
    parser.add_argument("query_para_file")
    parser.add_argument("--qrel_file","-qf")
    parser.add_argument("--result_count","-rc",type=int,default=10000)
    parser.add_argument("--retrieval_method","-rm",default="method:f2exp")
    args=parser.parse_args()


    queries = read_query_file(args.original_query_file,args.query_type,args.query_field)

    if args.qrel_file:
        print "remove unjudged queries"
        print "# queries before %d" %(len(queries))
        judged_qids = get_judged_qid(args.qrel_file)
        for qid in queries.keys():
            if qid not in judged_qids:
                queries.pop(qid,None)
        print "# queries after %d" %(len(queries))


    query_builder = IndriQueryFactory(count=args.result_count,
                            rule=args.retrieval_method)
    
    query_builder.gene_normal_query(args.query_para_file,queries,args.index_path)

if __name__=="__main__":
    main()

