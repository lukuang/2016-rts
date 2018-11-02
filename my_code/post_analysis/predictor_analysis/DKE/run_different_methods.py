"""
using different methods on RTS data to see whether
we could get better performances
"""

import os
import json
import sys
import re
import argparse
import subprocess
from lxml import etree
from string import Template
from enum import IntEnum, unique

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


sys.path.append("../")
from plot_silentDay_predictor import IND_DIR


@unique
class RetrievalMethod(IntEnum):
    f2exp = 0
    dirichlet = 1
    pivoted = 2
    bm25 = 3
    tfidf = 4

RULE = {
    RetrievalMethod.f2exp:"method:f2exp,s:0.1",
    RetrievalMethod.dirichlet:"method:dirichlet,mu:500",
    RetrievalMethod.pivoted:"method:pivoted,s:0.2",
    RetrievalMethod.bm25:"method:okapi,k1:1.0",
    RetrievalMethod.tfidf:"method:tfidf",
}


class GetDays(object):
    """
    Get days for each RTS year
    """

    def __init__(self,year):
        if year == Year.y2016:
            self._days = map(str,range(2,12))
            

        elif year == Year.y2015:
            self._days = map(str,range(20,30))

        elif year == Year.y2017:

            self._days = map(str,range(29,32)+range(1,6)) 



    @property
    def days(self):
        return self._days

def check_create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_query_file")
    parser.add_argument("dest_dir")
    parser.add_argument("--year","-y",choices=[0,1,3],default=0,type=int,
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
    parser.add_argument("--fbDocs","-fd",type=int,
        help="""
            When specified, rm3 feedback method is in use
        """)
    args=parser.parse_args()


    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    args.year = Year(args.year)
    individual_index_root = IND_DIR[args.year]

    days = GetDays(args.year).days

    args.dest_dir = os.path.join(args.dest_dir,args.year.name)
    check_create_dir(args.dest_dir)

    rule = RULE[ args.retrieval_method ]

    result_prefix = os.path.basename(args.src_query_file)
    result_file_name = result_prefix
    if len(result_file_name)==0:
        result_file_name = args.retrieval_method.name
    else:
        result_file_name += "_{}".format(args.retrieval_method.name)
    if args.fbDocs:
        result_file_name += "_fbDocs:{}".format(args.fbDocs)

    result_file = os.path.join(args.dest_dir,result_file_name)

    fbDocs = ""
    if args.fbDocs:
        fbDocs = "-fbDocs={}".format(args.fbDocs)

    command_template = Template("IndriRunQuery {} {} -rule={} -index=$index_path ".format(args.src_query_file,
                                                                                               fbDocs,
                                                                                               rule) )
    with open(result_file,"w") as of:
        for day in days:
            index_path = os.path.join(individual_index_root,day)
            command = command_template.substitute(index_path=index_path)
            print command
            p = subprocess.Popen(command,stdout=subprocess.PIPE,shell=True)
            while True:
                line = p.stdout.readline()
                if line != '':
                    if args.year == Year.y2015:
                        line_prefix = "201507{} ".format(day.zfill(2))
                    elif args.year == Year.y2016:
                        line_prefix = "201608{} ".format(day.zfill(2))
                    else:
                        if int(day) >= 29: 
                            line_prefix = "201707{} ".format(day.zfill(2))
                        else:
                            line_prefix = "201708{} ".format(day.zfill(2))
                    of.write(line_prefix+line)        
                else:
                    break

if __name__=="__main__":
    main()

