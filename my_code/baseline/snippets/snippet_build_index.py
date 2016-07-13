"""
generate index para file for each query
"""

import os
import json
import sys
import re
import argparse
import codecs

from myUtility.misc import gene_indri_index_para_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trec_text_dir")
    parser.add_argument("index_dir")
    parser.add_argument("index_para_dir")

    args=parser.parse_args()

    for qid in os.walk(args.trec_text_dir).next()[2]:
        file_list = [os.path.join(args.trec_text_dir,qid)]
        index_para_file = os.path.join(args.index_para_dir,qid)
        index_path = os.path.join(args.index_dir,qid)
        gene_indri_index_para_file(file_list,index_para_file,
                    index_path)

if __name__=="__main__":
    main()

