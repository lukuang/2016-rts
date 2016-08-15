"""
compute the differences between clarity for different queries
"""

import os
import json
import sys
import re
import argparse
import codecs


def get_clarity(clarity_dir):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in date_clarity:
            if qid not in clarities:
                clarities[qid] = {}

            clarities[qid][date] = date_clarity[qid]
    print clarities.keys()
    return clarities


def compute_clarity_diff(clarities):
    clarity_diff = {}
    for qid in clarities:
        if qid not in clarity_diff:
            clarity_diff[qid] = {} 
        days = clarities[qid].keys()
        days.sort()
        for day in days:
            previous_day = str(int(day)-1)
            if previous_day not in clarities[qid]:
                continue
            else:
                clarity_diff[qid][day] = clarities[qid][day] - clarities[qid][previous_day]
    return clarity_diff




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clarity_dir")
    parser.add_argument("dest_file")
    args = parser.parse_args()

    clarities = get_clarity(args.clarity_dir)
    clarity_diff = compute_clarity_diff(clarities)

    with open(args.dest_file,"w") as f:
        f.write(json.dumps(clarity_diff))

if __name__=="__main__":
    main()

