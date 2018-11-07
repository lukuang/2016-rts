"""
create query files for computing clarity
"""

import os
import json
import sys
import re
import argparse
import codecs

def get_query_words_by_day(query_dir,eval_topics):
    """get query words from the axiomatic expansion
    output and return the map as:
    {day: {qid: word_string}}
    """
    query_words = {}
    qid_finder = re.compile("<number>([^<]+?)<")
    query_words_finder1 = re.compile("<text>(#weight\(.+?\))</text>")
    query_words_finder2 = re.compile("<text>(.+?)</text>")
    for day in os.walk(query_dir).next()[2]:
        query_file = os.path.join(query_dir,day)
        query_words[day] = {}
        with open(query_file) as f:
            for line in f:
                if qid_finder.search(line):
                    m = qid_finder.search(line)
                    qid = m.group(1)
                    if qid.find("MB") == -1:
                        qid = "MB"+qid
                    line = "<number>%s</number>\n" %qid
                    #skip queries that are not evaluated
                    if qid not in eval_topics:
                        continue
                    elif qid not in query_words[day]:
                        query_words[day][qid] = ""
                    
                elif query_words_finder1.search(line):
                    #skip queries that are not evaluated
                    if qid not in eval_topics:
                        continue
                    m = query_words_finder1.search(line)
                    query_word_string = m.group(1)
                    # all_words = re.findall("(?<=\s)[a-zA-z]+(?=\s)",query_word_string)
                    # query_words[day][qid] = " ".join(all_words)
                    query_words[day][qid] = query_word_string
                    # if qid == "MB348" and day == "21":
                    #     print query_words[qid][day]
                    #     print len(query_words[qid][day])
                elif query_words_finder2.search(line):
                    #skip queries that are not evaluated
                    if qid not in eval_topics:
                        continue
                    m = query_words_finder2.search(line)
                    query_word_string = m.group(1)
                    all_words = re.findall("\w+",query_word_string)
                    query_words[day][qid] = " ".join(all_words)


    return query_words 


def output_clarity_queries(query_words,dest_dir):
    for day in  query_words:
        dest_file = os.path.join(dest_dir,day)
        with open(dest_file,"w") as f:
            for qid in query_words[day]:
                f.write("%s:%s\n" %(qid,query_words[day][qid]))

def read_qrel_file(qrel_file):
    eval_topics = set()
    with open(qrel_file) as f:
        for line in f:
            parts = line.split()
            eval_topics.add(parts[0])
    return eval_topics

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qrel_file")
    parser.add_argument("query_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    eval_topics = read_qrel_file(args.qrel_file)
    query_words = get_query_words_by_day(args.query_dir,eval_topics)
    
    output_clarity_queries(query_words,args.dest_dir)


if __name__=="__main__":
    main()

