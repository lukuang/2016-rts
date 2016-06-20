"""
TweetProcessor class
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
from abc import ABCMeta,abstractmethod
from myUtility.misc import gene_single_indri_text
from collections import namedtuple

IntervalFactory = namedtuple('IntervalFactory', ['before', 'within','after'])
Interval_value = IntervalFactory._make(["before","within","after"])





def TTime(object):
    def __init__(self,time_string):
        self.time_string = time_string
        self.struct_time = datetime.datetime.strptime(time_string\
            , '%B %d, %Y, %H:%M:%S UTC').timetuple()
        self.epoch = calendar.timegm(struct_time)
        self.epoch_ms = self.epoch*1000




START15 = TTime('July 20, 2015, 00:00:00 UTC')
END15 = TTime('July 29, 2015, 23:59:59 UTC') 



class Tweet(object):
    __metaclass__ = ABCMeta

    def __init__(self,tid,text):
        self.tid,self.text = tid,text


    def __repr__(self):
        """return a dictionary representation
        of the data
        """
        data = {
            "id":self.tid,
            "text":self.text
        }

        return data

    @property
    def tweet_indri_text(self):
        """return the indir formatted
        text for a tweet
        """
        return gene_single_indri_text(self.tid,self.text)





class TweetProcessor(object):
    __metaclass__=ABCMeta
    def __init__(self,interval,start= START15,end= END15):
        self.start, self.end, self.interval =\
                start,end,interval
        self.check_time_factory()

    def before_period(self,t_time):
        return t_time<self.start.epoch_ms

    def within_period(self,t_time):
        """check whether the tweet is with the
        evaluation period
        """ 
        return (t_time>=self.start.epoch_ms and t_time <=self.end.epoch_ms)

    def after_period(self,t_time):
        return t_time>self.end.epoch_ms

    def check_time_factory(self):
        if self.interval==Interval_value.before:
            self.check_time = self.before_period
        elif self.interval==Interval_value.within:
            self.check_time = self.within_period
        elif self.interval==Interval_value.after:
            self.check_time = self.after_period
        else:
            raise KeyError("not support the interval %s" %self.interval)


    @abstractmethod
    def process_file(self,tweet_file):
        pass

    @abstractmethod
    def process_line(self,tweet_string):
        tweet = json.loads(tweet_string)
        is_delete = ("delete" in tweet)

__all__=[
        "TweetProcessor",
        "Tweet",
        "TTime",
        "Interval_value",
        "START15",
        "END15"
    ]




