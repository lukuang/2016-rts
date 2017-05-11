"""
show the learning trand (learning curve) as the number of training example growths
"""

import os
import json
import sys
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
from sklearn.utils import shuffle
from sklearn.metrics import f1_score


class DataSet(object):
    """Dataset
    """
    def __init__(self,dataset_dir):
        self._dataset_dir = dataset_dir
        self._load_data_set()

    def _load_data_set(self):
        self._X = json.load(open(os.path.join(self._dataset_dir,"feature")))
        self._y = json.load(open(os.path.join(self._dataset_dir,"label")))

    @property
    def X(self):
        return self._X
    
    @property
    def y(self):
        return self._y
    

def load_data(top_data_dir):
    training_dir = os.path.join(top_data_dir,"training","data")
    training_dataset = DataSet(training_dir)

    

    return training_dataset

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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("top_data_dir")
    parser.add_argument('--method','-m',type=int,default=0,choices=range(5),
        help=
        """chose methods from:
                0:linear_svc
                1:logistic regression
                2:naive bayes
                3:decision  tree
                4:ExtraTreesClassifier
        """)
    args=parser.parse_args()

    training_dataset = load_data(args.top_data_dir)
    clf = get_classifier(args.method)

    print "cross validation:"
    clf_train_sizes = [0.05,0.1,0.2,0.4,0.6,0.8,1.0]
    clf_train_sizes, clf_train_scores, clf_valid_scores =\
        learning_curve(clf, training_dataset.X, training_dataset.y,
                       train_sizes=clf_train_sizes, cv=10,scoring='f1')

    print "-"*20

    print "Classification:"
    print "Training:"
    print clf_train_scores
    # random.shuffle(clf_train_scores)
    # print clf_train_scores
    print "Validation:"
    print clf_valid_scores
    # random.shuffle(clf_valid_scores)
    # print clf_valid_scores

    print "Average"
    print "Training:"
    for i in clf_train_scores:
        print "%f" %(sum(i)/len(i))
    print "Validation:"
    for i in clf_valid_scores:
        print "%f" %(sum(i)/len(i))





if __name__=="__main__":
    main()

