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

        else:
            self._days = map(str,range(23,32)+range(1,8)) 


    @property
    def days(self):
        return self._days

def check_create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_query_string_dict(src_query_file):
    str_dict = {}
    with open(src_query_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("<number>(.+)</number>",line)
            if m:
                qid = m.group(1).strip()
            else:
                m = re.search("<text>(.+)</text>",line)
                if m:
                    query_string = m.group(1)
                    combine_finder = re.search("#combine\((.+)\)",query_string)
                    if combine_finder:
                        query_string = combine_finder.group(1)
                    all_words = re.findall("[a-zA-z_]+",query_string)
                    all_words.sort()
                    str_dict[ " ".join(all_words) ] = qid
            

    return str_dict

def parse_expanded_query(line):
    expanded_query_str = re.sub("^# expanded:","",line).strip()
    m = re.search("#combine(\([^)]+)\)",expanded_query_str)
    if m:
        expanded_query_str = re.sub("#combine",'',m.group(1))

        all_words = re.findall("[a-zA-z_]+",expanded_query_str)
        all_words.sort()
        original_query_str = " ".join(all_words)
        return original_query_str,expanded_query_str
    else:
        return expanded_query_str,expanded_query_str

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
    parser.add_argument("--fbDocs","-fd",type=int,default=1,
        help="""
            When specified, rm3 feedback method is in use
        """)
    args=parser.parse_args()

    query_str_dict = get_query_string_dict(args.src_query_file)
    args.retrieval_method = RetrievalMethod(args.retrieval_method)
    args.year = Year(args.year)
    individual_index_root = IND_DIR[args.year]

    days = GetDays(args.year).days

    args.dest_dir = os.path.join(args.dest_dir,args.year.name)

    rule = RULE[ args.retrieval_method ]

    result_prefix = os.path.basename(args.src_query_file)
    expansion_dir_name = result_prefix
    expansion_dir_name += "_{}".format(args.retrieval_method.name)
    expansion_dir_name += "_fbDocs:{}".format(args.fbDocs)

    expansion_dir = os.path.join(args.dest_dir,expansion_dir_name)
    check_create_dir(expansion_dir)

    fbDocs = ""
    if args.fbDocs:
        fbDocs = "-fbDocs={}".format(args.fbDocs)

    command_template = Template("IndriRunQuery {} {} -rule={} -index=$index_path -printQuery=true | grep expanded".format(args.src_query_file,
                                                                                                                          fbDocs,
                                                                                                                      rule) )
    for day in days:
        result_file = os.path.join(expansion_dir,day)
        with open(result_file,"w") as of:
            index_path = os.path.join(individual_index_root,day)
            command = command_template.substitute(index_path=index_path)
            print command
            p = subprocess.Popen(command,stdout=subprocess.PIPE,shell=True)
            while True:
                line = p.stdout.readline()
                if line != '':
                    original_query_str,expanded_query_str = parse_expanded_query(line)   
                    qid = query_str_dict[original_query_str]
                    new_line = "%s:%s\n" %(qid,expanded_query_str)
                    of.write(new_line)        
                else:
                    break

if __name__=="__main__":
    main()

