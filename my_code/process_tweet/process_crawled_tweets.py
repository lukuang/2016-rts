"""
process crawled tweets
"""

import os
import json
import sys
import re
import argparse
import codecs
import time
import string

from myUtility.indri import TextFactory
from tweet_proc import *


def convert_epoch_to_indri_date(epoch_string):

    struct = time.gmtime(epoch_string)
    time_string = "%s/%s/%d" %(string.zfill(str(struct.tm_mon),2),string.zfill(str(struct.tm_mday),2),struct.tm_year)
    return time_string



class CrawledTweet(Tweet):
    """Struct for storing information of a single tweet
    for crawled tweet. Fields it contains are:
        id,
        text,
        created_at,
        timestamp_ms
    """
    def __init__(self,tweet_data):
        if "delete" in tweet_data:
            self = None
        if "retweeted_status" in tweet_data:
            created_at = tweet_data["created_at"]
            timestamp_ms = tweet_data["timestamp_ms"]
            tweet_data = tweet_data["retweeted_status"]
            tweet_data["timestamp_ms"] = timestamp_ms
            tweet_data["created_at"] = created_at
            
        timestamp_ms = tweet_data["timestamp_ms"]
        created_at = tweet_data["created_at"]
        tid = tweet_data["id_str"]
        text = tweet_data["text"]
        timestamp_s = float(timestamp_ms)/1000
        date_string = convert_epoch_to_indri_date(timestamp_s)
        super(CrawledTweet,self).__init__(tid,text)
        self._created_at,self._timestamp_ms, self._date_stirng = \
            created_at,timestamp_ms,date_string
        self._add_extra_field()

    def _add_extra_field(self):
        """get extra field from the crawled tweet
        """
        self.extra_fields = ["created_at","timestamp_ms","date"]
        self.field_data = {
                        "created_at" : self._created_at,
                        "timestamp_ms" : self._timestamp_ms,
                        "date" : self._date_stirng
                        }
    
    



class CrawledTweetTrecTextFactory(TextFactory):
    """Build trect text for crawled tweets
    """
    def __init__(self,source_file,dest_dir,debug=False):
        dest_file_path = self._get_dest_file_path(source_file,dest_dir)
        
        super(CrawledTweetTrecTextFactory,self).__init__(dest_file_path)

        self._source_file,self.debug = source_file,debug


    def _get_dest_file_path(self,source_file,dest_dir):
        file_name = os.path.basename(source_file)
        m =  re.search("status\.log\.(\d+)\-(\d+)_(\d+)\-(\d+)",file_name)
        if m is not None:
            year = m.group(1)
            month = m.group(2)
            day = m.group(3)
            hour = m.group(4)
            file_name = "%s-%s-%s_%s" %(year,month,day,hour)
        else:
            raise RuntimeError("file name %s wrong!" %(file_name))
        dest_file_path = os.path.join(dest_dir,file_name)
        return dest_file_path


    def write(self):
        self._process_file()
        super(CrawledTweetTrecTextFactory,self).write()


    def _process_file(self):
        with codecs.open(self._source_file,"r","utf-8") as f:
            for line in f:
                line = line.rstrip()
                if len(line)!=0:
                    self._process_line(line)


    def _process_line(self,line):
        tweet_data = json.loads(line)
        if "delete" not in tweet_data:
            tweet = CrawledTweet(tweet_data)
            # print tweet.field_data
            # print tweet.tid
            # print tweet.text
            self.add_document(tweet.tid,tweet.text,
                              tweet.extra_fields,
                              tweet.field_data)
        


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()

if __name__=="__main__":
    main()

