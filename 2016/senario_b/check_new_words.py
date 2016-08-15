"""
check new words for dynamic queries
"""

import os
import json
import sys
import re
import argparse
import codecs

def get_query_words(clariy_query_file):
    words = {}
    with open(clariy_query_file) as f:
        for line in f:
            m = re.search("(.+?):(.+?)$",line)
            if m:
                qid = m.group(1)
                q_string = m.group(2)
                q_words = set(re.findall("\w+",q_string))
                words[qid] = q_words
    return words

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_clarity_query")
    parser.add_argument("new_clarity_query")
    args=parser.parse_args()

    old_words = get_query_words(args.old_clarity_query)
    new_words = get_query_words(args.new_clarity_query)

    diff_words = {}
    discard_words = {}
    for qid in new_words:
        diff = new_words[qid] - old_words[qid]
        if diff:
            diff_words[qid] = list(diff)
            discard_words[qid] = list(old_words[qid] - new_words[qid])


    print "%d query have new words" %(len(diff_words))
    for qid in diff_words:
        print "for query %s:" %qid
        print "\tnew words:%s" %(" ".join(diff_words[qid]))
        print "\told words:%s" %(" ".join(discard_words[qid]))

if __name__=="__main__":
    main()

