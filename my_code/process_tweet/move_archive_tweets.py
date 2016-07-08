"""
move and reoganize tweets of archive for simulating result generation for 2016 RTS
"""

import os
import json
import sys
import re
import argparse
import codecs
from process_archive import ArchiveReorganizaer
from myUtility.misc import DebugStop
from tweet_proc import Interval_value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    #parser.add_argument("list1")
    #parser.add_argument("list2")
    parser.add_argument("--archive_dir","-ad",default="/lustre/scratch/lukuang/2016-RTS/2015-data/collection/web-data/raw")
    parser.add_argument("dest_dir")
    parser.add_argument("num_of_run",type=int)
    parser.add_argument("run_id",type=int)
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

    time_interval = t_intervals[args.interval]
    achive_reorganizer = ArchiveReorganizaer(time_interval,
                            args.archive_dir,args.dest_dir,
                            debug=args.debug
                            )

    try:
        achive_reorganizer.build(args.num_of_run,args.run_id)
    except DebugStop as e:
        print e
    print "finished!"

if __name__=="__main__":
    main()

