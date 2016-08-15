"""
remove duplicate in the results
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def get_text(index_dir,tweet_id):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tweet_id)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None


class PreviousResults(object):
    """class used to store previously post
    tweets for each run and query, as well as
    check novalty of the tweet
    """

    def __init__(self,debug=False):
        self._debug = debug
        self._previous_results = {}

    
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





def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_file")
    parser.add_argument("dest_file")
    parser.add_argument("--tweet_text_file","-ttf",default="/infolab/headnode2/lukuang/2016-rts/code/2016/senario_b/data/tweet_text_file")
    parser.add_argument("--debug","-de",action="store_true")
    parser.add_argument("--index_dir","-ir",default="/infolab/headnode2/lukuang/2016-rts/data/incremental_index")
    args=parser.parse_args()

    previous_results = PreviousResults(args.debug)
    tweet_text_map = {}
    if os.path.exists(args.tweet_text_file):
        if os.stat(args.tweet_text_file).st_size!=0:
            tweet_text_map = json.load(open(args.tweet_text_file))

    with open(args.dest_file,'w') as of:
        with open(args.src_file) as f:
            for line in f:
                parts = line.split()

                qid = parts[1]
                tid = parts[3]
                run_name = parts[6]
                
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

