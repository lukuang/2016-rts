"""
crawl data
"""

import os
import json
import sys
import re
import argparse
import codecs
from tweepy import OAuthHandler
from tweepy import Stream
from datetime import datetime
from threading import Timer

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")


from my_code.process_tweet  import CrawledTweet
from my_code.crawler import TweetListener


def run_at_even_hour(auth_file,dest_dir):
  """
  run at the next even hour
  to handle the starting time of running 
  code is not at even hour
  """ 
  x=datetime.today()
  y=x.replace(day=x.day+1, hour=x.hour+1, minute=1, second=0, microsecond=0)
  delta_t=y-x
  secs = delta_t.seconds+1
  print "now is %s" %(datetime.utcnow())
  print "need to wait %f secs" %(secs)
  t = Timer(secs, run_crawler,[auth_file,dest_dir])
  t.start()


def run_crawler(auth_file,dest_dir):
  log_dir = os.path.join(dest_dir,"log")
  text_dir = os.path.join(dest_dir,"text")
  listener = TweetListener(log_dir,text_dir)
  auth_info = json.load(open(auth_file))
  consumer_key = auth_info["consumer_key"]
  consumer_secret = auth_info["consumer_secret"]
  access_token = auth_info["access_token"]
  access_token_secret = auth_info["access_token_secret"]

  auth = OAuthHandler(consumer_key,consumer_secret)
  auth.set_access_token(access_token,access_token_secret)
  stream = Stream(auth,listener)
  print "run at %s" %(datetime.utcnow())
  while True:
    try:
      stream.sample()
    except Exception as ex:
      print str(ex)
      pass

def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("auth_file")
  parser.add_argument("dest_dir")
  args=parser.parse_args()

  # log_dir = os.path.join(args.dest_dir,"log")
  # text_dir = os.path.join(args.dest_dir,"text")
  # listener = TweetListener(log_dir,text_dir)
  # auth_info = json.load(open(args.auth_file))
  # consumer_key = auth_info["consumer_key"]
  # consumer_secret = auth_info["consumer_secret"]
  # access_token = auth_info["access_token"]
  # access_token_secret = auth_info["access_token_secret"]


  # auth = OAuthHandler(consumer_key,consumer_secret)
  # auth.set_access_token(access_token,access_token_secret)

  run_at_even_hour(args.auth_file,args.dest_dir)
  

if __name__=="__main__":
    main()

