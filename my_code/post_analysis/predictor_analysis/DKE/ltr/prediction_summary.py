"""
Summarize the predictions for all feature sets
"""

import os
import json
import sys
import re
import argparse
import codecs
from collections import OrderedDict
from scipy.stats import ttest_rel

def get_report_info(report_file):
    with open(report_file) as f:
        for line in f:
            if 'oracle:' in line:
                m = re.search('oracle:(\S+)$',line)
                oracle_avg = float(m.group(1))
            elif 'best baseline vs' in line:
                m = re.search('p-value of:(\S+)$',line)
                p_value = float(m.group(1))
            elif 'best baseline(' in line:
                m = re.search(':([0-9\.]+)$',line)
                best_baseline_avg = float(m.group(1))
    return oracle_avg, best_baseline_avg, p_value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction_dir",default='/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/ltr/data/collection_cv')
    args=parser.parse_args()

    avgs = {}
    performance_list = {}
    p_over_baseline = {}
    for feature_set in os.listdir(args.prediction_dir):
        feature_result_dir = os.path.join(args.prediction_dir,feature_set)
        for collection_name in os.listdir(feature_result_dir):
            if collection_name not in avgs:
                avgs[collection_name] = OrderedDict()
                performance_list[collection_name] = {}
                p_over_baseline[collection_name] = {}
            collection_dir =  os.path.join(feature_result_dir,collection_name)
            print 'process {}'.format(collection_dir)
            predictions = json.load(open( os.path.join(collection_dir, 'predictions') ))
            report_file = os.path.join(collection_dir, 'report')
            oracle_avg, best_baseline_avg, p_value = get_report_info(report_file)
            print "avgs: {} {} {}".format(oracle_avg, best_baseline_avg, p_value)
            p_over_baseline[collection_name][feature_set] = p_value
            avgs[collection_name]['oracle'] = oracle_avg
            avgs[collection_name]['best_baseline'] = best_baseline_avg
            avgs[collection_name][feature_set] = sum(predictions.values()) / len(predictions)
            performance_list[collection_name][feature_set] = predictions


    for collection_name in performance_list:
        print 'For collection {}'.format(collection_name)
        print '\toracle avg:{}'.format( round(avgs[collection_name]['oracle'],4) )
        print '\tbest_baseline avg:{}'.format( round(avgs[collection_name]['best_baseline'],4) )
        for feature_set in performance_list[collection_name]:
            print '\t{} avg:{}'.format(feature_set,
                                       round(avgs[collection_name][feature_set],4)) 
            significant = []
            print '\t\tp-values:'
            print '\t\t\tbest_baselines:{}'.format( round(p_over_baseline[collection_name][feature_set],4) )
            for other_feature_set in performance_list[collection_name]:
                if other_feature_set != feature_set:
                    other_list = []
                    target_list = []
                    for qid in performance_list[collection_name][feature_set]:
                        other_list.append(performance_list[collection_name][feature_set][qid])
                        target_list.append(performance_list[collection_name][other_feature_set][qid])
                    pvalue = round(ttest_rel(target_list,other_list).pvalue, 4)
                    print '\t\t\t{}:{}'.format(other_feature_set, pvalue)
        print '-'*10

if __name__=="__main__":
    main()

