"""
get text for all tweets
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


FULL_IND_DIR = {
    Year.y2015:"/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29",
    Year.y2016:"/infolab/headnode2/lukuang/2016-rts/data/incremental_index"
}


def get_text(index_dir,tid):
    run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
            %(index_dir,index_dir,tid)

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    content = p.communicate()[0]
    m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)
    if m is not None:
        return m.group(1)
    else:
        return None

def get_text_for_all(year,src_result_dir,all_text):
    src_file = os.path.join(src_result_dir,year.name)
    year_index_dir = FULL_IND_DIR[year]
    with open(src_file) as f:
        for line in f:
            parts = line.split()
            tid = parts[3]
            t_text = get_text(year_index_dir,tid)
            all_text[tid] = t_text



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_result_dir")
    parser.add_argument("text_dest_file")
    args=parser.parse_args()

    all_text = {}
    print "Get text for 2015"
    get_text_for_all(Year.y2015,args.src_result_dir,all_text)

    print "Get text for 2016"
    get_text_for_all(Year.y2016,args.src_result_dir,all_text)

    with codecs.open(args.text_dest_file,"w",'utf-8') as f:
        f.write(json.dumps(all_text)+"\n")

if __name__=="__main__":
    main()

