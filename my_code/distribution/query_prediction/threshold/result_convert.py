"""
convert indri run result to MB result
"""

import os
import json
import sys
import re
import argparse
import codecs


sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import T2Day


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_file")
    parser.add_argument("dest_file")
    parser.add_argument("--tweet2day_file","-tf",default="/infolab/node4/lukuang/2015-RTS/2015-data/tweet2dayepoch.txt")
    args=parser.parse_args()

    t2day = T2Day(args.tweet2day_file)

    with open(args.dest_file,'w') as of:
        with open(args.src_file) as f:
            for line in f:
                parts = line.split()
                qid = parts[0]
                tid = parts[2]
                runtag = parts[5]
                epoch = t2day.get_epoch(tid)
                if not epoch:
                    epoch = '1437349897'
                of.write("%s %s %s %s\n" %(qid,tid,epoch,runtag))




if __name__=="__main__":
    main()

