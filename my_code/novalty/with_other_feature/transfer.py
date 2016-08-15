"""
transfer the classification training data to regression data
"""

import os
import json
import sys
import re
import argparse
import codecs

def load_data_set(data_dir):
    X = json.load(open(os.path.join(data_dir,"X")))
    y = json.load(open(os.path.join(data_dir,"y")))
    query_ids = json.load(open(os.path.join(data_dir,"query_ids")))
    return X,y,query_ids


def output_data(feature_vector,threshold_vector,query_ids,dest_dir):
    with open(os.path.join(dest_dir,"X"),"w") as f:
        f.write(json.dumps(feature_vector))

    with open(os.path.join(dest_dir,"y"),"w") as f:
        f.write(json.dumps(threshold_vector))

    with open(os.path.join(dest_dir,"query_ids"),"w") as f:
        f.write(json.dumps(query_ids))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("dest_dir")
    parser.add_argument("--performance_measure","-pm",choices=["f1","precision"],
                        default="f1")
    args=parser.parse_args()

    X, y, query_ids = load_data_set(args.source_dir)

    feature_vector = []
    threshold_vector = []
    set_features = {}
    #original_top_4 = {}

    for i in range(len(y)):
        single_feature_vector = X[i]
        label = y[i]
        day_statistic = tuple(single_feature_vector[:3])
        measure = single_feature_vector[-1]
        if day_statistic not in set_features:
            set_features[day_statistic] = {}
        set_features[day_statistic][measure] = label
        #original_top_4[day_statistic] = single_feature_vector[:3]


    for day_statistic in set_features:
        pos_support = sum(set_features[day_statistic].values())
        # skip a set of features without any positive
        # examples 
        if pos_support == 0:
            continue

        max_performance = .0
        num_of_pos = 0
        num_of_result = 0
        precision = []
        recall = []
        performance = []
        index = 0
        max_index = 0
        single_threshold = .0

        for measure in sorted(set_features[day_statistic].keys(), reverse=True):
            if measure <= 0.5:
                continue
            label = set_features[day_statistic][measure]
            num_of_result += 1
            if label == 1:
                num_of_pos += 1 
            precision_now = num_of_pos*1.0 / num_of_result
            recall_now = num_of_pos*1.0 / pos_support
            precision.append(precision_now)
            recall.append(recall_now)
            if args.performance_measure == "f1":
                if precision_now == 0 or recall_now == 0:
                    performance_now = .0
                else:
                    performance_now = 2.0*precision_now*recall_now / (precision_now + recall_now)
            else:
                performance_now = precision_now

            performance.append(performance_now)

            if performance_now >= max_performance:
                max_index = index
                single_threshold = measure

            index += 1

        if single_threshold == .0 or performance_now == .0:
            continue
        print "For",day_statistic
        print "There are %d positive examples" %(pos_support)
        print "The max measure is %f" %(single_threshold)
        print "with performance: %f, precision:%f, recall: %f"\
                %(performance[max_index],precision[max_index],recall[max_index])


        #prepare regression training data
        #single_feature_vector = original_top_4[single_threshold]
        single_feature_vector = list(day_statistic)
        feature_vector.append(single_feature_vector)
        threshold_vector.append(single_threshold)

    output_data(feature_vector,threshold_vector,query_ids,args.dest_dir)


if __name__=="__main__":
    main()

