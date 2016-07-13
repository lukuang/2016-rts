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

def get_mb_queries(original_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    in_title = False
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\w+)",line)
            
            if mn is not None:
                qid = mn.group(1)
                title_queries[qid] = ""
                desc_queries[qid] = ""
            else:
                mt = re.search("<title>",line)
                if mt is not None:
                    in_title = True
                    continue
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
            elif in_title:
                title_queries[qid] = line+"\n"
                in_title = False
    return title_queries,desc_queries

def get_original_queries(original_query_file):
    title_queries,desc_queries = get_mb_queries(original_query_file)
    queries = {}
    for qid in title_queries:
        
        q_text = title_queries[qid]
        queries[qid] = Query(qid,q_text)

    return queries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("top_index_dir")
    parser.add_argument("top_query_para_dir")
    parser.add_argument("index_method",choices=["individual","incremental"])
    parser.add_argument("--retrieval_method","-rm",default="method:f2exp")
    parser.add_argument("--result_count","-rc",type=int,default=10)
    parser.add_argument("--fbDocs","-fd",type=int,default=10)
    parser.add_argument("--fbTerms","-ft",type=int,default=10)
    parser.add_argument("--fbOrigWeight","-fw",type=float,default=0.5)
    parser.add_argument("--expansion_method","-em",type=int,choices=[0,1,2,3],
            default=0,
            help="""methodes for expansion. Options:
                    original,
                    snippet,
                    wiki,
                    pseudo 
                """)
    parser.add_argument("--tune","-t",action="store_true")
    args=parser.parse_args()

    METHODS = [
        "original",
        "snippet",
        "wiki",
        "pseudo"
    ]

    dates = range(20,30)
    year = 2015
    month = 7


    expansion_method = METHODS[args.expansion_method]
    
    original_queries =  get_original_queries(args.original_query_file)

    print args.top_query_para_dir,args.index_method,args.expansion_method
    query_root_dir =  os.path.join(
                            args.top_query_para_dir,
                            args.index_method,expansion_method)
    if not os.path.exists(query_root_dir):    
        os.makedirs(query_root_dir)


    for date in dates:
        date = str(date)
        query_file = os.path.join(query_root_dir,date)

        index_dir = os.path.join(args.top_index_dir,args.index_method,date)

        date_when_str = "%s/%s/%d" %(str.zfill(str(month),2),
                                        str.zfill(date,2),
                                        year)
        date_when_str = "%s" %(date_when_str)

        if expansion_method == "original" or "pseudo":
            if expansion_method == "original":
                if args.tune:
                    for s in range(4):
                        s = (s+1)*0.1
                        tune_retrieval_method = args.retrieval_method +",s:%f" %(s)
                        tune_run_id = "original_%f" %(s)
                        tune_query_file = '%s_%f' %(query_file,s)
                        query_builder = IndriQueryFactory(count=args.result_count,
                            rule=tune_retrieval_method,use_stopper=False,
                            date_when="dateequals",psr=False)

                        query_builder.gene_query_with_date_filter(tune_query_file,
                            original_queries,index_dir,date_when_str,run_id=tune_run_id )
            else:
                if args.tune:
                    for s in range(3):
                        s = (s+1)*0.3
                        tune_retrieval_method = args.retrieval_method +",s:%f" %(s)
                        
                        for tune_fbDocs in [5,10,15]:
                            for tune_fbTerms in [5,10,15]:
                                for tune_fbOrigWeight in [0.3,0.6,0.9]:

                                    tune_run_id = "pseudo_%f_%d_%d_%f" %(s,tune_fbDocs,
                                                                         tune_fbTerms,
                                                                         tune_fbOrigWeight)

                                    tune_query_file = '%s_%f_%d_%d_%f' %(query_file,s,
                                                                         tune_fbDocs,
                                                                         tune_fbTerms,
                                                                         tune_fbOrigWeight)

                                    query_builder = IndriQueryFactory(count=args.result_count,
                                        rule=tune_retrieval_method,use_stopper=False,
                                    
                                        date_when="dateequals",psr=True)

                                    query_builder.gene_query_with_date_filter(tune_query_file,
                                        original_queries,index_dir,date_when_str,run_id=tune_run_id,
                                        fbDocs=tune_fbDocs,fbTerms=tune_fbTerms,
                                        fbOrigWeight=tune_fbOrigWeight)
        else:
            raise RuntimeError("method not implemented yet!")




if __name__=="__main__":
    main()

