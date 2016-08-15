"""
measure how many terms the expanded query can capture wrt the relevant tweets of this day
"""

import os
import json
import sys
import re
import argparse
import codecs
from myStemmer import pstem as stem

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import SemaCluster,T2Day

def get_tweet_day_map(tweet2day_file):
    """read the tweet2day file and return 
    the tweet id-day mapping as:
    {tweetid:day}
    """
    tweet_day_map = {}
    with open(tweet2day_file) as f:
        for line in f:
            parts = line.split()
            tweetid = unicode(parts[0])
            day_string = parts[1]
            day = unicode(day_string[-2:])
            tweet_day_map[tweetid] = day

    return tweet_day_map


def get_relevant_words_by_day(tweet_day_map,relevant_tweet_dir):
    """ return the relevant words wrt day and query as:
    {qid: {day: (words)} }
    """
    relevant_tweet_words = {}
    for qid in os.walk(relevant_tweet_dir).next()[2]:
        if qid not in relevant_tweet_words:
            relevant_tweet_words[qid] = {}
        relevant_tweet_file = os.path.join(relevant_tweet_dir,qid)
        with open(relevant_tweet_file) as f:
            for line in f:
                tweet_data = json.loads(line)
                tweetid = unicode(tweet_data['id'])
                try:
                    day =  tweet_day_map[tweetid]
                except KeyError:
                    print "cannot find day for %s" %tweetid
                    continue
                else:
                    if day not in relevant_tweet_words[qid]:
                        relevant_tweet_words[qid][day] = set()
                    tweet_text = tweet_data['text'] 
                    relevant_tweet_words[qid][day].update( map(stem,re.findall("\w+",tweet_text)) )

    return relevant_tweet_words

def get_query_words_by_day(query_dir):
    """get query words from the axiomatic expansion
    output and return the map as:
    {qid: {day: []}}
    """
    query_words = {}
    qid_finder = re.compile("<number>([^<]+?)<")
    query_words_finder1 = re.compile("<text>#weight\((.+?)\)</text>")
    query_words_finder2 = re.compile("<text>(.+?)</text>")
    for day in os.walk(query_dir).next()[2]:
        query_file = os.path.join(query_dir,day)
        with open(query_file) as f:
            for line in f:
                if qid_finder.search(line):
                    m = qid_finder.search(line)
                    qid = m.group(1)
                    if qid.find("MB") == -1:
                        qid = "MB"+qid
                    line = "<number>%s</number>\n" %qid
                    if qid not in query_words:
                        query_words[qid] = {}
                    if day not in query_words[qid]:
                        query_words[qid][day] = set()
                elif query_words_finder1.search(line):
                    m = query_words_finder1.search(line)
                    query_word_string = m.group(1)
                    all_words = re.findall("(?<=\s)[a-zA-z]+(?=\s)",query_word_string)
                    query_words[qid][day].update(all_words)
                elif query_words_finder2.search(line):
                    m = query_words_finder2.search(line)
                    query_word_string = m.group(1)
                    all_words = re.findall("\w+",query_word_string)
                    query_words[qid][day].update(all_words)

    return query_words               

def show_coverage(relevant_tweet_words,query_words,sema_cluster):
    """Show the coverage of the query wrt relevant words
    """
    print "Show coverage:"
    for qid in relevant_tweet_words:
        print "for query %s:" %(qid)
        for day in sorted(relevant_tweet_words[qid].keys()):
            common_words = relevant_tweet_words[qid][day]&\
                    query_words[qid][day]
            print "\tfor day %s:%s" %(day," ".join(common_words))
            print "\t\tclusters:%s" %(sorted(sema_cluster.cluster_4_day_qid(day,qid)) )

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relevant_tweet_dir","-rtr",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/relevant_tweets")
    parser.add_argument("query_dir")
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    parser.add_argument("--cluster_file","-cf",default="/infolab/node4/lukuang/2015-RTS/2015-data/clusters-2015.json")

    args=parser.parse_args()

    tweet_day_map = get_tweet_day_map(args.tweet2day_file)
    #print tweet_day_map
    relevant_tweet_words = get_relevant_words_by_day(tweet_day_map,args.relevant_tweet_dir)
    query_words = get_query_words_by_day(args.query_dir)

    t2day = T2Day(args.tweet2day_file)
    sema_cluster = SemaCluster(args.cluster_file,t2day)

    show_coverage(relevant_tweet_words,query_words,sema_cluster)

if __name__=="__main__":
    main()

