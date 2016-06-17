"""
create trec format text collection for tweets
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    #parser.add_argument("list1")
    #parser.add_argument("list2")
    parser.add_argument("tweet_dir")
    parser.add_argument("--interval","-i",type=int,choices=range(3),
        help="""Choose between the intervals wrt the evaluation period:
                0: before,
                1: within,
                2: after
            """)
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    t_intervals = [
                    Interval_value.before,
                    Interval_value.within,
                    Interval_value.after
        ]
    time_interval = time_interval[args.interval]

    tweet_dir = get_within_period_dir(args.tweet_dir)
    processor = TweetProcessor()
    deleted = []
    status = []

if __name__=="__main__":
    main()