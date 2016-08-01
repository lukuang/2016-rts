"""
evaluate the time used to compute the redundancy
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
import random

def load_result(result_file):
    results = []
    result_data = json.load(open(result_file))
    for rid in result_data:
        qids =  result_data[rid].keys()
        for qid in result_data[rid]:
            results += result_data[rid][qid]
    return results,qids

def compute_term_diff(tweet_text,t_text):
        words1 = re.findall("\w+",tweet_text)
        words2 = re.findall("\w+",t_text)
        common = list(set(words1).intersection(words2))
        diff = len(common)*1.0/max(len(words1),len(words2))
        return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_file")
    args=parser.parse_args()

    day_tweet_size = 10
    previous_result_size = 90

    results,qids = load_result(args.result_file)
    print  "%d qids" %(len(qids))
    diff = []

    for i in range(10):
        test_day_result = random.sample(results,day_tweet_size)
        
        test_previous_results = {}
        for qid in qids:

            test_previous_results[qid] = random.sample(results,previous_result_size) 
        
        test_qid = random.sample(qids,1)[0]
        start = time.time()
        time_of_computation = 0
        for tweet in test_day_result:
            for a_previous_tweet in test_previous_results[test_qid]:
                compute_term_diff(a_previous_tweet,tweet)
                time_of_computation += 1

        print "Computed %d times" %time_of_computation
        end = time.time()
        diff_now = end  - start
        diff.append(diff_now)
        print "The time used this iteration is %f" %diff_now

    print "-"*20
    average = sum(diff)/(1.0*len(diff))
    print "The average time used is: %f" %(average)
    estimate = average * 200
    print "The estimated time used for last date is: %f" %estimate



if __name__=="__main__":
    main()

