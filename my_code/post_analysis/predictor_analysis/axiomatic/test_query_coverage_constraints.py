"""
test whether the query coverage constraint is true
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess
from nltk import corpus
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from enum import IntEnum, unique
from myStemmer import pstem as stem

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year

FULL_IND_DIR = {
    Year.y2015: "/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/incremental/29",
    Year.y2016: "/infolab/headnode2/lukuang/2016-rts/data/incremental_index",
    Year.y2011: "/infolab/node4/lukuang/2015-RTS/2011-data/incremental_index"
}

Q_DIR = {
    Year.y2015:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2015/raw/clarity_queries",
    Year.y2016:"/infolab/headnode2/lukuang/2016-rts/code/my_code/post_analysis/data/2016/raw/clarity_queries",
    Year.y2011:"/infolab/node4/lukuang/2015-RTS/2011-data/generated_data/raw/clarity_queries"
}


class TextRetriever(object):
    def __init__(self,judged_tweet_text_file):
        self._judged_tweet_text_file = judged_tweet_text_file
        if os.path.exists(self._judged_tweet_text_file):
            self._judged_tweet_text = json.load(open(self._judged_tweet_text_file))
            for tid in self._judged_tweet_text:
                if self._judged_tweet_text[tid]:
                    # self._judged_tweet_text[tid] = re.sub("[^\w]"," ",self._judged_tweet_text[tid])
                    self._judged_tweet_text[tid] = self._judged_tweet_text[tid].encode('ascii',errors='ignore')
        else:
            self._judged_tweet_text = {}


    def get_text_for_tid(self,index_dir,tid):
        if tid in self._judged_tweet_text:
            return self._judged_tweet_text[tid]
        else:
            run_command = "dumpindex %s dt `dumpindex %s di docno %s`"\
                    %(index_dir,index_dir,tid)

            p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
            content = p.communicate()[0]
            m = re.search("<TEXT>(.+?)</TEXT>",content,re.DOTALL)

            if m is not None:
                self._judged_tweet_text[tid] = m.group(1)
                return m.group(1)
            else:
                self._judged_tweet_text[tid] = None
                return None

    def store(self):
        with codecs.open(self._judged_tweet_text_file,"w","utf-8") as of:
            of.write(json.dumps(self._judged_tweet_text))


class TextWordsConverter(object):
    def __init__(self):
        self._stopwords = corpus.stopwords.words('english')

    def convert_text_to_words(self,text):
        words = [w for w in re.findall("\w+",text.lower()) if w not in self._stopwords]
        words = map(stem,words)
        return words




class QueryGenerator(object):
    def __init__(self,tweets,year):
        self._qids = tweets.keys()
        query_dir = Q_DIR[year]
        self._query_file = os.walk(query_dir).next()[2][0]
        self._query_file = os.path.join(query_dir,self._query_file)
        print "open query file:\n%s" %(self._query_file)

    def generate_queries(self,converter):
        queries = {}
        with open(self._query_file) as f:
            for line in f:
                line = line.rstrip()
                m = re.search("^(\w+):(.+)$",line)
                if m:
                    qid = m.group(1)
                    if qid not in self._qids:
                        continue
                    else:
                        words = converter.convert_text_to_words(m.group(2))
                        queries[qid] = words
        return queries


class TweetForPlot(object):
    def __init__(self,qid,tid,words,relevance):
        self._qid,self._tid,self._words,self._relevance = \
                qid,tid,words,relevance
    def get_coverage(self,query_words):
        coverage_count = 0
        for w in query_words:
            if w in self._words:
                coverage_count += 1
        return coverage_count*1.0/len(query_words)

    def is_relevant(self):
        return self._relevance



class TweetGenerator(object):
    def __init__(self,year):
        self._year = year
        self._index_dir = FULL_IND_DIR[self._year]

        if self._year == Year.y2015:
            self._eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels.txt")
     
        elif self._year == Year.y2016:
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            self._qrel_file = os.path.join(self._eval_dir,"qrels.txt")

        elif self._year == Year.y2011:
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels")

        else:
            raise NotImplementedError("Year %s is not implemented!" %(self._year.name))

    def generate_tweets(self,text_retriever,converter):
        tweets = {}
        missing_tweet_count = 0
        total_tweet_count = 0
        with open(self._qrel_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                tid = parts[2]
                relevance_string = parts[3]
                if qid not in tweets:
                    tweets[qid] = []
                single_tweet = self._generate_single_tweet(text_retriever,converter,qid,tid,relevance_string)
                if single_tweet is not None:
                    tweets[qid].append(single_tweet)
                    missing_tweet_count += 1
                total_tweet_count += 1
        # print "%d out of %d tweets can be found" %(missing_tweet_count,total_tweet_count)
        return tweets


    def _generate_single_tweet(self,text_retriever,converter,qid,tid,relevance_string):
        text = text_retriever.get_text_for_tid(self._index_dir, tid)
        if text is None:
            # print "tweet %s cannot be found!" %(tid)
            return None
        words = converter.convert_text_to_words(text)
        relevance = False
        if int(relevance_string) > 0:
            relevance = True
        return TweetForPlot(qid,tid,words,relevance)

    

        




def prepare_probability(text_retriever,converter,year):
    tweet_generator = TweetGenerator(year)
    tweets = tweet_generator.generate_tweets(text_retriever,converter)
    text_retriever.store()

    query_generator = QueryGenerator(tweets,year)
    queries = query_generator.generate_queries(converter)

    relevance_count = {}
    total_count = {}

    for qid in queries:
        for tweet in tweets[qid]:
            coverage = tweet.get_coverage(queries[qid])
            if coverage not in total_count:
                total_count[coverage] = 0
                relevance_count[coverage] = 0
            total_count[coverage] += 1
            if tweet.is_relevant():
                relevance_count[coverage] += 1

    probability = {}
    for coverage in sorted(total_count.keys()):
        print "for coverage %f, there are %d out of %d tweets that are relevant" %(coverage,relevance_count[coverage],total_count[coverage])
        probability[coverage] = relevance_count[coverage]*1.0/total_count[coverage]

    return probability


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-py","--per_year",action="store_true")
    parser.add_argument("-pc","--per_collection",action="store_true")
    parser.add_argument("-a","--all",action="store_true")
    parser.add_argument("judged_tweet_text_file")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    converter = TextWordsConverter()
    text_retriever = TextRetriever(args.judged_tweet_text_file)
    

    per_year_probability = {}

    for year in Year:
        print "process year %s" %(year.name)
        per_year_probability[year] = prepare_probability(text_retriever,converter,year)
        coverages = []
        probabilities = []
        for coverage in sorted(per_year_probability[year].keys()):
            coverages.append(coverage)
            probabilities.append(per_year_probability[year][coverage])

        plt.plot(coverages, probabilities, 'ro', label='probabilities')
        plt.ylim([0,1])
        plt.legend()
        dest_file = os.path.join(args.dest_dir,year.name)
        plt.savefig(dest_file)
        plt.clf()


if __name__=="__main__":
    main()

