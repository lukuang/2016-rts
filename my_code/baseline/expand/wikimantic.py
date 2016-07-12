"""
code for expansion using wikimantic
"""

import os
import json
import sys
import re
import argparse
import codecs
sys.path.append("../../")

from process_query import read_query_file





def generate_input(queries,dest_file):
    with codecs.open(dest_file,"w","utf-8") as f:
        for qid in queries:
            words = re.findall("\w+",queries[qid].lower())
            size = len(words)
            for i in range(size):
                for j in range(i,size):
                    pid = "".join(map(str,range(i,j+1)))
                    phrase = " ".join(words[i:j+1])
                    #print "%s:%s" %(pid,phrase)
                    f.write("%s:%s:%s\n" %(qid,pid,phrase))





def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_query_file")
    parser.add_argument("query_type",choices=["2015_mb","json_mb","wt2g"])
    parser.add_argument("query_field",choices=["title","desc","combine"])
    parser.add_argument("dest_file")
    args=parser.parse_args()

    queries = read_query_file(args.original_query_file,args.query_type,args.query_field)
    generate_input(queries,args.dest_file)

if __name__=="__main__":
    main()

