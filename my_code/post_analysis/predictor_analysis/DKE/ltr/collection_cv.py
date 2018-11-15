"""
do collection cross-validation
"""

import os
import json
import sys
import re
import argparse
import codecs
from collections import defaultdict
from shutil import copyfile
from string import Template
import subprocess 
from scipy.stats import ttest_rel

def load_compand_qid_performances(year_performance, 
                                  collection_best_performances,
                                  collection_method_performances,
                                  year):
    for method in year_performance:
        for day in year_performance[method]:
            for qid in year_performance[method][day]:
                value = year_performance[method][day][qid]
                new_qid = '{}_{}_{}'.format(year, day, qid)
                collection_best_performances[new_qid] = max(collection_best_performances[new_qid],value)
                collection_method_performances[method][new_qid] = value

def find_best_method(collection_method_performances):
    best_avg = .0
    best_method = None
    for method in collection_method_performances:
        method_avg = sum(collection_method_performances[method].values())/len(collection_method_performances[method])
        if method_avg > best_avg:
            best_avg = method_avg
            best_method = method
    return [best_avg, best_method, collection_method_performances[best_method]]

def load_performances(performance_dir):
    best_performances = {
                        'mb1516':defaultdict(float),
                        'mb2011':defaultdict(float),
                        'rts2017':defaultdict(float),
                    }

    method_performances = {
                        'mb1516':defaultdict(lambda: defaultdict(float)),
                        'mb2011':defaultdict(lambda: defaultdict(float)),
                        'rts2017':defaultdict(lambda: defaultdict(float)),
                    }

    for fn in os.listdir(performance_dir):
        year_performance = json.load(open( os.path.join(performance_dir,fn) ))
        if fn == 'y2017':
            load_compand_qid_performances(year_performance,
                                          best_performances['rts2017'],
                                          method_performances['rts2017'],
                                          fn)
        elif fn == 'y2011':
            load_compand_qid_performances(year_performance,
                                          best_performances['mb2011'],
                                          method_performances['mb2011'],
                                          fn)
        else:
            load_compand_qid_performances(year_performance,
                                          best_performances['mb1516'],
                                          method_performances['mb1516'],
                                          fn)

    return best_performances, method_performances

