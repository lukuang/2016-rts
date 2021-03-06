"""
generate index para file for  snippets (one index for all queries)
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.misc import gene_indri_index_para_file


def snippet_build_index(trec_text_dir,index_dir,index_para_file):

    file_list = []
    for qid in os.walk(trec_text_dir).next()[2]:
        file_list.append(os.path.join(trec_text_dir,qid))
        
    #index_para_file = os.path.join(index_para_dir,"index_para")
    index_path = index_dir
    gene_indri_index_para_file(file_list,index_para_file,
                index_path,stemmer=None,use_stopper=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trec_text_dir")
    parser.add_argument("index_dir")
    parser.add_argument("index_para_file")

    args=parser.parse_args()

    snippet_build_index(args.trec_text_dir,args.index_dir,
                        args.index_para_file)

    # file_list = []
    # for qid in os.walk(args.trec_text_dir).next()[2]:
    #     file_list.append(os.path.join(args.trec_text_dir,qid))
        
    # index_para_file = os.path.join(args.index_para_dir,"index_para")
    # index_path = args.index_dir
    # gene_indri_index_para_file(file_list,index_para_file,
    #             index_path)

if __name__=="__main__":
    main()

