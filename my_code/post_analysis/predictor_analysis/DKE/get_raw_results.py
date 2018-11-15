"""
get raw retrieval results
"""

import os
import json
import sys
import re
import argparse
import codecs
from string import Template
import subprocess

from run_different_methods import RetrievalMethod,RULE,GetDays,check_create_dir

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


sys.path.append("../")
from plot_silentDay_predictor import IND_DIR

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_query_file")
    parser.add_argument("dest_dir")
    parser.add_argument("--year","-y",choices=[0,1,2,3],default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
                3:2017
        """)
    parser.add_argument("--retrieval_method","-rm",choices=list(map(int, RetrievalMethod)),default=0,type=int,
        help="""
            Choose the retrieval method:
                0:f2exp
                1:dirichlet
                2:pivoted
                3:bm25
                4:tfidf
        """)
    args=parser.parse_args()


    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    args.year = Year(args.year)
    individual_index_root = IND_DIR[args.year]
    rule = RULE[ args.retrieval_method ]

    days = GetDays(args.year).days

    args.dest_dir = os.path.join(args.dest_dir,args.retrieval_method.name )
    check_create_dir(args.dest_dir)

    command_template = Template("IndriRunQuery {} -rule={} -index={}/$day > $dest_file ".format(args.src_query_file,
                                                                                             rule,
                                                                                             individual_index_root) )
    for day in days:
        dest_file = os.path.join(args.dest_dir,day)
        if os.path.exists(dest_file):
            continue
        command = command_template.substitute(day=day,
                                              dest_file=dest_file)
        subprocess.call(command,shell=True)



if __name__=="__main__":
    main()

