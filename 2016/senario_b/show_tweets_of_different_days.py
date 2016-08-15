"""
show tweets of different days for a query
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def get_text(index_dir,tid):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tid)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def show_text(index,tids):
    for tid in tids:
        print "%s: %s" %(tid,get_text(index,tid))


def read_tids(result_file,required_qid):
    tids = []
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            qid = parts[0]
            if qid == required_qid:
                tids.append(parts[2])
    return tids

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_file_1")
    parser.add_argument("result_file_2")
    parser.add_argument("required_qid")
    parser.add_argument("--index_top_dir","-itr",default="/infolab/headnode2/lukuang/2016-rts/data/index")
    args=parser.parse_args()

    tids1 = read_tids(args.result_file_1,args.required_qid)
    tids2 = read_tids(args.result_file_2,args.required_qid)

    m1 = re.search("_(\d+)$", args.result_file_1)
    date1 = m1.group(1)

    m2 = re.search("_(\d+)$", args.result_file_2)
    date2 = m2.group(1)

    index_1 = os.path.join(args.index_top_dir,date1)
    index_2 = os.path.join(args.index_top_dir,date2)
    print index_1
    print index_2
    print "for query %s" %args.required_qid
    print "for file 1:"
    show_text(index_1,tids1)
    print "for file 2:"
    show_text(index_2,tids2)

if __name__=="__main__":
    main()

