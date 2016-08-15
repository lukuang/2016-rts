"""
find day for tweetid
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def get_date(index_dir,tweet_id):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tweet_id)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<date>\d+\/(\d+)\/.+?</date>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all_index_dir","-ar",default="/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29")
    args=parser.parse_args()

if __name__=="__main__":
    main()

