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

def run_query(runquery_script,query_file,result_file,debug):
    run_args = [runquery_script,query_file]
    if debug:
        print "-"*20
        print run_args
        print result_file
        print "-"*20
    else:
        p = subprocess.Popen(run_args,stdout=subprocess.PIPE)
        output = p.communicate()[0]
        with open(result_file,"a") as of:
                of.write(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir")
    parser.add_argument("query_para_dir")
    parser.add_argument("--runquery_script","-rq",default="IndriRunQuery")
    parser.add_argument("--debug","-de",action="store_true")
    
    
    args=parser.parse_args()
    # index_methods = ["individual","incremental"]

    # expansion_methods = [
    #     "original",
    #     "snippet",
    #     "wiki",
    #     "pseudo"
    # ]

    # not_implemented = ["snippet","wiki"]

    


    # for index_method in index_methods:
    #     for expansion_method in expansion_methods:
    #         if expansion_method not in not_implemented:
    #             sub_query_dir = os.path.join(
    #                                 args.top_query_para_dir,
    #                                 index_method,
    #                                 expansion_method,
    #                             )
    #             sub_result_dir = os.path.join(
    #                                 args.top_result_dir,
    #                                 index_method,
    #                                 expansion_method,
    #                             )
    file_names =  os.walk(args.query_para_dir).next()[2]
    done_results = [
                    os.path.join(args.result_dir,f) for f in
                    os.walk(args.result_dir).next()[2]
                    ]
    

    for file_name in file_names:

        query_file = os.path.join(args.query_para_dir,file_name)
        #result_file = os.path.join(sub_result_dir,file_name)
        m = re.search("^(\d+)_(.+)$",file_name)
        result_file = os.path.join(args.result_dir,m.group(2))
        if result_file in done_results:
            continue
        if m is not None:   
            print "run query %s" %query_file
            run_query(args.runquery_script,query_file,result_file,args.debug)
        else:
            print "Wrong file name %s" %file_name

    print "files skipped:"
    print done_results


if __name__=="__main__":
    main()

