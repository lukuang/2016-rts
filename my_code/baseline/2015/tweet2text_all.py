"""
convert all crawled tweets to indri text
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.misc import split_list

sys.path.append("/home/1546/code/2016-rts/my_code")
from process_tweet import CrawledTweetTrecTextFactory,CrawledTweet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("dest_dir")
    parser.add_argument("num_of_run",type=int)
    parser.add_argument("run_id",type=int)
    args=parser.parse_args()

    all_files = [os.path.join(args.source_dir,f) for f in os.walk(args.source_dir).next()[2] ]

    sub_list = split_list(all_files,args.num_of_run,args.run_id)
    for tweet_file in sub_list:
        text_writer = CrawledTweetTrecTextFactory(tweet_file,args.dest_dir)
        text_writer.write()

    print "finished"



if __name__=="__main__":
    main()

