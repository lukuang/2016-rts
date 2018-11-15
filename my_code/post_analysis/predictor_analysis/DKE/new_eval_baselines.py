"""
evaluate various baselines and get the oracle
performance as of NDCG@10-1
"""
from __future__ import division
import os
import json
import sys
import re
import argparse
from string import Template
from collections import defaultdict, Counter
import subprocess

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year

class CorpusInfo(object):
    def __init__(self,year):
        self._year  = year

        if year == Year.y2015:
            prefix = "201507"
            eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            tweet2day_file = os.path.join(eval_dir,"tweet2dayepoch.txt")
            cluster_file = os.path.join(eval_dir,"clusters-2015.json")
            qrel_file = os.path.join(eval_dir,"new_qrels.txt")
            topic_file = None
     
        elif year == Year.y2016:
            prefix = "201608"
            eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            tweet2day_file = os.path.join(eval_dir,"rts2016-batch-tweets2dayepoch.txt")
            cluster_file = os.path.join(eval_dir,"rts2016-batch-clusters.json")
            qrel_file = os.path.join(eval_dir,"qrels.txt")
            topic_file = None

        elif year == Year.y2011:
            prefix_mon = "201101"
            prefix_feb = "201102"
            eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            tweet2day_file = os.path.join(eval_dir,"tweet2day")
            cluster_file = os.path.join(eval_dir,"cluster.json")
            qrel_file = os.path.join(eval_dir,"new_qrels")
            topic_file = os.path.join(eval_dir,"topics")

        elif year == Year.y2017:
            eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2017/eval'
            tweet2day_file = os.path.join(eval_dir,"rts2017-batch-tweets2dayepoch.txt")
            cluster_file = os.path.join(eval_dir,"rts2017-batch-clusters.json")
            qrel_file = os.path.join(eval_dir,"rts2017-batch-qrels.txt")
            topic_file = None

        self.t2day = T2Day(tweet2day_file,year=year)
        self.sema_cluster = SemaCluster(cluster_file,self.t2day,year)
        self.eval_days = Days(qrel_file,year,topic_file).days
        self.qrel = Qrel(qrel_file,self.eval_days,year=year)

    def get_ndcg10(self,results):
        ndcg10 = self.qrel.get_raw_ndcg10_per_pair(results,
                                                   self.eval_days,
                                                   self.sema_cluster)
        return ndcg10

def read_results(result_file):
    results = {}
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            day = int(parts[0][6:])
            day = str(day)
            qid = parts[1]
            tid = parts[3]
            if day not in results:
                results[day] = {}
            if qid not in results[day]:
                results[day][qid] = []
            results[day][qid].append(tid)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year","-y",choices=range(4),default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
                3:2017
        """)
    parser.add_argument("result_dir")
    parser.add_argument("--force","-f",action="store_true")
    parser.add_argument("--performance_dir","-pd",default="/infolab/headnode2/lukuang/2017-rts/code/my_code/post_analysis/predictor_analysis/DKE/performances/raw",
        help="""
            Store the performances of each run
            """)
    args=parser.parse_args()



    args.year = Year(args.year)
    performance_file_path = os.path.join(args.performance_dir,args.year.name )
    corpus_info = CorpusInfo(args.year)

    performances = {}
    if os.path.exists(performance_file_path):
        performances = json.load(open(performance_file_path))

    avg_performances = {}
    single_query_performances = defaultdict(float)
    updated = False
    m_name = "f2exp"
    max_fns = {}
    for fn in os.listdir(args.result_dir):
        # # if fn not in ["raw_"+m_name,"expanded_"+m_name,"raw_"+m_name+"_fbDocs:10"]:
        # # if fn not in ["raw_"+m_name,"expanded_"+m_name]:
        # # if "expanded_" in fn or ("fbDocs:" in fn and "10" not in fn):
        # if "expanded_" in fn:
        #     continue
        # print "process file %s" %(fn)
        # if the performances exists and we do not
        # want to force evaluate, use the existing
        # performances
        if 'expanded' in fn:
            continue

        if (fn not in performances or  args.force ):
            updated = True
            performances[fn] = {}
            result_file = os.path.join(args.result_dir,fn)
            fn_results = read_results(result_file)
            performances[fn] = corpus_info.get_ndcg10(fn_results) 
        count  = 0
        avg_performances[fn] = .0
        for qid in performances[fn]:

            for day in performances[fn][qid]:
                q_day_string = "%s_%s" %(qid,day)
                if single_query_performances[q_day_string] < performances[fn][qid][day]:
                    max_fns[q_day_string] = fn
                single_query_performances[q_day_string] = max(single_query_performances[q_day_string],
                                                                performances[fn][qid][day])
                avg_performances[fn] += performances[fn][qid][day]
                count += 1
        # print performances[fn]
        avg_performances[fn] /=  count

    best_fn = ""
    best_avg = -100
    for fn in avg_performances:
        performance = avg_performances[fn]
        if performance > best_avg:
            best_avg = performance
            best_fn = fn

    if updated:
        with open(performance_file_path,"w") as f:
            f.write(json.dumps(performances,indent=2))


    print avg_performances
    print "F2exp average is {0:.4f}".format(avg_performances["raw_f2exp"])

    print "The best average performance is {0:.4f} which is achived by {1}".format(best_avg,best_fn)

    print "The oracle/best per-topic performance is {0:.4f}".format( sum(single_query_performances.values())/ len(single_query_performances) )

    print Counter(max_fns.values())
    # for q_day_string in max_fns:
    #     m = re.search("^(\S+)_(\S+)$",q_day_string)
    #     qid = m.group(1)
    #     day = m.group(2)
    #     trio_string = ""

    #     for fn in avg_performances:
    #         trio_string += " %s:%f," %(fn,performances[fn][qid][day])
    #     print trio_string  
if __name__=="__main__":
    main()

