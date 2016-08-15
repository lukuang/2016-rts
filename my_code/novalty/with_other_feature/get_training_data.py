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
from my_code.distribution.data import T2Day,SemaCluster,Qrel
from Levenshtein import ratio


def get_clarity(clarity_dir,judged_qids):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in judged_qids:
            clarities[date][qid] = date_clarity[qid]

    return clarities

def get_lm_difference(difference_file):
    differences = json.load(open(difference_file))

    return differences


def get_relevant_tweets(relevant_tweet_dir,valid_tids):
    tweets = {}
    for qid in os.walk(relevant_tweet_dir).next()[2]:
        query_relevant_file = os.path.join(relevant_tweet_dir,qid)
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
    all_words = set(words1)
    all_words.update(words2)
    return len(common)*1.0/(len(all_words))

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

def generate_measure_computer(measure_method):
    def compute_measure(tweets,tid,previous_tid):
        if measure_method == "cosine-sim" :
            t1_model = tweets[tid].raw_model
            t2_model = tweets[previous_tid].raw_model
                  
            sim = t1_model.cosine_sim(t2_model)
        elif measure_method == "set-sim":
            t1_model = tweets[tid].raw_model
            t2_model = tweets[previous_tid].raw_model

            sim = compute_term_diff(t1_model,t2_model)
        elif measure_method == "edit-sim":    
            sim = ratio(tweets[tid].text,tweets[previous_tid].text)
        else:
            raise NotImplementedError("Measure %s is not implemented"
                                       %(measure_method))
        return sim


    return compute_measure

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")
    parser.add_argument("--eval_topics","-ef",default="/infolab/node4/lukuang/2015-RTS/2015-data/eval_topics")
    parser.add_argument("--qrel_file","-qf",default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--relevant_tweet_dir","-rd",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/relevant_tweets")
    parser.add_argument("--clarity_dir","-cd",default="/infolab/node4/lukuang/2015-RTS/src/my_code/novalty/with_other_feature/data/clarity")
    parser.add_argument("--test_qid_file","-t",action="store_const",const="/infolab/node4/lukuang/2015-RTS/src/my_code/distribution/query_prediction/threshold_with_lm_difference/data/test_qids")
    parser.add_argument("difference_file")
    parser.add_argument("--measure_method","-m",choices=["cosine-sim","set-sim","edit-sim"],default="cosine-sim")
    parser.add_argument("--debug",'-de',action="store_true")
    parser.add_argument("dest_dir")
    args = parser.parse_args()

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)
    qrel = Qrel(args.qrel_file)

    feature_vector = []
    label_vector = []
    training_qids = []

    compute_measure = generate_measure_computer(args.measure_method)

    # There are qids in the qrel file but not in
    # cluster file. Ignore those files
    valid_tids = get_valid_tids(args.cluster_file)

    tweets = get_relevant_tweets(args.relevant_tweet_dir,valid_tids)

    eval_topics = json.load(open(args.eval_topics))
    training_qids = qrel.qids
    if args.test_qid_file:
        training_qids = []
        temp_qids = json.load(open(args.test_qid_file))
        for qid in temp_qids:
            if qid in eval_topics:
                training_qids.append(qid)

    print "get clarity"
    clarities = get_clarity(args.clarity_dir,training_qids)

    print "get language model difference"
    differences = get_lm_difference(args.difference_file)

    day_cluster = sema_cluster.day_cluster

    previous_tweets = {}
    print "start generating training data"
    for date in sorted(day_cluster.keys()):
        if date not in previous_tweets:
            previous_tweets[date] = {}
        for qid in day_cluster[date]:
            if qid not in previous_tweets[date]:
                previous_tweets[date][qid] = []
            for cluster_id in day_cluster[date][qid]:
                for tid in day_cluster[date][qid][cluster_id]:
                    # skip tweet not in the web archive
                    if tid not in tweets:
                        continue
                    # get training data for tweets in previous days first
                    for previous_day in previous_tweets:
                        if previous_day == date:
                            continue
                        else:
                            if qid in previous_tweets[previous_day]:
                                for previous_tid in previous_tweets[previous_day][qid]:
                                    if sema_cluster.same_cluster(qid,tid,previous_tid):
                                        label_vector.append(1)
                                    else:
                                        label_vector.append(0)
                                    single_feature_vector = [
                                                                clarities[date][qid],
                                                                clarities[previous_day][qid],
                                                                differences[qid][previous_day][date],
                                                                compute_measure(tweets,tid,previous_tid)
                                                            ]
                                    feature_vector.append(single_feature_vector)
                    # get training data for this day
                    for previous_tid in previous_tweets[date][qid]:
                        if sema_cluster.same_cluster(qid,tid,previous_tid):
                                        label_vector.append(1)
                        else:
                            label_vector.append(0)
                        single_feature_vector = [
                                                    clarities[date][qid],
                                                    clarities[date][qid],
                                                    .0,
                                                    compute_measure(tweets,tid,previous_tid)
                                                ]
                        feature_vector.append(single_feature_vector)
                    previous_tweets[date][qid].append(tid)


    
    write_to_disk(feature_vector,label_vector,args.dest_dir,training_qids)


if __name__=="__main__":
    main()

