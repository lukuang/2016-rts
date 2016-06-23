"""
plot histograms for relevant/all tweets
in per-hour basis for each topic
"""

import os
import json
import sys
import re
import argparse
import codecs
from lxml import etree
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
sys.path.append("../")
from process_tweet.tweet_proc import *

class TimeBins(object):
    def __init__(self, gap=3600,start=START15,end=END15):
        self.start,self.end = start,end
        self.bin_size = (self.start.epoch-self.end.epoch)/gap
        self.bins = [0]*self.bin_size

    def increment_size(self,bin_id):
        self.bins[bin_id] += 1


class RelTimeBins(TimeBins):

    def add_tweet_epoch_ms(self,epoch_ms):
        epoch = epoch_ms/1000
        self.add_tweet_epoch(epoch)

    def add_tweet_epoch(self,epoch):
        bin_id = (epoch-self.start.epoch)/self.gap
        self.increment_size(bin_id)


class AllTimeBins(TimeBins):

    def add_tweet_file_name(self,file_name):
        if file_name.find("/") != -1:
            dir_path,time_string = os.path.split(file_name)
        else:
            time_string = file_name


        m = re.match("^(\d+)-(\d+)$",time_string)
        if m is not None:
            day = int(m.group(1))
            hour = int(m.group(2))
            day_diff = day - start.struct_time.tm_mday
            bin_id = day_diff*24
            bin_id += hour
            self.increment_size(bin_id)
        else:
            raise ValueError("the file name %s is not right" %(time_string))

def read_epoch_file(epoch_file):
    """read the epoch file and return the mapping 
    {tweetid:epoch time}
    """

    tweet2epoch = {}
    with open(epoch_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            tweet2epoch[parts[0]] = parts[2]
    return tweet2epoch

def read_qrel(qrel):
    """read qrel file and return mapping
    {topicid:[relevent tweetid]}
    """
    rel_tweets = {}
    with open(qrel) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            topicid = "MB" + parts[0]
            if topicid not in rel_tweets:
                rel_tweets[topicid] = []
            tweetid = parts[2]
            score = int(parts[3])
            if score > 0:
                rel_tweets[topicid].append(tweetid)
    return rel_tweets

def read_cluster_file(cluster_file):
    """read the cluster file and return mapping
    {topic:[[tweetid]]}
    """
    clusters = {}
    topcis = json.load(open(cluster_file))["topcis"]
    for topicid in topcis:
        clusters[topicid] = topcis[topicid]["clusters"]
    return clusters

def get_num_of_tweets(single_file):
    document = open("20-0").read()
    document = "<root> %s </root>" %(document)
    root = etree.fromstring(document)
    return len(root)

def plot_hist(bins1,bins2)
    



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tweet_dir","-td",default="/lustre/scratch/lukuang/2015-RTS/2015_RTS/2015-data/collection/web-data/within/indri_text")
    parser.add_argument("epoch_file")
    parser.add_argument("qrel")
    parser.add_argument("clusters")
    args=parser.parse_args()
    clusters = read_cluster_file(args.clusters)
    rel_tweets = read_qrel(args.qrel)
    tweet2epoch = read_epoch_file(args.epoch_file)
    all_files = os.walk(args.tweet_dir).next()[2]


    all_bins = AllTimeBins()
    for single_file in all_files:
        single_file = os.path.join(args.tweet_dir,single_file)
        num_of_tweets = get_num_of_tweets(single_file)
        for _ in range(num_of_tweets)
            all_bins.add_tweet_file_name(single_file)
    with open("all_bins","w") as f:
        f.write(json.dumps(all_bins.bins))

    rel_bins = {}
    for topicid in rel_tweets:
        rel_bins[topicid] = RelTimeBins()
        for tweetid in rel_tweets[topicid]:
            rel_bins[topicid].add_tweet_epoch(rel_tweets[topicid][tweetid])

    cluster_bins = {}          
    for topicid in clusters:
        cluster_bins[topicid] = [RelTimeBins()] * len(clusters[topicid])

    plot_hist(rel_bins.bins,all_bins.bins)


if __name__=="__main__":
    main()

