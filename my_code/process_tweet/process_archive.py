"""
process tweets fo tweet archive
"""

import os
import json
import sys
import re
import argparse
import codecs
import bz2
from tweet_proc import *

class ArchiveTweet(Tweet):
    pass

class ArchiveTweetProcessor(TweetProcessor):
    def __init__(self,interval,archive_dir,debug=False,start=None,end=None):
        if start is None:
            super(ArchiveTweetProcessor,self).__init__(self,interval)
        else:
            super(ArchiveTweetProcessor,self).__init__(self,interval,start,end)
        self,archive_dir,self.debug = archive_dir,debug
        self.check_day_dir_factory()

    def check_day_dir_factory(self):
        if self.interval == Interval_value.before:
            self.check_day_dir = self.dir_is_before
        elif self.interval == Interval_value.within:
            self.check_day_dir = self.dir_is_within
        elif self.interval == Interval_value.after:
            self.check_day_dir = self.dir_is_after
        else:
            raise KeyError("the interval %s is not supported" %interval)

    def dir_is_before(self,dir_name):

        return( "19">=dir_name)

    def dir_is_within(self,dir_name):
        
        return( "19"<=dir_name<="29")

    def dir_is_after(self,dir_name):
        
        return( dir_name=>"29")

    def process_top_dir(self):
        day_dirs = [    os.path.join(self.archive_dir,x) \
                        for x in os.walk(archive_dir).next()[1] \
                        if self.check_day_dir(x)
                    ]
        day_dirs.sort()
        for day_dir in day_dirs:
            day_dir = os.path.join(self.archive_dir,day_dir)
            self.process_day_dir(day_dir)



    def process_day_dir(self,day_dir):
        tweets = []
        print day_dir
        
        hour_dirs = os.walk(day_dir).next()[1]
        hour_dirs.sort()
        for h_dir in hour_dirs:
            h_dir = os.path.join(day_dir,h_dir)
            self.process_hour_dir(h_dir)
            

        return tweets

    def process_hour_dir(self,h_dir):
        tweets = []

        tweet_files = os.walk(h_dir).next()[2]
        print tweet_files
        tweet_files.sort()
        for tweet_file in tweet_files:
            tweet_file = os.path.join(h_dir,tweet_file)
            tweets += self.process_file(tweet_file)
            if self.debug:
                if len(tweets)!=0:
                    break
        tweets = sorted(tweets,key= lambda x : x.tid)
        self.operation(tweets)

    def process_file(self,tweet_file):
        tweets = []
        with bz2.BZ2File(tweet_file) as f:
            for line in f:
                try:
                    new_tweet = self.process_line(line)
                except KeyError:
                    print "wrong tweet fromat"
                    print "the file is",tweet_file
                    print "the line is",line
                if new_tweet is not None:
                    tweets.append(new_tweet)
        return tweets

    def process_line(self,tweet_string):
        tweet = json.loads(tweet_string)
        if "delete" in tweet:
            return None
        else:
            t_time = int(tweet["timestamp_ms"])
            if self.check_time(t_time):
                tid = tweet["id_str"]
                text = tweet["text"]
                return ArchiveTweet(tid,text)
            else:
                return None   

    @abstractmethod
    def operation(self,):


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()

if __name__=="__main__":
    main()

