"""
compute clarity for each query file
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def compute_clarity(show_clarity_file,index_dir,original_query_file):
    clarity = {}
    run_command = "%s %s %s" %(show_clarity_file,index_dir,original_query_file)
    #print "command being run:\n%s" %(run_command)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            clarity[qid] = float(parts[1])
            

        else:
            break 
    return clarity

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show_clarity_file","-scf",default="/infolab/headnode2/lukuang/2016-rts/code/my_code/distribution/query_prediction/clarity/show_clarity")
    parser.add_argument("clarity_query_dir")
    parser.add_argument("top_index_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    for day in sorted(os.walk(args.clarity_query_dir).next()[2]):
        day_index_dir = os.path.join(args.top_index_dir,day)
        day_query_file = os.path.join(args.clarity_query_dir,day)
        day_clarity = compute_clarity(args.show_clarity_file,day_index_dir,day_query_file)       
        dest_file = os.path.join(args.dest_dir,day)
        with open(dest_file,"w") as f:
            f.write(json.dumps(day_clarity))



if __name__=="__main__":
    main()

