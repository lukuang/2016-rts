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
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
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



@unique
class PlotType(IntEnum):
    dot_plot = 0
    bar_chart = 1


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

    def generate_queries(self,converter,query_length):
        queries = {}
        # max_length = 0
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
                        if query_length is None:
                            queries[qid] = words
                        elif len(words) != query_length:
                            continue
                        else:
                            queries[qid] = words
        #                 if len(words)> max_length:
        #                     max_length = len(words)
        # print "max query length: %d" %(max_length)
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

    

        




def prepare_count(text_retriever,converter,year,query_length):
    tweet_generator = TweetGenerator(year)
    tweets = tweet_generator.generate_tweets(text_retriever,converter)
    text_retriever.store()

    query_generator = QueryGenerator(tweets,year)
    queries = query_generator.generate_queries(converter,query_length)

    relevance_count = {}
    total_count = {}

    for qid in queries:
        for tweet in tweets[qid]:
            coverage = tweet.get_coverage(queries[qid])
            # if coverage == 0:
            #     print "tweet %s for query %s has coverage 0!" %(tweet._tid,qid)
            if coverage not in total_count:
                total_count[coverage] = 0
                relevance_count[coverage] = 0
            total_count[coverage] += 1
            if tweet.is_relevant():
                relevance_count[coverage] += 1

    # probability = {}
    for coverage in sorted(total_count.keys()):
        print "for coverage %f, there are %d out of %d tweets that are relevant" %(coverage,relevance_count[coverage],total_count[coverage])
        # probability[coverage] = relevance_count[coverage]*1.0/total_count[coverage]

    return relevance_count,total_count

def prepare_per_query_count(text_retriever,converter,year,query_length):
    tweet_generator = TweetGenerator(year)
    tweets = tweet_generator.generate_tweets(text_retriever,converter)
    text_retriever.store()

    query_generator = QueryGenerator(tweets,year)
    queries = query_generator.generate_queries(converter,query_length)

    relevance_count = {}
    total_count = {}

    for qid in queries:
        relevance_count[qid] = {}
        total_count[qid] = {}
        for tweet in tweets[qid]:
            coverage = tweet.get_coverage(queries[qid])
            # if coverage == 0:
            #     print "tweet %s for query %s has coverage 0!" %(tweet._tid,qid)
            if coverage not in total_count[qid]:
                total_count[qid][coverage] = 0
                relevance_count[qid][coverage] = 0
            total_count[qid][coverage] += 1
            if tweet.is_relevant():
                relevance_count[qid][coverage] += 1

    # probability = {}
    # for coverage in sorted(total_count.keys()):
    #     print "for coverage %f, there are %d out of %d tweets that are relevant" %(coverage,relevance_count[coverage],total_count[coverage])
    #     probability[coverage] = relevance_count[coverage]*1.0/total_count[coverage]

    return relevance_count,total_count


def plot(plot_type,dest_file,relevance_count,total_count,data_lable):
    if len(relevance_count) == 0:
        print "No queries!"
        return 
    if plot_type == PlotType.dot_plot:
        dot_plot(dest_file,relevance_count,total_count,data_lable)
    elif plot_type == PlotType.bar_chart:
        bar_chart_plot(dest_file,relevance_count,total_count,data_lable)
    else:
        raise NotImplementedError("The plot type is not implemented:%s" %(str(plot_type)) )

def dot_plot(dest_file,relevance_count,total_count,data_lable):
    coverages = []
    probabilities = []
    for coverage in sorted(relevance_count.keys()):
        coverages.append(coverage)
        single_probability = relevance_count[coverage]*1.0/total_count[coverage]
        probabilities.append(single_probability)
    plt.plot(coverages, probabilities, 'ro', label=data_lable)
    plt.title(data_lable)
    plt.ylabel("probabilities")
    plt.xlabel('query coverage')
    plt.ylim([0,1])
    plt.xlim([0,1.1])
    plt.legend()
    plt.savefig(dest_file)
    plt.clf()

def bar_chart_plot(dest_file,relevance_count,total_count,data_lable):
    # bin_name = ("0.0-0.1","0.1-0.2","0.2-0.3","0.3-0.4","0.4-0.5",
    #         "0.5-0.6","0.6-0.7","0.7-0.8","0.8-0.9","0.9-1.0")
    # bin_pos = np.arange(len(bin_name))
    bin_size = 101
    bin_pos = np.arange(bin_size)
    bin_relevance_count = [0]*bin_size
    bin_total_count = [0]*bin_size
    bin_probabilities = [0]*bin_size
    for coverage in sorted(relevance_count.keys()):
        pos = int(math.floor(coverage*(bin_size-1))) 
        # if pos == bin_size:
        #     pos = bin_size -1
        bin_relevance_count[pos] += relevance_count[coverage]
        bin_total_count[pos] += total_count[coverage]
        # print "add the counts of %f to bin %s" %(coverage,bin_name[pos])

    for i in range(bin_size):
        try:
            bin_probabilities[i] = bin_relevance_count[i]*1.0/bin_total_count[i]
        except ZeroDivisionError:
            pass
    plt.bar(bin_pos, bin_probabilities, align='center', alpha=0.5)
    plt.title(data_lable)
    # plt.xticks(bin_pos)
    plt.ylim([0,1])
    plt.ylabel("probabilities")
    plt.xlabel('coverage range')
    plt.savefig(dest_file)
    plt.clf()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-py","--per_year",action="store_true")
    parser.add_argument("-pc","--per_collection",action="store_true")
    parser.add_argument("-pq","--per_query",action="store_true")
    parser.add_argument("-a","--all",action="store_true")
    parser.add_argument("-ql","--query_length",type=int)
    parser.add_argument("--plot_type","-pt",choices=list(map(int, PlotType)),default=0,type=int,
        help="""
            Choose the plot type:
                0:dot_plot
                1:bar_chart
        """)
    parser.add_argument("judged_tweet_text_file")
    parser.add_argument("dest_dir")
    args=parser.parse_args()

    args.plot_type = PlotType(args.plot_type)

    converter = TextWordsConverter()
    text_retriever = TextRetriever(args.judged_tweet_text_file)
    

    per_year_probability = {}
    if args.per_query:
        print "print per query plot for 2016"
        relevance_count,total_count = prepare_per_query_count(text_retriever,converter,Year.y2016,args.query_length)
        for qid in relevance_count:
            dest_file = os.path.join(args.dest_dir,qid)

            plot(args.plot_type, dest_file,relevance_count[qid],total_count[qid],qid)
    else:
        for year in Year:
            print "process year %s" %(year.name)
            relevance_count,total_count = prepare_count(text_retriever,converter,year,args.query_length)
            
            dest_file = os.path.join(args.dest_dir,year.name)

            plot(args.plot_type, dest_file,relevance_count,total_count,year.name)
        


if __name__=="__main__":
    main()

