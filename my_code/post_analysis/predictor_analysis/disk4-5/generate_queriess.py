"""
generate indri query as well as clarity queries
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.indri import IndriQueryFactory


def get_queries(original_query_file):
    queries = {}
    qid= ""
    desc = ""
    in_desc = False
    with open(original_query_file) as f:
        for line in f:
            line = line.rstrip()
            if in_desc:
                narr_finder = re.search("<narr>",line)
                if narr_finder:
                    in_desc = False
                    desc_qid = "%s_desc" %(qid)
                    queries[desc_qid] = desc
                    desc = ""
                else:
                    all_words = re.findall("\w+",line.lower())
                    desc +=  " ".join(all_words) + " "

            else:
                qid_finder = re.search("<num> Number:\s+(\d+)",line)
                
                if qid_finder:
                    qid = qid_finder.group(1)
                else:
                    title_finder = re.search("<title>(.+)$",line)
                    if title_finder:
                        all_words = re.findall("\w+",title_finder.group(1).lower())
                        title_qid = "%s_title" %(qid)
                        queries[title_qid] = " ".join(all_words)

                    desc_finder = re.search("<desc>",line)
                    if desc_finder:
                        in_desc = True

    return queries



def create_clarity_queries(clarity_query_file,queries):
    with open(clarity_query_file,'w') as f:
        for qid in queries:
            title = queries[qid]
            f.write("%s:%s\n" %(qid,title))



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original_query_file","-oqf",default="/infolab/node4/lukuang/2015-RTS/disk4-5/eval/301-450.601-700.qry")
    parser.add_argument("--index","-i",default="/infolab/node4/lukuang/2015-RTS/disk4-5/index/10")
    parser.add_argument("dest_file")
    parser.add_argument("clarity_query_file")
    args=parser.parse_args()


    queries = get_queries(args.original_query_file)
    query_generator = IndriQueryFactory(100)

    query_generator.gene_normal_query(args.dest_file,queries,args.index,run_id="disk45")

    create_clarity_queries(args.clarity_query_file,queries)



if __name__=="__main__":
    main()

