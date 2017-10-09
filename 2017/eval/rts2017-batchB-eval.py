#!/usr/bin/python

# This is the evaluation script for the TREC 2017 RTS evaluation
# (scenario B) with batch NIST assessor judgments, v1.0.

__author__ = 'Luchen'
import argparse
import json
import numpy
import math
import gzip


parser = argparse.ArgumentParser(description='Evaluation script for TREC 2016 RTS scenario B with batch NIST assessor judgments')
parser.add_argument('-q', required=True, metavar='qrels', help='batch qrels file')
parser.add_argument('-c', required=True, metavar='clusters', help='cluster anotations')
parser.add_argument('-t', required=True, metavar='tweetsdayepoch', help='tweets2dayepoch file')
parser.add_argument('-r', required=True, metavar='run', help='run file')

args = parser.parse_args()
qrels_path = vars(args)['q']
clusters_path = vars(args)['c']
file_tweet2day = vars(args)['t']
run_path = vars(args)['r']


K = 10
days = []
for i in range(29, 32):
    days.append("201707%02d" % i)
for i in range(1, 6):
    days.append("201708%02d" % i)


# qrels dictionary, {topic: {tweetid: gain}}
qrels_dt = {}
clusters_day_dt = {}
for line in open(qrels_path).readlines():
    line = line.strip().split()
    topic = line[0]
    tweetid = line[2]
    score = int(line[3])
    if score == -2:
        score = 0
    else:
        score /= float(2)
    if topic in qrels_dt:
        qrels_dt[topic][tweetid] = score
    else:
        qrels_dt[topic] = {tweetid: score}
        clusters_day_dt[topic] = {day: [] for day in days}


# created timestamp and date for each tweetid in the qrel
# tweet2day_dt: {tweetid: date}
tweet2day_dt = {}
for line in open(file_tweet2day).readlines():
    line = line.strip().split()
    tweet2day_dt[line[0]] = line[1]


# cluster dictionaries
clusters_clusterid_dt = {}
clusters_topic_dt = json.load(open(clusters_path))
for topic in clusters_topic_dt:
    clusters_json = clusters_topic_dt[topic]["clusters"]
    if topic not in clusters_clusterid_dt:
        clusters_clusterid_dt[topic] = {}
    for clusterid in clusters_json.keys():
        for tweetid in clusters_json[clusterid]["tweets"]:
            if tweet2day_dt[tweetid] in days:
                clusters_clusterid_dt[topic][tweetid] = clusterid
                clusters_day_dt[topic][tweet2day_dt[tweetid]].append(tweetid)


# run dictionaries
# run_dt: {topic: {date: [tweetids}}
runname = ''
run_dt = {}
run_epoch_dt = {}
for line in gzip.open(run_path, "r").readlines():

    line = line.decode().strip().split()

    runname = line[6]
    topic = line[1]
    if topic in qrels_dt:
        if topic not in run_dt:
            run_dt[topic] = {}
        day = line[0]
        if day not in run_dt[topic]:
            run_dt[topic][day] = []
        tweetid = line[3]
        run_dt[topic][day].append(tweetid)

print("{0}\t{1:5s}\t{2:6s}\t{3:6s}".format("runtag".ljust(len(runname)), "topic", "nDCGp", "nDCG1"))

total_ndcg1, total_ndcgp = 0.0, 0.0
for topic in sorted(qrels_dt):
    topic_ndcg1, topic_ndcgp = 0.0, 0.0
    exist_clusterids = set()
    for day in days:
        interesting = False
        max_gain_dt = {}
        tweets_fromprotocol = clusters_day_dt[topic][day]
        for tweetid in tweets_fromprotocol:
            clusterid = clusters_clusterid_dt[topic][tweetid]
            if clusterid not in exist_clusterids:
                interesting = True
                if clusterid not in max_gain_dt:
                    max_gain_dt[clusterid] = qrels_dt[topic][tweetid]
                else:
                    max_gain_dt[clusterid] = max(max_gain_dt[clusterid], qrels_dt[topic][tweetid])
        if interesting:
            if topic in run_dt and day in run_dt[topic]:
                ndcg = 0.0
                gains = []
                for tweetid in run_dt[topic][day]:
                    gain = 0.0
                    if tweetid in clusters_day_dt[topic][day]:
                        clusterid = clusters_clusterid_dt[topic][tweetid]
                        if clusterid not in exist_clusterids:
                            exist_clusterids.add(clusterid)
                            gain = qrels_dt[topic][tweetid]
                            # tweet gain is with respect to its own gain, not max gain in the cluster
                            # if clusterid in max_gain_dt:
                            #    gain = max_gain_dt[clusterid]
                    gains.append(gain)
                rank_cut = min(len(gains), K)
                dcg = 0.0
                for i in range(rank_cut):
                    gain = gains[i]
                    dcg += float(pow(2, gain) - 1) / math.log(i + 2, 2)

                # compute idcg
                top_gains = list(max_gain_dt.values())
                top_gains.sort(reverse=True)
                rank_cut = min(len(top_gains), K)
                idcg = 0.0
                top_gains = top_gains[:rank_cut]
                for i in range(rank_cut):
                    gain = top_gains[i]
                    idcg += float(pow(2, gain) - 1) / math.log(i + 2, 2)
                if idcg != 0:
                    ndcg = dcg / idcg
                topic_ndcg1 += ndcg
                topic_ndcgp += ndcg
        else:
            if topic not in run_dt or day not in run_dt[topic]:
                topic_ndcg1 += 1
                topic_ndcgp += 1
            elif topic in run_dt and day in run_dt[topic]:
                push_num = min(K, len(run_dt[topic][day]))
                topic_ndcgp += (1 - push_num/float(K))



    topic_ndcg1 /= len(days)
    topic_ndcgp /= len(days)
    print("{0}\t{1:5s}\t{2:.4f}\t{3:.4f}".format(runname, topic, topic_ndcgp, topic_ndcg1))
    total_ndcg1 += topic_ndcg1
    total_ndcgp += topic_ndcgp
total_ndcg1 /= len(qrels_dt)
total_ndcgp /= len(qrels_dt)
print("{0}\t{1:5s}\t{2:.4f}\t{3:.4f}".format(runname, "All", total_ndcgp, total_ndcg1))
