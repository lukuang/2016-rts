"""
run wt2g queries queries
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_dir")
    parser.add_argument("result_dir")
    args=parser.parse_args()
    files = os.walk(args.query_dir).next()[2]
    run_args = ["IndriRunQuery","QUERY_FILE"]
    for f in files:
        query_file = os.path.join(args.query_dir,f)
        run_args[1] = query_file
        p = subprocess.Popen(run_args,stdout=PIPE)
        output = p.communicate()[0]

        result_file = re.sub("queries","result",f)
        result_file = os.path.join(args.result_dir,result_file)
        with open(result_file,"w") as of:
            of.write(output)


if __name__=="__main__":
    main()

