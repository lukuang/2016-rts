"""
read query files of different type
"""

import os
import json
import sys
import re
import argparse
import codecs

def get_mb_queries(original_query_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    in_title = False
    with open(original_query_file) as f:
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

def get_mb_queries_2011(original_file):
    title_queries = {}
    qid = ""
    with open(original_file) as f:
        for line in f:
            line = line.rstrip()
            mn = re.search("<num> Number: (\w+)",line)
            
            if mn :
                qid = mn.group(1)
                title_queries[qid] = ""
            else:
                mq = re.search("<title>(.+?)</title>",line)
                if mq:
                    title_queries[qid] = mq.group(1)
    return title_queries,{}


def get_wt2g_queries(original_query_file):
    title_queries = {}
    desc_queries = {}
    qid = ""
    in_desc = False
    with open(original_query_file) as f:
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


def get_mb_json_queries(original_query_file):
    data = json.load(open(original_query_file))
    title_queries = {}
    desc_queries = {}
    for q in data:
        qid = q["topid"]
        title_queries[qid] = q["title"]
        desc_queries[qid] = q["description"]

    return title_queries, desc_queries

def read_query_file(original_query_file,query_type,query_field):
    if query_type == "2015_mb":
        title_queries,desc_queries = get_mb_queries(original_query_file)
    elif query_type == "json_mb":
        title_queries,desc_queries = get_mb_json_queries(original_query_file)
    elif query_type == "2011":
        title_queries,desc_queries = get_mb_queries_2011(original_query_file)
    else:
        title_queries,desc_queries = get_wt2g_queries(original_query_file)

    if query_field == "title":
        return title_queries
    elif query_field == "desc":
        return desc_queries
    else:
        queries = {}
        for qid in title_queries:
            queries[qid] = desc_queries[qid] + title_queries[qid]
        return queries    


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("query_type",choices=["2015_mb","json_mb","wt2g"])
    parser.add_argument("query_field",choices=["title","desc","combine"])
    args=parser.parse_args()
    read_query_file(args.original_query_file,args,query_type,args.query_field)

if __name__=="__main__":
    main()

