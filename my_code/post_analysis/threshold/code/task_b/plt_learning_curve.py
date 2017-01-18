"""
plot learning curve
"""

import os
import json
import sys
import math
import re
import argparse
import codecs
from sklearn import cross_validation
from sklearn import metrics
from sklearn import linear_model
from sklearn.model_selection import learning_curve
from sklearn.metrics import classification_report
import numpy as np
import cPickle


def load_data_set(data_dir):
    silent_feature_vector = json.load(open(os.path.join(data_dir,"silent_feature_vector")))
    #temp = json.load(open(os.path.join(data_dir,"silent_feature_vector")))
    #silent_feature_vector = [x[0] for x in temp]
    threshold_feature_vector = json.load(open(os.path.join(data_dir,"threshold_feature_vector")))
    threshold_vector = json.load(open(os.path.join(data_dir,"threshold_vector")))
    silent_classification_vector = json.load(open(os.path.join(data_dir,"silent_classification_vector")))
    return silent_feature_vector,threshold_feature_vector,threshold_vector,silent_classification_vector



def get_classifier(method):
    if method == 0:
        from sklearn.svm import SVC
        classifier = SVC(kernel="linear",C=1)
    elif method == 1:
        from sklearn import linear_model
        classifier = linear_model.LogisticRegression(C=1e5)
    elif method == 2:
        from sklearn.naive_bayes import GaussianNB
        classifier = GaussianNB()
    elif method == 3:
        from sklearn import tree
        classifier = tree.DecisionTreeClassifier()
    else:
        from sklearn.ensemble import ExtraTreesClassifier
        classifier = ExtraTreesClassifier()


    return classifier

def gene_train_sizes(sample_size):
    train_sizes = []
    train_sizes.append(math.ceil(sample_size*1.0/3))
    train_sizes.append(math.ceil(sample_size*2.0/3))
    train_sizes.append(sample_size)



    return train_sizes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument('--method','-m',type=int,default=0,choices=range(5),
        help=
        """chose methods from:
                0:linear_svc
                1:logistic regression
                2:naive bayes
                3:decision  tree
                4:ExtraTreesClassifier
        """)
    args= parser.parse_args()

    silent_feature_vector,threshold_feature_vector,threshold_vector,silent_classification_vector\
        = load_data_set(args.data_dir)
    regr = linear_model.LinearRegression()
    clf = get_classifier(args.method)
    
    #regr_train_sizes = gene_train_sizes(len(threshold_feature_vector))        
    #clf_train_sizes = gene_train_sizes(len(silent_feature_vector)) 
    regr_train_sizes = [0.3,0.6,1.0]
    clf_train_sizes = [0.3,0.6,1.0]

    print "cross validation:"
    regr_train_sizes, regr_train_scores, regr_valid_scores =\
        learning_curve(regr, threshold_feature_vector, threshold_vector, train_sizes=regr_train_sizes, cv=5)
    
    clf_train_sizes, clf_train_scores, clf_valid_scores =\
        learning_curve(clf, silent_feature_vector, silent_classification_vector, train_sizes=clf_train_sizes, cv=5)

    print "Thresholding:"
    print regr_train_scores
    print regr_valid_scores

    print "-"*20

    print "Classification:"
    print clf_train_scores
    print clf_valid_scores


if __name__=="__main__":
    main()

