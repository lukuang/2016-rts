"""
generate a new qrel from old qrel by making half of the queries silent
remove relevant documents of these silent queries from the index
"""

import os
import json
import sys
import re
import argparse
import codecs
import random

def read_qrel_file(qrel_file):
    qrel = {}
    with open(qrel_file) as f:
        for line in f:
            parts = line.split()
            qid = parts[0]
            docid = parts[2]
            judgment = parts[3]
            if qid not in qrel:
                qrel[qid] = {}
            qrel[qid][docid] = judgment

    return qrel


def choose_silent_queries(qrel):
    selected_silent_qid = random.sample(qrel.keys(), len(qrel)/2)
    return selected_silent_qid

def gene_new_qrel(qrel,selected_silent_qid,dest_qrel_file,dest_silent_query_info):
    silent_query_info = {}
    with open(dest_qrel_file,"w") as f:
        for qid in qrel: 
            for docid in qrel[qid]:   
                print_line = False
                judgment = int(qrel[qid][docid]) 
                if qid in selected_silent_qid:

                    if (judgment <= 0):
                        print_line = True
                    else:
                        if qid not in silent_query_info:
                            silent_query_info[qid] = []
                        silent_query_info[qid].append(docid)
                else:
                    print_line = True

                if print_line:
                    f.write("%s_title Q0 %s %d\n" %(qid, docid, judgment))
                    f.write("%s_desc Q0 %s %d\n" %(qid, docid, judgment))

    num_of_removed = sum([ len(silent_query_info[qid]) for qid in silent_query_info])
    print "There are %d documents removed" %(num_of_removed)

    with open(dest_silent_query_info,"w") as f:
        f.write(json.dumps(silent_query_info,indent=2))

 


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/disk4-5/eval/qrel")
    parser.add_argument("dest_qrel_file")
    parser.add_argument("dest_silent_query_info")
    parser.add_argument("--index_dir","-id",default="/infolab/node4/lukuang/2015-RTS/disk4-5/index/10")
    args=parser.parse_args()

    qrel =  read_qrel_file(args.qrel_file)
    print "There are %d queries" %(len(qrel))
    selected_silent_qid = choose_silent_queries(qrel)

    gene_new_qrel(qrel,selected_silent_qid,args.dest_qrel_file,args.dest_silent_query_info)

if __name__=="__main__":
    main()

