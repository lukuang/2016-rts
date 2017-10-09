#!/usr/bin/python

# This is the evaluation script for the TREC 2017 RTS evaluation
# (scenario A) with batch NIST assessor judgments, v1.00. Based on
# script for TREC 2016 RTS evaluation.
#
# Release History:
#
# - v1.00 (Sept 2017): Original release

__author__ = 'Luchen'
import argparse
import json
import numpy
from datetime import datetime
import sys

parser = argparse.ArgumentParser(description='Evaluation script for TREC 2017 RTS '
                                             'scenario A with batch NIST assessor judgments')
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
unixTimestamp = datetime.utcfromtimestamp(0)

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
# tweet2epoch_dt: {tweetid: epoch time}
tweet2day_dt = {}
tweet2epoch_dt = {}
for line in open(file_tweet2day).readlines():
    line = line.strip().split()
    tweet2day_dt[line[0]] = line[1]
    tweet2epoch_dt[line[0]] = line[2]


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
# run_epoch_dt: {topic: {tweetid: adjusted epoch time}}
runname = ''
run_dt = {}
run_epoch_dt = {}
run_lines = open(run_path).readlines()
if len(run_lines) == 0:
    print("This is an empty run.")
    sys.exit()
for line in run_lines:
    line = line.strip().split()
    runname = line[3]
    topic = line[0]
    if topic in qrels_dt:
        tweetid = line[1]
        pushed_at = datetime.strptime("17"+line[2], "%y%m%d-%H:%M:%S")
        epoch = int((pushed_at - unixTimestamp).total_seconds())
        if topic not in run_dt:
            run_dt[topic] = {}
            run_epoch_dt[topic] = {}
        if tweetid in tweet2day_dt and tweet2day_dt[tweetid] in days:
            if epoch >= int(tweet2epoch_dt[tweetid]):
                day = tweet2day_dt[tweetid]
                if day in run_dt[topic]:
                    run_dt[topic][day].append(tweetid)
                else:
                    run_dt[topic][day] = [tweetid]
                run_epoch_dt[topic][tweetid] = epoch



print("{0}\t{1:5s}\t{2:6s}\t{3:6s}\t{4:6s}\t{5:6s}\t{6:10s}\t{7:10s}\t{8:10s}\t{9:15s}\t{10:15s}\t{11}".format(
    "runtag".ljust(len(runname)), "topic",
    "EGp", "EG1", "nCGp", "nCG1",
    "GMP.33", "GMP.50", "GMP.66",
    "mean_latency", "median_latency",
    "total_length"))

