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
import time
from tweet_proc import *
from abc import ABCMeta,abstractmethod
from myUtility.misc import DebugStop

class ArchiveTweet(Tweet):
    def __init__(self,tid,text,created_at,timestamp_ms):
        super(ArchiveTweet,self).__init__(tid,text)
        self.created_at,self.timestamp_ms = created_at,timestamp_ms

    @property
    def tweet_indri_text(self):
        """return the indir formatted
        text for a tweet
        """
        extra_fields = ["created_at","timestamp_ms"]
        field_data = {
                        "created_at" : self.created_at,
                        "timestamp_ms" : self.timestamp_ms
                        }
        return gene_single_indri_text(self.tid,self.text)


class ArchiveTweetProcessor(TweetProcessor):
    __metaclass__=ABCMeta

    def __init__(self,interval,archive_dir,debug=False,start=START15,end=END15):

        super(ArchiveTweetProcessor,self).__init__(interval,start,end)
        self.archive_dir,self.debug = archive_dir,debug
        self.check_day_dir_factory()
        self.tweet_buffer = []
        self.day = str(start.struct_time.tm_mday)
        self.hour = str(start.struct_time.tm_hour)

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
        
        return( dir_name>="29")

    def process_top_dir(self):
        day_dirs = [    os.path.join(self.archive_dir,x) \
                        for x in os.walk(self.archive_dir).next()[1] \
                        if self.check_day_dir(x)
                    ]
        day_dirs.sort()
        for day_dir in day_dirs:
            day_dir = os.path.join(self.archive_dir,day_dir)
            self.process_day_dir(day_dir)



    def process_day_dir(self,day_dir):
        
        hour_dirs = os.walk(day_dir).next()[1]
        hour_dirs.sort()
        for h_dir in hour_dirs:
            h_dir = os.path.join(day_dir,h_dir)
            self.process_hour_dir(h_dir)
            


    def process_hour_dir(self,h_dir):

        tweet_files = os.walk(h_dir).next()[2]
        #print tweet_files
        tweet_files.sort()
        for tweet_file in tweet_files:
            tweet_file = os.path.join(h_dir,tweet_file)
            self.process_file(tweet_file)

    def process_file(self,tweet_file):

        with bz2.BZ2File(tweet_file) as f:
            for line in f:
                self.process_line(line)
                # except KeyError:
                #     print "wrong tweet fromat"
                #     print "the file is",tweet_file
                #     print "the line is",line
                # if new_tweet is not None:
                #     tweets.append(new_tweet)

    def process_line(self,tweet_string):
        tweet = json.loads(tweet_string)
        if "delete" not in tweet:
            t_time = int(tweet["timestamp_ms"])
            created_at = tweet["created_at"]
            t_time_sec = t_time/1000
            if self.check_time(t_time):
                tid = tweet["id_str"]
                text = tweet["text"]
                day, hour = self.get_hour_day_from_epoch_time(t_time_sec)
                if day!=self.day or hour!=self.hour:
                    self.operation()
                    self.tweet_buffer
                    self.day = day
                    self.hour = hour
                self.tweet_buffer.append(ArchiveTweet(tid,text,created_at,str(t_time)))  

    @staticmethod
    def get_hour_day_from_epoch_time(t_time_sec):
        struct_time = time.gmtime(t_time_sec)
        return str(struct_time.tm_mday), str(struct_time.tm_hour)

    # @staticmethod
    # def get_hour_day_from_path(h_dir):
    #     head,hour = os.path.split(h_dir)
    #     if len(hour) == 0:
    #         head,hour = os.path.split(head)
    #     head,day = os.path.split(head)

    #     return day,hour

    @abstractmethod
    def operation(self):
        pass


class ArchiveTrecTextBuilder(ArchiveTweetProcessor):
    def __init__(self,interval,archive_dir,dest_dir,debug=False,start=START15,end=END15):
        super(ArchiveTrecTextBuilder,self).__init__(interval,archive_dir,debug,start,end)
        self.dest_dir = dest_dir



    def build(self):
        self.process_top_dir()

    def operation(self):
        if self.tweet_buffer:
            file_name = self.day+"-"+self.hour
            dest_file =os.path.join(self.dest_dir,file_name)
            with codecs.open(dest_file,"a","utf-8") as f:
                for tweet in self.tweet_buffer:
                    single_text = tweet.tweet_indri_text
                    if single_text is None:
                        continue
                    else:
                        f.write(single_text+"\n")
                        if self.debug:
                            raise DebugStop("write to %s" %(dest_file))

        




