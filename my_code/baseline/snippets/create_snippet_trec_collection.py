"""
create collection from snippet result for each query
"""

import os
import json
import sys
import re
import argparse
import codecs
from myUtility.indri import TextFactory

def create_snippet_single_trec_file(snippets_dir,dest_dir,qid):

    qid_dir = os.path.join(snippets_dir,qid)
    dest_file = os.path.join(dest_dir,qid)
    query_snippet_writer = TextFactory(dest_file)
    for json_file in os.walk(qid_dir).next()[2]:
    
        snippets = json.load(open(os.path.join(qid_dir,json_file)))
        for snippet in snippets:
            docid = snippet["id"]
            doc_text = snippet["snippets"]
            query_snippet_writer.add_document(docid,doc_text)

    query_snippet_writer.write()


def create_snippet_trec_collection(snippets_dir,dest_dir):
    for qid in os.walk(snippets_dir).next()[1]:
        create_snippet_single_trec_file(snippets_dir,dest_dir,qid)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snippets_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    create_snippet_trec_collection(args.snippets_dir,args.dest_dir)
    
    # for qid in os.walk(args.snippets_dir).next()[1]:
    #     qid_dir = os.path.join(args.snippets_dir,qid)
    #     dest_file = os.path.join(args.dest_dir,qid)
    #     query_snippet_writer = TextFactory(dest_file)
    #     for json_file in os.walk(qid_dir).next()[2]:
        
    #         snippets = json.load(open(os.path.join(qid_dir,json_file)))
    #         for snippet in snippets:
    #             docid = snippet["id"]
    #             doc_text = snippet["snippets"]
    #             query_snippet_writer.add_document(docid,doc_text)

    #     query_snippet_writer.write()


if __name__=="__main__":
    main()