total_eg1, total_egp, total_ncg1, total_ncgp, total_gmp_33, total_gmp_50, total_gmp_66 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
latency_gained = []
total_length = 0
for topic in sorted(qrels_dt):
    topic_eg1, topic_egp, topic_ncg1, topic_ncgp, topic_gmp_33, topic_gmp_50, topic_gmp_66 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    topic_latency = []
    length = 0
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
                eg, ncg = 0.0, 0.0
                gmp_33, gmp_50, gmp_66 = 0.0, 0.0, 0.0
                gains = []
                pain_count = 0
                length += len(run_dt[topic][day])
                for tweetid in run_dt[topic][day]:
                    gain, delay = 0.0, 0.0
                    if tweetid in clusters_day_dt[topic][day]:
                        clusterid = clusters_clusterid_dt[topic][tweetid]
                        if clusterid not in exist_clusterids:
                            exist_clusterids.add(clusterid)
                            gain = qrels_dt[topic][tweetid]
                            # latency of each tweet is with respect to the first tweet in the cluster
                            first_tweetid_in_cluster = clusters_topic_dt[topic]["clusters"][clusterid]["tweets"][0]
                            delay = (
                                float(run_epoch_dt[topic][tweetid]) - float(tweet2epoch_dt[first_tweetid_in_cluster]))
                            delay = max(0, delay)
                    gains.append(gain)
                    if gain > 0:
                        topic_latency.append(delay)
                    else:
                        pain_count += 1

                eg = sum(gains[:min(len(gains), K)]) / len(run_dt[topic][day])
                max_gains = list(max_gain_dt.values())
                max_gains.sort(reverse=True)
                max_gain = sum(max_gains[:min(len(max_gains), K)])
                ncg = sum(gains[:min(len(gains), K)]) / max_gain

                gmp_33 = 0.33 * sum(gains[:min(len(gains), K)]) - (1 - 0.33) * pain_count
                gmp_50 = 0.5 * sum(gains[:min(len(gains), K)]) - 0.5 * pain_count
                gmp_66 = 0.66 * sum(gains[:min(len(gains), K)]) - (1 - 0.66) * pain_count
                topic_eg1 += eg
                topic_egp += eg
                topic_ncg1 += ncg
                topic_ncgp += ncg
                topic_gmp_33 += gmp_33
                topic_gmp_50 += gmp_50
                topic_gmp_66 += gmp_66
        else:
            if topic not in run_dt or day not in run_dt[topic]:
                topic_eg1 += 1
                topic_ncg1 += 1
                topic_egp += 1
                topic_ncgp += 1

            elif topic in run_dt and day in run_dt[topic]:
                push_num = len(run_dt[topic][day])
                topic_egp += (1 - push_num / float(K))
                topic_ncgp += (1 - push_num / float(K))
                gmp_33 = - (1 - 0.33) * push_num
                gmp_50 = - (1 - 0.5) * push_num
                gmp_66 = - (1 - 0.66) * push_num
    topic_eg1 /= len(days)
    topic_egp /= len(days)
    topic_ncg1 /= len(days)
    topic_ncgp /= len(days)
    topic_gmp_33 /= len(days)
    topic_gmp_50 /= len(days)
    topic_gmp_66 /= len(days)
    mean_topic_latency = numpy.mean(topic_latency) if topic_latency != [] else 0
    median_topic_latency = numpy.median(topic_latency) if topic_latency != [] else 0
    print("{0}\t{1:5s}\t{2:.4f}\t{3:.4f}\t{4:.4f}\t{5:.4f}\t{6:<10.4f}\t{7:<10.4f}\t{8:<10.4f}\t{9:<15.1f}\t{10:<15.1f}\t{11}".format(
        runname, topic, topic_egp, topic_eg1, topic_ncgp, topic_ncg1,
        topic_gmp_33, topic_gmp_50, topic_gmp_66,
        mean_topic_latency, median_topic_latency,
        length))
    total_eg1 += topic_eg1
    total_egp += topic_egp
    total_ncg1 += topic_ncg1
    total_ncgp += topic_ncgp
    total_gmp_33 += topic_gmp_33
    total_gmp_50 += topic_gmp_50
    total_gmp_66 += topic_gmp_66

    total_length += length
    latency_gained += topic_latency

total_eg1 /= len(qrels_dt)
total_egp /= len(qrels_dt)
total_ncg1 /= len(qrels_dt)
total_ncgp /= len(qrels_dt)
total_gmp_33 /= len(qrels_dt)
total_gmp_50 /= len(qrels_dt)
total_gmp_66 /= len(qrels_dt)

print("{0}\t{1:5s}\t{2:.4f}\t{3:.4f}\t{4:.4f}\t{5:.4f}\t{6:<10.4f}\t{7:<10.4f}\t{8:<10.4f}\t{9:<15.1f}\t{10:<15.1f}\t{11}".format(
        runname, "All", total_egp, total_eg1, total_ncgp, total_ncg1,
        total_gmp_33, total_gmp_50, total_gmp_66,
        numpy.mean(latency_gained) if latency_gained != [] else 0,
        numpy.median(latency_gained) if latency_gained != [] else 0,
        total_length))
