"""
classes for silent days
"""

import os
import json
import sys
import re
import argparse
import codecs
from abc import ABCMeta,abstractmethod


sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster,Days,Year



class SilentDays(object):
    """
    base class for silent days
    """
    __metaclass__ = ABCMeta

    def __init__(self,year):
        self._year = year

        self._silent_days = {}

        if self._year == Year.y2015:
            self._prefix = "201507"
            self._eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"clusters-2015.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels.txt")
            self._topic_file = None
     
        elif self._year == Year.y2016:
            self._prefix = "201608"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"rts2016-batch-tweets2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"rts2016-batch-clusters.json")
            self._qrel_file = os.path.join(self._eval_dir,"qrels.txt")
            self._topic_file = None

        elif self._year == Year.y2011:
            self._prefix_mon = "201101"
            self._prefix_feb = "201102"
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"tweet2day")
            self._cluster_file = os.path.join(self._eval_dir,"cluster.json")
            self._qrel_file = os.path.join(self._eval_dir,"new_qrels")
            self._topic_file = os.path.join(self._eval_dir,"topics")

        elif self._year == Year.y2017:
            self._eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2017/eval'
            self._tweet2day_file = os.path.join(self._eval_dir,"rts2017-batch-tweets2dayepoch.txt")
            self._cluster_file = os.path.join(self._eval_dir,"rts2017-batch-clusters.json")
            self._qrel_file = os.path.join(self._eval_dir,"rts2017-batch-qrels.txt")
            self._topic_file = None


        else:
            raise NotImplementedError("Year %s is not implemented!" %(self._year.name))

        self._t2day = T2Day(self._tweet2day_file,year=self._year)
        self._sema_cluster = SemaCluster(self._cluster_file,self._t2day,self._year)
        self._days = Days(self._qrel_file,self._year,self._topic_file).days
        self._qrel = Qrel(self._qrel_file,self._days,year=self._year)
        # print self._qrel._judgement
        self._judged_qids = self._qrel.qids
        print self._qrel.qids

    @abstractmethod
    def _get_silent_days(self):
        pass

    @property
    def silent_days(self):
        if not self._silent_days:
            self._get_silent_days()

        return self._silent_days

    @property
    def qrel(self):
        return self._qrel
    
    @property
    def all_days(self):
        return self._days
    

         
class SilentDaysFromRes(SilentDays):
    """
    Get silent days from results
    """

    def __init__(self,year,result_dir):
        super(SilentDaysFromRes,self).__init__(year)
        self._result_dir = result_dir

    def _get_silent_days(self):
        self._read_results()
        self._get_silent_days_from_results()


    def _read_results(self):
        self._results = {}
        all_days = set()
        for qid in self._days:
            for day in self._days[qid]:
                all_days.add(day)
        for day in os.walk(self._result_dir).next()[2]:
            if day not in all_days:
                continue
            day_result_file = os.path.join(self._result_dir,day)
            self._results[day] = {}
            with open(day_result_file) as f:
                for line in f:
                    line = line.rstrip()
                    parts = line.split()
                    qid = parts[0]
                    if qid in self._judged_qids:
                        if qid not in self._results[day]:
                            self._results[day][qid] = []
                        docid = parts[2]
                        self._results[day][qid].append(docid) 


    def _get_silent_days_from_results(self):
        # for day in self._results:

        #     for qid in self._results[day]:
        #         if day not in self._days[qid]:
        #             continue
        #         else:
        #             if day not in self._silent_days:
        #                 self._silent_days[day] = {}

        #             if self._qrel.is_irrelevant_day(qid,day,self._sema_cluster,{qid:self._results[day][qid][:10]}):
        #                 self._silent_days[day][qid] = True
        #             else:
        #                 self._silent_days[day][qid] = False

        for qid in self._days:
            for day in self._days[qid]:
                if day not in self._silent_days:
                    self._silent_days[day] = {}
                if day not in self._results or qid not in self._results[day]:
                    self._silent_days[day][qid] = True
                elif self._qrel.is_irrelevant_day(qid,day,self._sema_cluster,{qid:self._results[day][qid][:10]}):
                    self._silent_days[day][qid] = True
                else:
                    self._silent_days[day][qid] = False


class SilentDaysFromJug(SilentDays):
    """
    Get silent days from judgement
    """

    def __init__(self,year):
        super(SilentDaysFromJug,self).__init__(year)



    def _get_silent_days(self):
        non_silent_days = {}
        tweet2day_dt = {}
        

        
        for line in open(self._tweet2day_file).readlines():
            line = line.strip().split()
            tweet2day_dt[line[0]] = line[1]

        for line in open(self._qrel_file).readlines():
            parts = line.strip().split()
            qid = parts[0]
            tid = parts[2]
            score = int(parts[3])
            try:
                tweet_day = tweet2day_dt[tid]
            except KeyError:
                # if score > 0:
                #     print "Cannot find relevant %s" %(tid)
                continue
            if qid not in non_silent_days:
                non_silent_days[qid] = set()
            if score > 0:
                non_silent_days[qid].add(tweet_day)

            else:
                continue

        for qid in non_silent_days:
            
            for day in self._days[qid]:
                if day not in self._silent_days:
                    self._silent_days[day] = {}
                if self._year == Year.y2011:
                    if int(day) in range(9):
                        prefix = "201102"
                    else:
                        prefix = "201101"
                elif self._year == Year.y2016:
                    prefix = "201608"
                elif self._year == Year.y2015:
                    prefix = "201507"
                elif self._year == Year.y2017:
                    if int(day) >= 29:
                        prefix = "201707"
                    else:
                        prefix = "201708"
                else:
                    raise NotImplementedError("The Silent Day for year %w is not implemented" %(self._year.name))


                day_string = "%s%s" %(prefix,day.zfill(2))
                if day_string not in non_silent_days[qid]:
                    self._silent_days[day][qid] = True
                else:
                    self._silent_days[day][qid] = False



        # print "Show silent days:"
        # print silent_days
        # print "There are %d queries judged" %(len(silent_days))
        # print "-"*20












def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year","-y",choices=list(map(int, Year)),default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
                3:2017
        """)
    parser.add_argument("--result_dir","-rd")
    args=parser.parse_args()

    args.year = Year(args.year)
    if args.result_dir:
        silent_day_generator = SilentDaysFromRes(args.year,args.result_dir)
    else:
        silent_day_generator = SilentDaysFromJug(args.year)

    silent_days = silent_day_generator.silent_days
    print silent_days

    silent_day_count = 0
    total_count = 0
    print "There are %d days" %(len(silent_days.keys()))
    for qid in silent_days:
        for day in silent_days[qid]:
            total_count += 1
            if silent_days[qid][day]:
                silent_day_count += 1
            # print "There are %s queries of day %s" %(len(silent_days[day].keys()), day)
    # print silent_days

    print "%d out of %d are silent days" %(silent_day_count,total_count)

    true_count = 0
    all_days = silent_day_generator.all_days
    for qid in all_days:
        for day in all_days[qid]:
            if day not in silent_days or qid not in silent_days[day]:
                print "Missing %s %s" %(day,qid)
            true_count +=1

    print "True count %d" %(true_count)
if __name__=="__main__":
    main()

