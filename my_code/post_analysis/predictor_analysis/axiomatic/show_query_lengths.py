"""
show the number of queries of each query length
"""

import os
import json
import sys
import re
import argparse
import codecs
from nltk import corpus

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


Q_DIR = {
    Year.y2015:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/clarity_queries",
    Year.y2016:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/clarity_queries",
    Year.y2011:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/clarity_queries"
}


class TextWordsConverter(object):
    def __init__(self):
        self._stopwords = corpus.stopwords.words('english')

    def convert_text_to_words(self,text):
        words = [w for w in re.findall("\w+",text.lower()) if w not in self._stopwords]
        return words


def get_judged_qids(year):
    qids = set()
    if year == Year.y2015:
        eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
        qrel_file = os.path.join(eval_dir,"new_qrels.txt")
 
    elif year == Year.y2016:
        eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
        qrel_file = os.path.join(eval_dir,"qrels.txt")

    elif year == Year.y2011:
        eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
        qrel_file = os.path.join(eval_dir,"new_qrels")

    else:
        raise NotImplementedError("Year %s is not implemented!" %(year.name))

    with open(qrel_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            if qid not in qids:
                qids.add(qid)
    return qids

def get_query_length_counts(qids,year,converter):
    query_dir = Q_DIR[year]
    query_file = os.walk(query_dir).next()[2][0]
    query_file = os.path.join(query_dir,query_file)
    length_counts = {}
    with open(query_file) as f:
        print "open query file:\n%s" %(query_file)
        for line in f:
            line = line.rstrip()
            m = re.search("^(\w+):(.+)$",line)
            if m:
                qid = m.group(1)
                if qid not in qids:
                    continue
                else:
                    words = converter.convert_text_to_words(m.group(2))
                    length = len(words)
                    if length not in length_counts:
                        length_counts[length] = 0
                    length_counts[length] += 1
    return length_counts



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    args=parser.parse_args()


    converter = TextWordsConverter()

    for year in Year:
        print "process year %s" %(year.name)
        qids = get_judged_qids(year)
        length_counts = get_query_length_counts(qids,year,converter)
        for length in sorted(length_counts.keys()):
            print "\tThere are %d queries for length %d" %(length_counts[length],length)


if __name__=="__main__":
    main()

