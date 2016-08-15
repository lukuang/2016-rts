"""
change run id for result file
"""

import os
import json
import sys
import re
import argparse
import codecs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file")
    parser.add_argument("dest_file")
    parser.add_argument("run_id")
    args=parser.parse_args()


    with open(args.dest_file,"w") as of:
        with open(args.source_file) as f:
            for line in f:
                parts = line.split()
                parts[6] = args.run_id
                of.write(" ".join(parts)+"\n")

if __name__=="__main__":
    main()

