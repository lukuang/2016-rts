"""
compare tweet id lists from different list
"""

import os
import json
import sys
import re
import argparse
import codecs
import datetime
import calendar
import time
import bz2 


START = calendar.timegm(datetime.datetime.strptime('July 20, 2015, 00:00:00 UTC'\
            , '%B %d, %Y, %H:%M:%S UTC').timetuple()) * 1000
END = calendar.timegm(datetime.datetime.strptime('July 29, 2015, 23:59:59 UTC'\
            , '%B %d, %Y, %H:%M:%S UTC').timetuple()) * 1000


class Tweet(object):

    def __init__(self,tid,is_delete):
        self.tid,self.is_delete = tid,is_delete 

class TweetProcessor(object):

    def __init__(self,start= START,end= END):
        self.start, self.end = start,end


    def within_period(self,t_time):
        """check whether the tweet is with the
        evaluation period
        """ 
        return (t_time>=self.start and t_time <=self.end)

    def process_day_dir(self,day_dir,only_id = False):
        tweets = []
        print day_dir
        hour_dirs = os.walk(day_dir).next()[1]
        hour_dirs.sort()
        for h_dir in hour_dirs:
            h_dir = os.path.join(day_dir,h_dir)
            tweets += self.process_hour_dir(h_dir)
            #if len(tweets)!=0:
            #    break
        deleted = []
        status = []
        if only_id:
            
            for x in tweets:
                if x.is_delete:
                    deleted.append(x.tid)
                else:
                    status.append(x.tid)
        else:
            for x in tweets:
                if x.is_delete:
                    deleted.append(x)
                else:
                    status.append(x)

        return deleted,status

    def process_hour_dir(self,h_dir):
        tweets = []

        tweet_files = os.walk(h_dir).next()[2]
        print tweet_files
        tweet_files.sort()
        for tweet_file in tweet_files:
            tweet_file = os.path.join(h_dir,tweet_file)
            tweets += self.process_file(tweet_file)
        tweets = sorted(tweets,key= lambda x : x.tid)
        return tweets


    def process_file(self,tweet_file):
        tweets = []
        with bz2.BZ2File(tweet_file) as f:
            for line in f:
                try:
                    new_tweet = self.process_line(line)
                except KeyError:
                    print "the file is",tweet_file
                    print "the line is",line
                if new_tweet is not None:
                    tweets.append(new_tweet)
        return tweets


    def process_line(self,tweet_string):
        tweet = json.loads(tweet_string)
        is_delete = ("delete" in tweet)
        if is_delete:
            #return None
            try:
                t_time = int(tweet["delete"]["timestamp_ms"])
                tid = tweet["delete"]["status"]["id_str"]
            except KeyError:
                print tweet
                sys.exit(-1)
        else:

            t_time = int(tweet["timestamp_ms"])
            tid = tweet["id_str"]
        if len(tid)!=18:
            return None
        #   raise KeyError
        if self.within_period(t_time):

            return Tweet(tid,is_delete)
        else:
            return None


def check_dir(dir_name):
    return( "19"<=dir_name<="29")



def compare(list1,list2):
    with open(list1) as f1, \
            open(list2) as f2:
        l1_line = f1.readline().rstrip()
        l2_line = f2.readline().rstrip()

def get_within_period_dir(tweet_dir):
    tweet_dir = [  os.path.join(tweet_dir,x) \
                   for x in os.walk(tweet_dir).next()[1] \
                   if check_dir(x)
                ]

    tweet_dir.sort()
    return tweet_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    #parser.add_argument("list1")
    #parser.add_argument("list2")
    parser.add_argument("tweet_dir")
    parser.add_argument("status_file")
    parser.add_argument("deleted_file")
    args=parser.parse_args()
    tweet_dir = get_within_period_dir(args.tweet_dir)
    processor = TweetProcessor()
    deleted = []
    status = []
    for day_dir in tweet_dir:
        temp_deleted,temp_status = processor.process_day_dir(day_dir,True)
        #deleted += temp_deleted
        #status += temp_status
        #break
        with open(args.status_file,"a") as f:
            for tid in temp_status:
                f.write(tid+"\n")
        with open(args.deleted_file,"a") as f:
            for tid in temp_deleted:
                f.write(tid+"\n")





if __name__=="__main__":
    main()

