"""
computing coverage considering idf of terms
"""

import os
import json
import sys
import re
import argparse
import time
import codecs
import subprocess

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

from test_query_coverage_constraints import Q_DIR,FULL_IND_DIR,PlotType,TextRetriever,TextWordsConverter,TweetForPlot,TweetGenerator,plot

IND_DIR = {
    Year.y2015: "/infolab/node4/lukuang/2015-RTS/2015-data/collection/simulation/index/individual",
    Year.y2016: "/infolab/headnode2/lukuang/2016-rts/data/full_index_reparsed",
    Year.y2011: "/infolab/node4/lukuang/2015-RTS/2011-data/individual_index"
}


def return_1(day_index_dir,query_words):
    return 1


def get_term_idf(day_index_dir,term):
    run_command = ["/infolab/headnode2/lukuang/2017-rts/code/my_code/post_analysis/predictor_analysis/axiomatic/c_code/idf",
                   "-index=%s" %(day_index_dir),
                   "-query_term=%s" %(term)]

    p = subprocess.Popen(run_command,stdout=subprocess.PIPE)
    output = p.communicate()[0]
    try:
        value = float(output.rstrip()) 
    except ValueError:
        print "output is:\n%s" %(output)
        print run
        sys.exit(-1)
    return value

def get_idf(day_index_dir,query_words):
    idfs = {}
    # since I directly used the documentStemCount function, use 
    # the stemmed term here
    for w in query_words:
        idfs[w] = get_term_idf(day_index_dir,w)
        # idfs[w] = return_1(day_index_dir,w)

    return idfs


class YearStats(object):
    def __init__(self,year):
        self._year = year


        if self._year == Year.y2015:
            self._eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2dayepoch.txt")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels.txt")
            self._topic_file = None
     
        elif self._year == Year.y2016:
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"rts2016-batch-tweets2dayepoch.txt")
            self._qrel_file = os.path.join(self._eval_dir,"qrels.txt")
            self._topic_file = None

        elif self._year == Year.y2011:
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2day")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels")
            self._topic_file = os.path.join(self._eval_dir,"topics")

        else:
            raise NotImplementedError("Year %s is not implemented!" %(self._year.name))

        self._t2day = T2Day(self._tweet2day_file,year=self._year)
        self._days = Days(self._qrel_file,self._year,self._topic_file).days
        self._qrel = Qrel(self._qrel_file,self._days,year=self._year)
        self._judged_qids = self._qrel.qids
    
    @property
    def t2day(self):
        return self._t2day
        
    @property
    def days(self):
        return self._days

    @property
    def qids(self):
        return self._judged_qids
    
    

class WeightQuery(object):
    def __init__(self,year,days,query_words):

        self._year,self._query_words = year,query_words
        self._top_day_index_dir = IND_DIR[year]
        self._idfs = {}
        self._day_idf_sum = {}
        for day in days:
            day_index_dir = os.path.join(self._top_day_index_dir,day)
            self._idfs[day] = get_idf(day_index_dir,query_words)
            self._day_idf_sum[day] = sum(self._idfs[day].values())

    @property
    def idfs(self):
        return self._idfs

    @property
    def day_idf_sum(self):
        return self._day_idf_sum
    
    

class WeightQueryGenerator(object):
    def __init__(self,year,year_stats):
        self._year = year
        query_dir = Q_DIR[year]
        self._query_file = os.walk(query_dir).next()[2][0]
        self._query_file = os.path.join(query_dir,self._query_file)
        print "open query file:\n%s" %(self._query_file)
        self._qids = year_stats.qids 
        self._days = year_stats.days

    def generate_queries(self,converter,query_length,required_qid=None):
        queries = {}
        # max_length = 0
        with open(self._query_file) as f:
            for line in f:
                line = line.rstrip()
                m = re.search("^(\w+):(.+)$",line)
                if m:
                    qid = m.group(1)
                    if required_qid:
                        if qid != required_qid:
                            continue
                    if qid not in self._qids:
                        continue
                
                    else:
                        words = converter.convert_text_to_words(m.group(2))
                        if query_length is None:
                            queries[qid] = WeightQuery(self._year,self._days[qid],words)
                        elif len(words) != query_length:
                            continue
                        else:
                            queries[qid] = WeightQuery(self._year,self._days[qid],words)
        #                 if len(words)> max_length:
        #                     max_length = len(words)
        # print "max query length: %d" %(max_length)
        print "queries: "
        print queries.keys()
        return queries


class WeightTweetForPlot(TweetForPlot):
    def __init__(self,qid,tid,words,relevance, day):
        self._qid,self._tid,self._words,self._relevance,self._day = \
                qid,tid,words,relevance,day

    def get_coverage(self,query):
        coverage_count = .0
        if query.day_idf_sum[self._day] != 0:
            try:
                for w in query.idfs[self._day]:
                    if w in self._words:
                        coverage_count += query.idfs[self._day][w]
            except KeyError:
                print "Error day %s" %(self._day)
                print "Qid:%s" %(self._qid)
                print "Tid:%s" %(self._tid)
                sys.exit(-1)
            coverage = coverage_count*1.0/query.day_idf_sum[self._day]
        else:
            for w in query.idfs[self._day]:
                if w in self._words:
                    coverage_count += 1
            coverage = coverage_count*1.0/len(query.idfs[self._day])

        # print "for query %s and tweet %s" %(self._qid,self._tid)
        # print "coverage %f and idf sum %f" %(coverage_count,query.day_idf_sum[self._day])
        # time.sleep(3)
        return round(coverage,2)

    def get_subquery(self,query):
        subquery_term_list = []
        for w in query.idfs[self._day]:
            if w in self._words:
                subquery_term_list.append(w)
        return ("_".join(sorted(subquery_term_list)))


