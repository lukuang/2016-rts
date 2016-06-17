"""
get tweets by their ids
"""

import os
import json
import sys
import re
import argparse
import codecs
import math
import time
from time import gmtime, strftime
import tweepy 
from tweepy.error import RateLimitError,TweepError
from tweepy import OAuthHandler





RATE_LIMIT = 180



def limit_handled(cursor):
    """handle rate limit by waiting
    for a 15 mins window
    """
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "reached rate limit and pause at:",now
            time.sleep(15 * 60)
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "restart at:",now


def read_tweet_id(id_file):
    """get tweet id from a file
    """
    tweet_ids = []
    with open(id_file) as f:
        for line in f:
            parts = line.split()
            tweet_id = parts[0]
            tweet_ids.append(tweet_id)
    return tweet_ids


def get_tweets_by_ids(tweet_ids,dest_dir,auth_file,record_file):
    """use statuse look up api to get
    tweets for ids
    """

    para = json.load(open(auth_file))
    consumer_key=str(para["consumer_key"])
    consumer_secret=str(para["consumer_secret"])
    access_token=str(para["access_token"])
    access_token_secret=str(para["access_token_secret"])

    record = {}
    if os.path.exists(record_file):
        with open(record_file) as f:
            for line in f:
                line = line.rstrip()
                record[line] = 0
    #print consumer_key
    #print consumer_secret
    #print access_token
    #print access_token_secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    size = len(tweet_ids)
    print "total size",size
    gap = 100
    num_of_requests = int( math.ceil(size*1.0/gap) )
    results = []
    new_record = []
    for i in range(num_of_requests):
        if (i%10000==0):
            print "processed ",i
        temp_list = tweet_ids[i*gap:(i+1)*gap]
        sub_id_list = []
        for tweet_id in temp_list:
            if tweet_id not in record:
                sub_id_list.append(tweet_id)
        #print sub_id_list
        #print len(sub_id_list)
        if len(sub_id_list)==0:
            continue
        try:
            statuses = api.statuses_lookup(
                        sub_id_list,
                        include_entities=True,
                        trim_user=False)
        except RateLimitError:
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "api is down and pause at:",now
            print "i is",i
            time.sleep(15 * 60)
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "restart at:",now
            statuses = api.statuses_lookup(
                        sub_id_list,
                        include_entities=True,
                        trim_user=False)
        except TweepError:
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "reached rate limit and pause at:",now
            print "i is",i
            time.sleep(15 * 60)
            now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            print "restart at:",now
            statuses = api.statuses_lookup(
                        sub_id_list,
                        include_entities=True,
                        trim_user=False)

        for status in statuses:
            results.append(status._json)

        new_record += sub_id_list
        if i%100 == 0:
            dest_file = os.path.join(dest_dir,str(i)+".json")
            with open(dest_file,"w") as f:
                f.write(json.dumps(results))

            with open(record_file,"a") as f:
                for tweet_id in new_record:
                    f.write(tweet_id+"\n")

            results = []
            new_record = []
        








def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id_file")
    parser.add_argument("dest_dir")
    parser.add_argument("auth_file")

    args=parser.parse_args()

    record_file = os.path.join(args.dest_dir,"record")
    tweet_ids = read_tweet_id(args.id_file)
    get_tweets_by_ids(tweet_ids,args.dest_dir,args.auth_file,record_file)
    now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    print "finished at:",now


if __name__=="__main__":
    main()

