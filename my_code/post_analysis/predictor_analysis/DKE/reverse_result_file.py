"""
reverse the run B result file back to raw indri 
run result files
"""

import os
import json
import sys
import re
import argparse
import codecs


def get_run_info(result_file):
    run_info = {}
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            day = int(parts[0][6:])
            day = str(day)
            qid = parts[1]
            tid = parts[3]
            rank = parts[4]
            score = parts[5]
            run_tag = parts[6]
            if day not in run_info:
                run_info[day] = {}
            if qid not in run_info[day]:
                run_info[day][qid] = []
            new_line = " ".join([qid,"Q0",tid,rank,score,run_tag])
            new_line += "\n"
            run_info[day][qid].append(new_line)
    return run_info

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_file")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    run_name = os.path.basename(args.result_file)
    args.dest_dir = os.path.join(args.dest_dir,run_name)
    if not os.path.exists(args.dest_dir):
        os.makedirs(args.dest_dir)
    run_info = get_run_info(args.result_file)

    for day in run_info:
        dest_file = os.path.join(args.dest_dir,day)
        with open(dest_file,"w") as f:
            for qid in run_info[day]:
                for line in run_info[day][qid]:
                    f.write(line)


if __name__=="__main__":
    main()

