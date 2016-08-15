"""
remove duplicate in the results
"""

import os
import json
import sys
import re
import argparse
import codecs
from get_text import get_text


class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,previous_result_file,debug=False):
        self._previous_result_file = previous_result_file
        self._debug = debug
        self._load_previous_results()
        

    def _load_previous_results(self):
        self._previous_results = {}
        if os.path.exists(self._previous_result_file):
            f_size = os.stat(self._previous_result_file).st_size
            if f_size!=0:
                self._previous_results =\
                    json.load(open(self._previous_result_file))


    def _store_tweet(self,tweet_text,run_name,qid):
        if self._debug:
            print "store new tweet %s\nfor query %s run %s"\
                %(tweet_text,qid,run_name)
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
        
        if qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []
        
        self._previous_results[run_name][qid].append(tweet_text)


    def _term_diff(self,tweet_text,t_text):
        words1 = re.findall("\w+",tweet_text)
        words2 = re.findall("\w+",t_text)
        common = list(set(words1).intersection(words2))
        return len(common)*1.0/max(len(words1),len(words2))


    def _check_tweet_redundant(self,tweet_text,t_text):
        if self._debug:
            print "check diff between %s\nand %s" %(tweet_text,t_text)
        term_diff = self._term_diff(tweet_text,t_text)
        if self._debug:
            print "the metric is %f" %(term_diff)
        if term_diff >= 0.500000:
            return True
        else:
            return False



    def is_redundant(self,tweet_text,run_name,qid):
        
        if run_name not in self._previous_results:
            self._previous_results[run_name] = {}
            self._previous_results[run_name][qid] = []
            
        elif qid not in self._previous_results[run_name]:
            self._previous_results[run_name][qid] = []

        
        else:

            for t_text in self._previous_results[run_name][qid]:
                if self._check_tweet_redundant(tweet_text,t_text):
                    if self._debug:
                        print "%s\n is redundant to\n%s" %(tweet_text,t_text)
                        print "-"*20
                    return True

        self._store_tweet(tweet_text,run_name,qid)
        return False


    def store_previous(self):
        with open(self._previous_result_file,'w') as f:
            f.write(json.dumps(self._previous_results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_file")
    parser.add_argument("dest_file")
    parser.add_argument("--tweet_text_file","-ttf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet_text_file")
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--senario_b","-b",action="store_true")
    parser.add_argument("--index_dir","-ir",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29")
    args=parser.parse_args()

    previous_result_file = "./previous_result"
    previous_results = PreviousResults(previous_result_file,args.debug)
    tweet_text_map = {}
    if os.path.exists(args.tweet_text_file):
        if os.stat(args.tweet_text_file).st_size!=0:
            tweet_text_map = json.load(open(args.tweet_text_file))

    with open(args.dest_file,'w') as of:
        with open(args.src_file) as f:
            for line in f:
                parts = line.split()
                if args.senario_b:
                    qid = parts[1]
                    tid = parts[3]
                    run_name = parts[6]
                else:
                    qid = parts[0]
                    tid = parts[1]
                    run_name = parts[3] 
                try:
                    tweet_text = tweet_text_map[tid]
                except KeyError:
                    print "need to fetch text for %s" %tid
                    tweet_text = get_text(args.index_dir,tid)

                    tweet_text_map[tid] = tweet_text

                if tweet_text is None:
                    raise RuntimeError("the tweet id %s does not have text!" %tid)
                else:
                    if not previous_results.is_redundant(tweet_text,run_name,qid):
                        of.write(line)

    with open(args.tweet_text_file,"w") as f:
        f.write(json.dumps(tweet_text_map))

if __name__=="__main__":
    main()

