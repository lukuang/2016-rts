"""
convert indri query to 'qid: text' format
"""

import os
import json
import sys
import re
import argparse
import codecs


def get_judged_qid(qrel_file):
    judged_qids = []
    with open(qrel_file) as f:
        for line in f:
            parts= line.rstrip().split()
            qid = parts[0]
            if qid not in judged_qids:
                judged_qids.append(qid)
    return judged_qids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_file")
    parser.add_argument("dest_file")
    parser.add_argument("--qrel_file","-qf",
        default="/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt")
    parser.add_argument("--with_weight",'-w',action='store_true')
    args=parser.parse_args()


    judged_qids = get_judged_qid(args.qrel_file)

    queries = {}
    
    with open(args.source_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("<number>(MB\d+)</number>",line)
            if m:
                qid = m.group(1)
            m2 = re.search("<text>(.+?)</text>",line)
            if m2:
                query_string = m2.group(1)
                
                if args.with_weight:
                    query_model = {}
                    m3 = re.search("\#combine\((.+?)\)",line)
                    if m3:
                        query_string = m3.group(1)
                        print query_string
                        words = re.findall("\w+",query_string)
                        for w in words:
                            query_model[w] = 1
                    else:
                        m3 = re.search("\#weight\((.+?)\)",line)
                        if m3:
                            query_string = m3.group(1)
                            weight_word_pair = re.compile("^\s*?([0-9\.]+)\s+(\w+)")
                            m4 = weight_word_pair.search(query_string)
                            while m4:
                                weight = float(m4.group(1))
                                word = m4.group(2)
                                query_model[word] = weight
                                query_string = weight_word_pair.sub("",query_string,count=1)
                                m4 = weight_word_pair.search(query_string)
                        else:
                            words = re.findall("\w+",query_string)
                            size = len(words)
                            for w in words:
                                query_model[w] = 1


                    if qid in judged_qids:
                        queries[qid] = query_model 
                        print sum(queries[qid].values())  
                        #print query_model

                else:
                
                    m3 = re.search("\#combine\((.+?)\)",line)
                    if m3:
                        query_string = m3.group(1)
                    m3 = re.search("\#weight\((.+?)\)",line)
                    if m3:
                        query_string = m3.group(1)
                        query_string = re.sub("[^a-zA-z\_\s]","",query_string)
                    query_string = re.sub("\s+"," ",query_string)
                    query_string = query_string.strip()
                    if qid in judged_qids:
                        queries[qid] = query_string
                        

    with open(args.dest_file, 'w') as f:
        for qid in queries:
            if args.with_weight:
                f.write("%s:" %(qid))
                for w in queries[qid]:
                    f.write("%s,%f;"%(w,queries[qid][w]))
                f.write("\n")
            else:
                f.write("%s:%s\n" %(qid, queries[qid]))



if __name__=="__main__":
    main()