class WeightTweetGenerator(TweetGenerator):
    def __init__(self,year,year_stats):
        super(WeightTweetGenerator,self).__init__(year)

        self._t2day = year_stats.t2day

        self._days = year_stats.days

    def generate_tweets(self,text_retriever,converter,required_qid=None):
        tweets = {}
        missing_tweet_count = 0
        total_tweet_count = 0
        with open(self._qrel_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                tid = parts[2]
                if required_qid:
                    if qid != required_qid:
                        continue
                day = self._t2day.get_date(tid)
                if day is None:
                    # print "Cannot find day for %s" %(tid)
                    continue 
                else:
                    day = str(int(self._t2day.get_date(tid)) )
                if day not in self._days[qid]:
                    # print "day %s not in days for %s" %(day,qid)
                    continue
                relevance_string = parts[3]
                if qid not in tweets:
                    tweets[qid] = []
                single_tweet = self._generate_single_tweet(text_retriever,converter,qid,tid,relevance_string,day)
                if single_tweet is not None:
                    tweets[qid].append(single_tweet)
                    missing_tweet_count += 1
                total_tweet_count += 1
        # print "%d out of %d tweets can be found" %(missing_tweet_count,total_tweet_count)
        return tweets

    def _generate_single_tweet(self,text_retriever,converter,qid,tid,relevance_string,day):
        text = text_retriever.get_text_for_tid(self._index_dir, tid)
        if text is None:
            # print "tweet %s cannot be found!" %(tid)
            return None
        words = converter.convert_text_to_words(text)
        relevance = False
        if int(relevance_string) > 0:
            relevance = True
        return WeightTweetForPlot(qid,tid,words,relevance,day)



def prepare_count(text_retriever,converter,year,query_length,year_stats):
    tweet_generator = WeightTweetGenerator(year,year_stats)
    tweets = tweet_generator.generate_tweets(text_retriever,converter)
    text_retriever.store()
    print year_stats.days
    query_generator = WeightQueryGenerator(year,year_stats)
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

def prepare_per_query_count(text_retriever,converter,year,query_length,year_stats,show_subquery,required_qid):
    tweet_generator = WeightTweetGenerator(year,year_stats)
    tweets = tweet_generator.generate_tweets(text_retriever,converter,required_qid)
    text_retriever.store()

    query_generator = WeightQueryGenerator(year,year_stats)
    queries = query_generator.generate_queries(converter,query_length,required_qid)

    if show_subquery:
        subquery_coverage = {}

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
            if show_subquery:
                if coverage not in subquery_coverage:
                    subquery_coverage[coverage] = set()
                subquery_coverage[coverage].add(tweet.get_subquery(queries[qid]))
            total_count[qid][coverage] += 1
            if tweet.is_relevant():
                relevance_count[qid][coverage] += 1

    if show_subquery:
        print "show subquery and its coverage:"
        for coverage in sorted(subquery_coverage.keys()):
            print "%f %d-%d:" %(coverage,relevance_count[qid][coverage],total_count[qid][coverage])
            for subquery in subquery_coverage[coverage]:
                print "\t%s" %(subquery)


    # probability = {}
    # for coverage in sorted(total_count.keys()):
    #     print "for coverage %f, there are %d out of %d tweets that are relevant" %(coverage,relevance_count[coverage],total_count[coverage])
    #     probability[coverage] = relevance_count[coverage]*1.0/total_count[coverage]

    return relevance_count,total_count



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-py","--per_year",action="store_true")
    parser.add_argument("-pc","--per_collection",action="store_true")
    parser.add_argument("-pq","--per_query",action="store_true")
    parser.add_argument("-ss","--show_subquery",action="store_true")
    parser.add_argument("-a","--all",action="store_true")
    parser.add_argument("-ql","--query_length",type=int)
    parser.add_argument("-rq","--required_qid",type=str)
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
        year = Year.y2016
        year_stats = YearStats(year)
        relevance_count,total_count = prepare_per_query_count(text_retriever,converter,year,args.query_length,
                                                              year_stats,args.show_subquery,args.required_qid)

         
        for qid in relevance_count:
            dest_file = os.path.join(args.dest_dir,qid)

            plot(args.plot_type, dest_file,relevance_count[qid],total_count[qid],qid)
    else:
        for year in Year:
            print "process year %s" %(year.name)
            year_stats = YearStats(year)
            relevance_count,total_count = prepare_count(text_retriever,converter,year,args.query_length,year_stats)
            print sorted(relevance_count.keys())
            print "There are %d coverage values" %(len(relevance_count))
            dest_file = os.path.join(args.dest_dir,year.name)

            plot(args.plot_type, dest_file,relevance_count,total_count,year.name)
        


if __name__=="__main__":
    main()

