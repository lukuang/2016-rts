"""
run 2015 queries
"""

import os
import json
import sys
import re
import subprocess
import argparse
import codecs

def run_query(query_file,result_file,debug):
    run_args = ["IndriRunQuery",query_file]
    if debug:
        print "-"*20
        print run_args
        print result_file
        print "-"*20
    else:
        p = subprocess.Popen(run_args,stdout=subprocess.PIPE)
        output = p.communicate()[0]
        with open(result_file,"w") as of:
                of.write(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("top_result_dir")
    parser.add_argument("top_query_para_dir")
    parser.add_argument("--debug","-de",action="store_true")
    
    
    args=parser.parse_args()
    index_methods = ["individual","incremental"]

    expansion_methods = [
        "original",
        "snippet",
        "wiki",
        "pseudo"
    ]

    not_implemented = ["snippet","wiki"]

    

    for date in dates:
        date = str(date)
        for index_method in index_methods:
            for expansion_method in expansion_methods:
                if expansion_method not in not_implemented:
                    sub_query_dir = os.path.join(
                                        args.top_query_para_dir,
                                        index_method,
                                        expansion_method,
                                    )
                    sub_result_dir = os.path.join(
                                        args.top_result_dir,
                                        index_method,
                                        expansion_method,
                                    )
                    file_names =  os.walk(sub_query_dir).next()[2]]
                    for file_name in file_names:

                        query_file = os.path.join(sub_query_dir,file_name)
                        result_file = os.path.join(sub_result_dir,file_name)
                        run_query(query_file,result_file,args.debug)


if __name__=="__main__":
    main()

