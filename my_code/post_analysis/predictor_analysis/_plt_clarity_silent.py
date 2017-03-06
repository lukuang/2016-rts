"""
print silent day& clarity
"""

import os
import json
import sys
import re
import argparse
import codecs
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Qrel,T2Day,SemaCluster


def get_clarity(clarity_dir,days,judged_qids):
    clarities = {}
    for date in os.walk(clarity_dir).next()[2]:
        if date not in days:
            continue

        clarities[date] = {}
        day_clarity_file = os.path.join(clarity_dir,date)
        date_clarity = json.load(open(day_clarity_file))
        for qid in date_clarity:
            if qid in judged_qids:
                clarities[date][qid] = date_clarity[qid]

    return clarities


def read_results(result_dir,judged_qids,days):
    results = {}
    for day in os.walk(result_dir).next()[2]:
        if day not in days:
            continue
        day_result_file = os.path.join(result_dir,day)
        results[day] = {}
        with open(day_result_file) as f:
            for line in f:
                line = line.rstrip()
                parts = line.split()
                qid = parts[0]
                if qid in judged_qids:
                    if qid not in results[day]:
                        results[day][qid] = []
                    docid = parts[2]
                    results[day][qid].append(docid)                    

    return results


def load_silent_day(tweet2day_file,qrels_file,days,prefix):
    silent_days = {}
    non_silent_days = {}
    tweet2day_dt = {}
    for day in days:
        silent_days[day] = {}

    
    for line in open(tweet2day_file).readlines():
        line = line.strip().split()
        tweet2day_dt[line[0]] = line[1]

    for line in open(qrels_file).readlines():
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
        for day in days:
            day_string = "%s%s" %(prefix,day.zfill(2))
            if day_string not in non_silent_days[qid]:
                silent_days[day][qid] = True
            else:
                silent_days[day][qid] = False



    # print "Show silent days:"
    # print silent_days
    # print "There are %d queries judged" %(len(silent_days))
    # print "-"*20

    return silent_days



def get_silent_days_from_results(result_dir,qrel,sema_cluster):
    silent_days = {}
    judged_qids = qrel.qids
    days = qrel.days
    results = read_results(result_dir,judged_qids,days)
    for day in results:
        silent_days[day] = {}
        for qid in results[day]:
            if qrel.is_irrelevant_day(qid,day.zfill(2),sema_cluster,{qid:results[day][qid][:10]}):
                silent_days[day][qid] = True
            else:
                silent_days[day][qid] = False

    return silent_days



def plot_clarity(clarities,silent_days,dest_file):
    silent_clarities = []
    non_silent_clarities = []
    val = .0
    for day in clarities:
        for qid in clarities[day]:
            if silent_days[day][qid]:
                silent_clarities.append(clarities[day][qid])
                if clarities[day][qid] == 5.93344:
                    print "%s,%s" %(qid,day)
            else:
                non_silent_clarities.append(clarities[day][qid])

    print silent_clarities
    print max(silent_clarities)
    print non_silent_clarities
    print max(non_silent_clarities)
    plt.plot(silent_clarities, np.zeros_like(silent_clarities) + 1.0, 'ro',non_silent_clarities,np.zeros_like(non_silent_clarities) + -1.0,'bx')
    plt.ylim([-2,2])
    plt.savefig(dest_file)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year","-y",choices=[0,1],type=int,default=0,
            help="""
                Choose year:
                    0: 2015
                    1: 2016
            """)
    parser.add_argument("--get_from_results","-r",action="store_true",
            help="""
                If specified, get silent day info from results. Otherwise,
                use evaluation info.
            """)
    parser.add_argument("result_dir")
    parser.add_argument("clarity_dir")
    parser.add_argument("dest_file")
    args=parser.parse_args()

    #load eval info
    if args.year == 0:
        is_16 = False
        prefix = "201507"
        eval_dir = "/infolab/node4/lukuang/2015-RTS/2015-data/"
        tweet2day_file = os.path.join(eval_dir,"tweet2dayepoch.txt")
        cluster_file = os.path.join(eval_dir,"clusters-2015.json")
        qrel_file = os.path.join(eval_dir,"new_qrels.txt")
 
    else:
        is_16 = True
        prefix = "201608"
        eval_dir = '/infolab/node4/lukuang/2015-RTS/src/2016/eval'
        tweet2day_file = os.path.join(eval_dir,"rts2016-batch-tweets2dayepoch.txt")
        cluster_file = os.path.join(eval_dir,"rts2016-batch-clusters.json")
        qrel_file = os.path.join(eval_dir,"qrels.txt")


    t2day = T2Day(tweet2day_file,is_16=is_16)
    sema_cluster = SemaCluster(cluster_file,t2day,is_16=is_16)
    qrel = Qrel(qrel_file,is_16=is_16)
    days = qrel.days

    judged_qids = qrel.qids 
    clarities = get_clarity(args.clarity_dir,days,judged_qids)
    if args.get_from_results:
        silent_days = get_silent_days_from_results(args.result_dir,qrel,sema_cluster)
    else:
        silent_days = load_silent_day(tweet2day_file,qrel_file,days,prefix)

    # print clarities
    # print silent_days
    plot_clarity(clarities,silent_days,args.dest_file)


if __name__=="__main__":
    main()

