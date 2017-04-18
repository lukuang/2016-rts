"""
process trec text file by eleminating the relevant documents
for selected silent queries
"""

import os
import json
import sys
import re
import argparse
import codecs

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original_trec_text","-rt",default="/infolab/node4/lukuang/2015-RTS/disk4-5/trec/trectext")
    parser.add_argument("dest_file")
    parser.add_argument("silent_query_info_file")
    args=parser.parse_args()

    silent_query_info =  json.load(open(args.silent_query_info_file))
    removed_docids = []

    for qid in silent_query_info:
        removed_docids += silent_query_info[qid]

    single_document = []
    docid= ""
    escape = 0
    written = 0
    print type(removed_docids)
    print len(set(removed_docids))
    with open(args.dest_file,"w") as of:
        with open(args.original_trec_text) as f:
            for line in f:
                single_document.append(line)
                docid_finder = re.search("<DOCNO>\s+(.+?)\s+</DOCNO>",line)
                if docid_finder:
                    docid = unicode(docid_finder.group(1))
                    # print "Find docid %s" %(docid)
                else:
                    doc_end_finder = re.search("</DOC>",line)
                    if doc_end_finder:
                        if docid not in removed_docids:
                            # print "docid not removed"
                            for l in single_document:
                                of.write(l)
                            written += 1
                        else: 
                            # print "escape %s" %(docid)
                            escape += 1
                        single_document = []
                        docid= ""

    print "escaped %d documents" %(escape)
    print "writted %d documents" %(written)



if __name__=="__main__":
    main()

