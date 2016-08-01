"""
re compute threshold
"""

import os
import json
import sys
import re
import argparse
import codecs
import subprocess

def compute_day_clarities(show_clarity_file,date_index_dir,date_clarity_query_file):

    day_clarities = {}
    run_command = "%s %s %s" %(show_clarity_file,date_index_dir,date_clarity_query_file)
    #print "command being run:\n%s" %(run_command)
    p = subprocess.Popen(run_command,stdout=subprocess.PIPE,shell=True)
    
    while True:
        line = p.stdout.readline()
        if line != '':
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            day_clarities[qid] = float(parts[1])
            

        else:
            break 
    return day_clarities

def get_coeff(coeff_file):
        coeff =  json.load(open(coeff_file))
        return coeff

def compute_new_threshold(day_clarities,coeff,scores):
    threshold = {}
    for qid in day_clarities:
        threshold[qid] = day_clarities[qid]*coeff[0]
        threshold[qid] += scores[qid][0]*coeff[1]
        for i in range(len(scores[qid])-1):
            try:
                threshold[qid] += coeff[i+2]*(scores[qid][i+1] - scores[qid][i]) 
            except IndexError:
                print i,len(coeff),len(scores[qid])
    return threshold         

def read_results(result_file):
    scores = {}
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            qid = parts[0]
            score = float(parts[4])
            if qid not in scores:
                scores[qid] = []
            scores[qid].append(score)
    return scores


def change_threshold(dest_file,date,thresholds):
    old = json.load(open(dest_file))
    if date in old:
        print "change for data %s" %date
        old[date] = thresholds
        with open(dest_file,"w") as f:
            f.write(json.dumps(old))
    else:
        print "No such date %s!" %date
        print "no change was made!"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("show_clarity_file")
    parser.add_argument("date_index_dir")
    parser.add_argument("date_clarity_query_file")
    parser.add_argument("coeff_file")
    parser.add_argument("result_file")
    parser.add_argument("date")
    parser.add_argument("dest_file")


    args=parser.parse_args()

    day_clarities = compute_day_clarities(args.show_clarity_file,
                                          args.date_index_dir,
                                          args.date_clarity_query_file)
    coeff = get_coeff(args.coeff_file)

    scores = read_results(args.result_file)
    thresholds = compute_new_threshold(day_clarities,coeff,scores)

    print thresholds

    print "change threshold for file %s" %args.dest_file
    change_threshold(args.dest_file,args.date,thresholds)



if __name__=="__main__":
    main()

