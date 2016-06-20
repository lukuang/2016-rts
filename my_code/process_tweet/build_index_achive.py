"""
build index for archive tweets
"""

import os
import json
import sys
import re
import argparse
import codecs
from process_archive import ArchiveTweet, ArchiveTrecTextBuilder
from myUtility.misc import DebugStop
from tweet_proc import TTime

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    #parser.add_argument("list1")
    #parser.add_argument("list2")
    parser.add_argument("--archive_dir","-ad",default="/lustre/scratch/lukuang/2015-RTS/2015_RTS/2015-data/collection/web-data/raw")
    parser.add_argument("dest_dir")
    parser.add_argument("--interval","-i",type=int,choices=range(3),
        help="""Choose between the intervals wrt the evaluation period:
                0: before,
                1: within,
                2: after
            """)
    parser.add_argument("--debug","-de",action="store_true")
    args=parser.parse_args()

    t_intervals = [
                    Interval_value.before,
                    Interval_value.within,
                    Interval_value.after
        ]

    time_interval = time_interval[args.interval]
    text_builder = ArchiveTrecTextBuilder(t_intervals,
                            args.archive_dir,args.dest_dir,
                            debug=args.debug
                            )
    
    try:
        text_builder.build()
    except DebugStop as e:
        print e

if __name__=="__main__":
    main()

