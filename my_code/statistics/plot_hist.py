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
#import matplotlib.mlab as mlab
import matplotlib 
matplotlib.use('agg') 
import matplotlib.pyplot as plt
sys.path.append("../")
from process_tweet.tweet_proc import *

class TimeBins(object):
    def __init__(self, gap=3600,start=START15,end=END15):
        self.start,self.end,self.gap = start,end,gap
        #self.bin_size = (self.end.epoch-self.start.epoch)/gap + 1
        #self.bins = [0]*self.bin_size
        self.bins = []
        #print "The size is: %d" %(self.bin_size)

        

class RelTimeBins(TimeBins):

    def add_tweet_epoch_ms(self,epoch_ms):
        epoch = epoch_ms/1000
        self.add_tweet_epoch(epoch)

    def add_tweet_epoch(self,epoch):
        hour_id = (epoch-self.start.epoch)/self.gap
        try:
            self.bins.append(hour_id)
        except IndexError:
            print "wrong index %d" %(hour_id)
            print "epoch %"
            sys.exit(-1)


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
            day_diff = day - self.start.struct_time.tm_mday
            hour_id = day_diff*24
            hour_id += hour
            self.bins.append(hour_id)
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
            tweet2epoch[parts[0]] = int(parts[2])
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
            if 0 < score < 3:
                rel_tweets[topicid].append(tweetid)
    return rel_tweets

def read_cluster_file(cluster_file):
    """read the cluster file and return mapping
    {topic:[[tweetid]]}
    """
    clusters = {}
    topics = json.load(open(cluster_file))["topics"]
    for topicid in topics:
        clusters[topicid] = topics[topicid]["clusters"]
    return clusters

def get_num_of_tweets(single_file):
    document = open(single_file).read()
    document = "<root> %s </root>" %(document)
    root = etree.fromstring(document)
    return len(root)

#TODO implement this function to plot
#histogram
def plot_hist(bins1,bins2,topicid):
    #print bins1
    #print bins2
    plt.hist(bins2, histtype='stepfilled', normed=True, color='b', label='All')
    plt.hist(bins1, histtype='stepfilled', normed=True, color='r', alpha=0.5, label=topicid)
    plt.title("All/%s Histogram" %(topicid))
    plt.xlabel("Bin")
    plt.ylabel("number")
    plt.legend()
    plt.savefig("all-%s.png" %(topicid))
    plt.clf()



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
    if not os.path.exists("all_bins"):
        for single_file in all_files:
            single_file = os.path.join(args.tweet_dir,single_file)
            num_of_tweets = get_num_of_tweets(single_file)
            for _ in range(num_of_tweets):
                all_bins.add_tweet_file_name(single_file)
        with open("all_bins","w") as f:
            f.write(json.dumps(all_bins.bins))
    else:
        all_bins.bins = json.load(open("all_bins"))

    rel_bins = {}
    for topicid in rel_tweets:
        rel_bins[topicid] = RelTimeBins()
        for tweetid in rel_tweets[topicid]:
            rel_bins[topicid].add_tweet_epoch(tweet2epoch[tweetid])
            
    cluster_bins = {}          
    for topicid in clusters:
        cluster_bins[topicid] = [RelTimeBins()] * len(clusters[topicid])

    for topicid in rel_bins:
        if not rel_bins[topicid].bins:
            continue
        plot_hist(rel_bins[topicid].bins,all_bins.bins,topicid)
        #break

if __name__=="__main__":
    main()

