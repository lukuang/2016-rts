"""
estimate the time used to get tweet text from index
"""

import os
import json
import sys
import re
import argparse
import codecs
import random
import subprocess
import time


def read_tids(result_file):
    tids = []
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            tids.append(parts[2])
    return tids

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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date_index_dir")
    parser.add_argument("result_file")

    args = parser.parse_args()

    tids = read_tids(args.result_file)

    diff = []
    for i in range(10):
        test_tids = random.sample(tids,10)
        start = time.time()
        time_of_computation = 0
        for tid in test_tids:
            new_text = get_text(args.date_index_dir,tid)
            time_of_computation +=1
            if new_text is None:
                print "cannot find text for tid %s" %tid
        print "Computed %d times" %time_of_computation
        end = time.time()
        diff_now = end  - start
        diff.append(diff_now)
        print "The time used this iteration is %f" %diff_now

    print "-"*20
    average = sum(diff)/(1.0*len(diff))
    print "The average time used is: %f" %(average)
    estimate = average * 203
    print "The estimated time used for last date is: %f" %estimate



if __name__=="__main__":
    main()

