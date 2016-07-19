"""
get all relevant tweets
"""

import os
import json
import sys
import re
import argparse
import codecs


def get_rel_ids(qrel_file):
    relevant_ids = {}
    with open(qrel_file)  as f:
        for line in f:
            line = line.rstrip()
                parts = line.split()
                
                qid = parts[0]
                tid = parts[2]
                score = int(parts[3])

                if "MB" not in parts[0]:
                    qid = "MB%s" %qid
                if score > 0:
                    relevant_ids[tid] = qid
    return relevant_ids


def get_rel_tweets(hour_file,relevant_ids):
    relevant_tweets = {}
    with open(hour_file) as f:
        for line in f:
            line = line.rstrip()
            if len(line) == 0:
                continue
            tweet_data = json.loads(line)
            if "delete" not in tweet_data:
                try:
                    id_str = tweet_data["id_str"]
                    if id_str in relevant_ids:
                        qid = relevant_ids[id_str]
                        if qid not in relevant_tweets:
                            relevant_tweets[qid] = []
                        relevant_tweets[qid].append(tweet_data)
                                
                except KeyError:
                    print "mal-format tweet:\n%s\n" %line

    return relevant_tweets


def write_relevant_tweets(relevant_tweets,dest_dir,file_suffix):
    #dest_file = os.path.join(dest_dir,"%s"%file_suffix)
   
    # with codecs.open(dest_file,"w","utf-8") as f:
    #     for tweet in relevant_tweets:
    #         f.write(json.dumps(tweet)+"\n") 

    for qid in relevant_tweets:
        dest_file = os.path.join(dest_dir,"%s"%qid)
        with codecs.open(dest_file,"a","utf-8") as f:
            for tweet in relevant_tweets[qid]:
                f.write(json.dumps(tweet)+"\n") 


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_dir")
    parser.add_argument("qrel_file")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    relevant_ids = get_rel_ids(args.qrel_file)

    for hour_file in os.walk(args.raw_dir).next()[2]:
        print "process file %s" %(hour_file)
        m = re.search("(\d+-\d+)$",hour_file)
        if m is not None:
            file_suffix
            hour_file = os.path.join(args.raw_dir,hour_file)
            relevant_tweets = get_rel_tweets(hour_file,relevant_ids)
            write_relevant_tweets(relevant_tweets,args.dest_dir,file_suffix)

        else:
            raise RuntimeError("wrong file name %s\n" %(hour_file))

if __name__=="__main__":
    main()

