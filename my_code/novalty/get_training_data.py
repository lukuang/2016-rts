"""
get training data for novalty check
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.corpus import Sentence

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import T2Day,SemaCluster
from Levenshtein import ratio

def get_relevant_tweets(query_relevant_file,valid_tids,qid):
    tweets = {}
    with open(query_relevant_file) as f:
        for line in f: 
            tweet_data = json.loads(line)
            tid = tweet_data['id_str']
            if tid not in valid_tids[qid]:
                continue
            text = tweet_data['text'].lower()
            tweets[tid] = Sentence(text)
    return tweets


def compute_term_diff(t1_model,t2_model):
    words1 =    [ x[0] for x in t1_model.model.most_common()]
    words2 = [ x[0] for x in t2_model.model.most_common()]
    common = list(set(words1).intersection(words2))
    return len(common)*1.0/max(len(words1),len(words2))

def write_to_disk(feature_vector,label_vector,
                  dest_dir,training_qids):
    with open(os.path.join(dest_dir,"X"),'w') as f:
        f.write(json.dumps(feature_vector))


    with open(os.path.join(dest_dir,"y"),'w') as f:
        f.write(json.dumps(label_vector))

    if training_qids:
        with open(os.path.join(dest_dir,"query_ids"),'w') as f:
            f.write(json.dumps(training_qids))

def get_valid_tids(cluster_file):
    valid_tids = {}
    data = json.load(open(cluster_file))
    data = data["topics"]
    for qid in data:
        valid_tids[qid] = []
        for cluster  in data[qid]["clusters"]:
            for tid in cluster:
                if tid not in valid_tids[qid]:
                    valid_tids[qid].append(tid)
    return valid_tids



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--relevant_tweet_dir","-rd",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/relevant_tweets")
    parser.add_argument("--test","-t",action="store_true")
    parser.add_argument("--query_id_files","-qid")
    parser.add_argument("--debug",'-de',action="store_true")
    parser.add_argument("dest_dir")
    args = parser.parse_args()

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)

    feature_vector = []
    label_vector = []
    training_qids = []

    # There are qids in the qrel file but not in
    # cluster file. Ignore those files
    valid_tids = get_valid_tids(args.cluster_file)

    print "there are %d vaild tids" %len(valid_tids)
    if args.test:
        training_qids = json.load(open(args.query_id_files))

    for qid in os.walk(args.relevant_tweet_dir).next()[2]:
        if args.test:
            if qid not in training_qids:
                continue
        query_relevant_file = os.path.join(args.relevant_tweet_dir,qid)
        tweets = get_relevant_tweets(query_relevant_file,valid_tids,qid)
        tids = tweets.keys()
        size = len(tids)
        for i in range(size):
            tid = tids[i]
            for j in range(i+1,size):
                second_tid = tids[j]
                if sema_cluster.same_cluster(qid,tid,second_tid):
                    label_vector.append(1)
                else:
                    label_vector.append(0)

                    
                t1_model = tweets[tid].raw_model
                t2_model = tweets[second_tid].raw_model
                
                cosine_sim = t1_model.cosine_sim(t2_model)
                
                term_diff = compute_term_diff(t1_model,t2_model)
            
                edit_ratio = ratio(tweets[tid].text,tweets[second_tid].text)
                #print type(cosine_sim),type(term_diff),type(edit_ratio)
                #print cosine_sim,term_diff,edit_ratio
                if args.debug and label_vector[-1]==1:
                    if cosine_sim==.0 or term_diff==.0 or edit_ratio==.0:
                        same = "NO"
                        if sema_cluster.same_cluster(qid,tid,second_tid):
                            same = "YES"
                        print "in the same cluster? %s" %(same)
                        print "tid: %s, second tid %s" %(tid,second_tid)
                        print "tweet1: %s" %(tweets[tid].text)
                        print "tweet2: %s" %(tweets[second_tid].text)
                    
                        print "cosine sim: %f" %(cosine_sim)
                        print "term diff: %f" %(term_diff)
                        print "ratio: %f" %(edit_ratio)
                        sys.exit(0)
                if label_vector[-1]==0 and (cosine_sim>=1.0 or term_diff>=1.0 or edit_ratio>=1.0):
                    print "tid: %s, second tid %s" %(tid,second_tid)
                    print "tweet1: %s" %(tweets[tid].text)
                    print "tweet2: %s" %(tweets[second_tid].text)
                
                    print "cosine sim: %f" %(cosine_sim)
                    print "term diff: %f" %(term_diff)
                    print "ratio: %f" %(edit_ratio)

                single_feature_vector = [cosine_sim, term_diff,edit_ratio]
                feature_vector.append(single_feature_vector)

    write_to_disk(feature_vector,label_vector,args.dest_dir,training_qids)


if __name__=="__main__":
    main()

