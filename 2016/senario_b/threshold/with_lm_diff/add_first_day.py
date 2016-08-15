"""
add first day result of no_lm to the result with_lm
"""

import os
import json
import sys
import re
import argparse
import codecs

def load_first_day_from_no_lm(no_lm_result_file):
    first_day_result = []
    with open(no_lm_result_file) as f:
        for line in f:
            parts = line.split()
            day = parts[0]
            if day == "20160802":
                first_day_result.append(line)

    return first_day_result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("with_lm_result_file")
    parser.add_argument("no_lm_result_file")
    parser.add_argument("dest_file")
    args=parser.parse_args()

    first_day_result = load_first_day_from_no_lm(args.no_lm_result_file)
    result_with_lm = open(args.with_lm_result_file).readlines()
    
    with open(args.dest_file,"w") as f:  
        for line in first_day_result:
            f.write(line)

        for line in result_with_lm:
            f.write(line)

if __name__=="__main__":
    main()

