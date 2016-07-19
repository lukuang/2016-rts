"""
show the user-relevant correlation
"""

import os
import json
import sys
import re
import argparse
import codecs


_current_dir = os.path.dirname(os.path.abspath(__file__))
_module_dir = os.path.dirname(os.path.abspath(_current_dir))
import sys
sys.path.append(_module_dir)


def read_cluster_file(cluster_file):
    cluster_info = {}
    cluster_data = json.load(open(cluster_file))
    topics = cluster_data["topics"]
    for qid in topics:
        cluster_info[qid] = topics[qid]["clusters"]
    
    return cluster_info




def show_usr_tweet_corr(relevent_tweet_dir,qid):
    relevant_tweet_file = os.path.join(relevent_tweet_dir,qid)
    users = {}
    with open(relevant_tweet_file) as f:
        for line in f:
            line = line.rstrip()
            if len(line)!=0:
                tweet = json.loads(line)
                try:
                    uid = tweet["user"]["id"]
                except KeyError:
                    message = "mal-formated tweet for query:%s\n"%qid
                    message += "The tweet is:\n%s" %(line)
                    raise RuntimeError(message)
                else:
                    if uid not in users:
                        users[uid] = 0

                    users[uid] += 1

    print "-"*20
    print "for query %s" %qid
    for uid in users:
        print "%s:%d" %(uid,users[uid])
    print "-"*20


def show_usr_cluster_corr(cluster_info,relevent_tweet_dir,qid):
    relevant_tweet_file = os.path.join(relevent_tweet_dir,qid)
    users = {}
    with open(relevant_tweet_file) as f:
        for line in f:
            line = line.rstrip()
            if len(line)!=0:
                tweet = json.loads(line)
                try:
                    uid = tweet["user"]["id_str"]
                    tid = tweet["id_str"]
                except KeyError:
                    message = "mal-formated tweet for query:%s\n"%qid
                    message += "The tweet is:\n%s" %(line)
                    raise RuntimeError(message)
                else:
                    for i in range(len(cluster_info[qid]) ):
                        if tid in cluster_info[qid][i]:
                            if i not in users:
                                users[i] = {}
                            if uid not in users[i]:
                                users[i][uid] = 0
                            users[i][uid] += 1


    print "-"*20
    print "for query %s" %qid
    for cid in users:
        print "%d:" %(cid)
        for uid in users[cid]:
            print "\t%s:%d" %(uid,users[cid][uid])
    print "-"*20




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster_file","-cf",
                        default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json") 
    parser.add_argument("--relevent_tweet_dir","-rd",
                        default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/relevant_tweets")
    parser.add_argument("qid")
    parser.add_argument("--show_cluster","-sc",action='store_true')
    args=parser.parse_args()

    if args.show_cluster:
        cluster_info = read_cluster_file(args.cluster_file)
        show_usr_cluster_corr(cluster_info,args.relevent_tweet_dir,args.qid)
    else:
        show_usr_tweet_corr(args.relevent_tweet_dir,args.qid)

if __name__=="__main__":
    main()

