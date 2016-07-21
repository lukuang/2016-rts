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
sys.path.append("/infolab/node4/lukuang/2015-RTS/src")


from my_code.process_tweet  import CrawledTweet
from my_code.crawler import TweetListener



def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("auth_file")
  parser.add_argument("dest_dir")
  args=parser.parse_args()

  log_dir = os.path.join(args.dest_dir,"log")
  text_dir = os.path.join(args.dest_dir,"text")
  listener = TweetListener(log_dir,text_dir)
  auth_info = json.load(open(args.auth_file))
  consumer_key = auth_info["consumer_key"]
  consumer_secret = auth_info["consumer_secret"]
  access_token = auth_info["access_token"]
  access_token_secret = auth_info["access_token_secret"]


  auth = OAuthHandler(consumer_key,consumer_secret)
  auth.set_access_token(access_token,access_token_secret)

  stream = Stream(auth,listener)
  while True:
    try:
      stream.sample()
    except Exception as ex:
      print str(ex)
      pass

if __name__=="__main__":
    main()

