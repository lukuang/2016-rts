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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snippets_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    for qid in os.walk(args.snippets_dir).next()[1]:
        qid_dir = os.path.join(args.snippets_dir,qid)
        dest_file = os.path.join(args.dest_dir,qid)
        query_snippet_writer = TextFactory(dest_file)
        for json_file in os.walk(qid_dir).next()[2]:
        
            snippets = json.load(open(os.path.join(qid_dir,json_file)))
            for snippet in snippets:
                docid = snippet["id"]
                doc_text = snippet["snippets"]
                query_snippet_writer.add_document(docid,doc_text)

        query_snippet_writer.write()


if __name__=="__main__":
    main()

