"""
Create link files for the queries
"""

import os
import json
import sys
import re
import argparse
import codecs
from nltk.parse.stanford import StanfordDependencyParser

def read_query_file(query_file):
    day_queries = {}
    with open(query_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("^(.+?):(.+?)$",line)
            if m:
                qid = m.group(1)
                query_text = m.group(2)
                day_queries[qid] = query_text
            else:
                message = "File %s is mal formated!\n" %(query_file)
                message += "Wrong line:\n%s\n" %(line)
                raise RuntimeError(message)
    return day_queries


def get_queries(query_dir):
    queries = {}
    for day in os.walk(query_dir).next()[2]:
        query_file = os.path.join(query_dir,day)
        day_queries = read_query_file(query_file)
        queries[day] = day_queries
    return queries

def procss_unit(text_unit):
    return re.sub("[^\w]+","",text_unit)

def get_links(queries):
    os.environ['CLASSPATH']="/infolab/node4/lukuang/Stanford/stanford-parser-full-2016-10-31/stanford-parser.jar:"
    os.environ['CLASSPATH'] += "/infolab/node4/lukuang/Stanford/stanford-parser-full-2016-10-31/stanford-parser-3.7.0-models.jar"
    parser=StanfordDependencyParser(model_path="edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz")
    
    links = {}

    for day in queries:
        links[day] = {}
        print "Process day %s" %(day)
        for qid in queries[day]:
            print "\tProcess query %s" %(qid)
            query_text = queries[day][qid]
            # print query_text
            triples = [list(parse.triples()) for parse in parser.raw_parse(query_text)][0]
            # print triples
            query_links = []
            for t in triples:
                a_link = "%s %s" %(procss_unit(t[0][0]),procss_unit(t[2][0]))
                query_links.append(a_link)
                # print "add link %s to query %s" %(a_link,qid)
            links[day][qid] = query_links
    return links

def write_links(links,dest_dir):
    for day in links:
        dest_file = os.path.join(dest_dir,day)
        with open(dest_file,"w") as f:
            for qid in links[day]:
                f.write("%s:" %(qid) )
                for query_link in links[day][qid]:
                    f.write("%s," %(query_link))
                f.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_dir")
    parser.add_argument("dest_dir")
    args=parser.parse_args()



    queries = get_queries(args.query_dir)
    print "Got queries"
    links = get_links(queries)
    write_links(links,args.dest_dir)

if __name__=="__main__":
    main()

