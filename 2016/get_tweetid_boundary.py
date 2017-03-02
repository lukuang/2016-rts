"""
generate tweet boundary for each day
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess 

def get_tweet_id(output):
    for line in output.split("\n"):
        tweetid_finder = re.search("<DOCNO>(\d+)",line)
        if tweetid_finder:
            return tweetid_finder.group(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw_tweet_dir","-rd",default="/infolab/headnode2/lukuang/2016-rts/data/raw/first/reparsed_text/")
    parser.add_argument("dest_file")
    args=parser.parse_args()

    boundary = {}
    for day_file_name in os.walk(args.raw_tweet_dir).next()[2]:
        m = re.search("08-(\d+)",day_file_name)
        if m:
            day = m.group(1)
            boundary[day] = {
                "start":"",
                "end":""
            }
            day_file = os.path.join(args.raw_tweet_dir,day_file_name)
            p1 = subprocess.Popen(["head","-10",day_file], stdout=subprocess.PIPE)
            head_output = p1.communicate()[0]
            boundary[day]["start"] = get_tweet_id(head_output)

            p2 = subprocess.Popen(["tail","-10",day_file], stdout=subprocess.PIPE)
            tail_output = p2.communicate()[0]
            boundary[day]["end"] = get_tweet_id(tail_output)

    with open(args.dest_file,"w") as f:
        f.write(json.dumps(boundary))


if __name__=="__main__":
    main()