def load_result_performance(result_file):
    result_performances = {}
    old_qid = None
    with open(result_file) as f:
        for line in f:
            parts = line.split()
            qid = parts[0]
            if qid != old_qid:
                old_qid = qid
                m = re.search('performance=(\S+)', line)
                result_performances[qid] = float(m.group(1))

    return result_performances

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranker","-r",choices=range(9),default=6,type=int,
                        help= """
                            0: MART (gradient boosted regression tree)
                            1: RankNet
                            2: RankBoost
                            3: AdaRank
                            4: Coordinate Ascent
                            6: LambdaMART
                            7: ListNet
                            8: Random Forests
                        """)
    # parser.add_argument("--baseline","-bl",default="raw_f2exp",
    #                     help="""
    #                         The baseline method to compare against
    #                     """)
    parser.add_argument("--metric2t","-mt",default="NDCG@60")
    parser.add_argument("--verbose","-v",action="store_true")
    parser.add_argument("--rank_lib_file","-rf",default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/ltr/RankLib-2.1-patched.jar")
    parser.add_argument("--raw_dir",'-rd',default='/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/ltr/data/raw')
    parser.add_argument("--collection_cv_dir",default='/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/ltr/data/collection_cv')
    parser.add_argument("--performance_dir","-pfd", default="/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis/DKE/performances/raw",
                        help="""
                            directory that stores performances for all methods
                        """)
    parser.add_argument("--eval_only","-e",action='store_true')
    args=parser.parse_args()


    train_cmd_template = Template('java -jar %s -train $train_file -tvs 0.8 -ranker %d -metric2t %s -save $model_file'
                                  %(args.rank_lib_file, args.ranker,args.metric2t) )

    eval_cmd_template = Template('java -jar %s -load $model_file -rank $test_file -indri $result_file'
                                 %(args.rank_lib_file))

    print "Load performance"
    best_performances, method_performances = load_performances(args.performance_dir)
    best_baseline = {}
    for collection in method_performances:
        best_baseline[collection] = find_best_method(method_performances[collection])
    for dn in os.listdir(args.raw_dir):
        top_raw_dir = os.path.join(args.raw_dir,dn)
        if os.path.isdir(top_raw_dir):
            print 'process {}'.format(dn)
            top_cv_dir = os.path.join(args.collection_cv_dir,dn)
            
            collections = []
            for collection_name in os.listdir(top_raw_dir):
                collection_cv_dir = os.path.join(top_cv_dir,collection_name)
                if not os.path.exists(collection_cv_dir):
                    os.makedirs(collection_cv_dir)
                collections.append(collection_name)

            for test_collection_name in collections:
                print "\tGenerating data for {}".format(test_collection_name)
                collection_cv_dir = os.path.join(top_cv_dir,test_collection_name)
                collection_raw_file = os.path.join(top_raw_dir,test_collection_name)
                test_file = os.path.join(collection_cv_dir,'test')
                train_file = os.path.join(collection_cv_dir,'train')
                if not args.eval_only:
                    copyfile(collection_raw_file, test_file)
                    with open(train_file,'w') as of:
                        for train_collection_name in collections:
                            if train_collection_name != test_collection_name:
                                collection_raw_file = os.path.join(top_raw_dir,train_collection_name)
                                with open(collection_raw_file) as f:
                                    for line in f:
                                        of.write(line)

                # Generate Model
                print "\tGenerating model"
                if not args.eval_only:
                    model_file = os.path.join(collection_cv_dir,'model')
                    train_exe = train_cmd_template.substitute(train_file=train_file,
                                                              model_file=model_file)
                    
                    if args.verbose:
                        subprocess.call(train_exe,shell=True)
                                        
                    else:
                        subprocess.call(train_exe,shell=True,
                                        stdout=open(os.devnull, 'wb'))

                # Generate result
                print "\tGenerating result"
                result_file = os.path.join(collection_cv_dir,'result')
                if not args.eval_only:
                    eval_exe = eval_cmd_template.substitute(model_file=model_file,
                                                            test_file=test_file,
                                                          result_file=result_file)

                    if args.verbose:
                        subprocess.call(eval_exe,shell=True)
                    else:
                        subprocess.call(eval_exe,shell=True,
                                        stdout=open(os.devnull, 'wb'))

                # Check performance.
                # Compare to default, oracle and do statistical 
                # significant test
                result_performances = load_result_performance(result_file)
                if args.verbose:
                    print "\tThere are {} results".format( len(result_performances))

                print "Store predictions"
                prediction_file = os.path.join(collection_cv_dir,'predictions')
                for qid in best_performances[test_collection_name]:
                    if qid not in result_performances:
                        result_performances[qid] = .0
                with open(prediction_file,'w') as pf:
                    pf.write(json.dumps(result_performances,indent=2))

                report_file = os.path.join(collection_cv_dir,'report')
                oracle_performance_list = []
                result_performance_list = []
                baseline_performance_list = []
                for qid in best_performances[test_collection_name]:
                    oracle_performance_list.append(best_performances[test_collection_name][qid])
                    result_performance_list.append(result_performances[qid])
                    baseline_performance_list.append(best_baseline[test_collection_name][2][qid])

                oracle_avg = sum(oracle_performance_list) / len(oracle_performance_list)
                result_avg = sum(result_performance_list) / len(result_performance_list)
                baseline_avg = sum(baseline_performance_list) / len(baseline_performance_list)

                # store predictions

                # report training performances
                print "\tReport performance"
                with open(report_file,'w') as f:
                    f.write('avg:\n\toracle:{}\n\tpredicted:{}\n\tbest baseline({}):{}\n'.format(round(oracle_avg,4),
                                                                                                 round(result_avg,4),
                                                                                                 best_baseline[test_collection_name][1],
                                                                                                 round(baseline_avg,4),
                                                                                                 ))
                    oracle_predicted = ttest_rel(oracle_performance_list,result_performance_list)
                    f.write('oracle vs. predicted with the p-value of:{}\n'.format(round(oracle_predicted.pvalue,4)))
                    baseline_predicted = ttest_rel(baseline_performance_list,result_performance_list)
                    f.write(' best baseline vs. predicted with the p-value of:{}\n'.format(round(baseline_predicted.pvalue,4)))

                print '-'*20

if __name__=="__main__":
    main()

