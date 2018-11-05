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
from my_code.distribution.data import Year

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year","-y",choices=[0,1,3],default=0,type=int,
        help="""
            Choose the year:
                0:2015
                1:2016
                2:2011
                3:2017
        """)
    parser.add_argument("result_dir")
    parser.add_argument("--force","-f",action="store_true")
    parser.add_argument("--performance_dir","-pd",default="/infolab/headnode2/lukuang/2017-rts/code/my_code/post_analysis/predictor_analysis/DKE/performances",
        help="""
            Store the performances of each run
            """)
    args=parser.parse_args()


    EVAL_DIRS = {
        Year.y2015 : "/infolab/node4/lukuang/2015-RTS/2015-data/",
        Year.y2016 : "/infolab/node4/lukuang/2015-RTS/src/2016/eval",
        Year.y2017 : "/infolab/node4/lukuang/2015-RTS/src/2017/eval",
    }
    args.year = Year(args.year)
    performance_file_path = os.path.join(args.performance_dir,args.year.name )
    

    performances = {}
    if os.path.exists(performance_file_path):
        performances = json.load(open(performance_file_path))


    eval_dir = EVAL_DIRS[args.year]
    if args.year == Year.y2017:
        command_template = Template( "python $eval_dir/per-day-ndcg0.py " +
                                      "-q $eval_dir/rts2017-batch-qrels.txt " + 
                                      "-c $eval_dir/rts2017-batch-clusters.json " +
                                      "-t $eval_dir/rts2017-batch-tweets2dayepoch.txt " +
                                      "-r $result_file") 
    elif args.year == Year.y2016:
        command_template = Template( "python $eval_dir/per-day-ndcg0.py " +
                                      "-q $eval_dir/qrels.txt " + 
                                      "-c $eval_dir/rts2016-batch-clusters.json " +
                                      "-t $eval_dir/rts2016-batch-tweets2dayepoch.txt " +
                                      "-r $result_file")
    elif args.year == Year.y2015:
        command_template = Template( "python $eval_dir/per-day-ndcg0.py " +
                                      "-q $eval_dir/qrels.txt " + 
                                      "-c $eval_dir/clusters-2015.json " +
                                      "-t $eval_dir/tweet2dayepoch.txt " +
                                      "-r $result_file")
    else:
        raise NotImplementedError("Year {} not implemented".format(args.year.name))

    avg_performances = {}
    single_query_performances = defaultdict(float)
    updated = False
    m_name = "f2exp"
    max_fns = {}
    for fn in os.listdir(args.result_dir):
        # if fn not in ["raw_"+m_name,"expanded_"+m_name,"raw_"+m_name+"_fbDocs:10"]:
        if fn not in ["raw_"+m_name,"expanded_"+m_name]:
            continue

        # if the performances exists and we do not
        # want to force evaluate, use the existing
        # performances

        if (fn not in performances or  args.force ):
            updated = True
            performances[fn] = {}
            result_file = os.path.join(args.result_dir,fn)
            command = command_template.substitute(eval_dir=eval_dir,result_file=result_file)
            # print command
            p = subprocess.Popen(command,stdout=subprocess.PIPE,shell=True)
            while True:
                line = p.stdout.readline()
                if line != '':
                    rows = line.split()
                    qid = rows[1]
                    day = rows[2]
                    # try:
                    q_performance = float(rows[3])
                    # except IndexError:
                    # pass
                    # else:
                    if qid == "All":
                        performances[fn][qid] = q_performance
                    else:
                        if qid not in performances[fn]:
                            performances[fn][qid] = {}
                        performances[fn][qid][day] = q_performance
                        
                else:
                    break

        for qid in performances[fn]:

            if qid != "All":
                for day in performances[fn][qid]:
                    q_day_string = "%s_%s" %(qid,day)
                    if single_query_performances[q_day_string] < performances[fn][qid][day]:
                        max_fns[q_day_string] = fn
                    single_query_performances[q_day_string] = max(single_query_performances[q_day_string],
                                                                  performances[fn][qid][day])
            else:
                avg_performances[fn] =  performances[fn][qid] 

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

