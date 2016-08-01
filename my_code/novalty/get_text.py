"""
get text for a tweet according to index dir and tid
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def get_text(index_dir,tweet_id):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tweet_id)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    args=parser.parse_args()
    tweet_id = "622918920844906496"
    index_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual/20"
    t = get_text(index_dir,tweet_id)
    print "the text is:\n%s" %t


if __name__=="__main__":
    main()

