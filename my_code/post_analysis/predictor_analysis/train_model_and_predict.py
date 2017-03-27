"""
train model and do prediction. Show performances for both
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
from sklearn.metrics import classification_report
import numpy as np
import cPickle



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

    testing_dir = os.path.join(top_data_dir,"testing","data")
    testing_dataset = DataSet(testing_dir)

    return training_dataset, testing_dataset

def get_classifier(method):
    if method == 0:
        from sklearn.svm import SVC
        classifier = SVC(kernel="linear",C=1)
        # classifier = SVC()
    elif method == 1:
        from sklearn import linear_model
        classifier = linear_model.LogisticRegression(C=1e5)
    elif method == 2:
        from sklearn.naive_bayes import GaussianNB
        classifier = GaussianNB()
    elif method == 3:
        from sklearn import tree
        classifier = tree.DecisionTreeClassifier()
    elif method == 4:
        from sklearn.ensemble import ExtraTreesClassifier
        classifier = ExtraTreesClassifier()
    else:
        from sklearn.ensemble import RandomForestClassifier
        classifier = RandomForestClassifier()

    return classifier

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("top_data_dir")
    parser.add_argument('--method','-m',type=int,default=0,choices=range(6),
        help=
        """chose methods from:
                0:linear_svc
                1:logistic regression
                2:naive bayes
                3:decision  tree
                4:ExtraTreesClassifier
                5:RandomForestClassifier
        """)
    args=parser.parse_args()

    training_dataset, testing_dataset = load_data(args.top_data_dir)
    clf = get_classifier(args.method)

    print "cross validation:"
    training_predicted = cross_validation.cross_val_predict(clf,training_dataset.X,training_dataset.y,cv=5)
    print classification_report(training_dataset.y, training_predicted)
    print "-"*20

    print "Store trained model"
    
    clf.fit(training_dataset.X,training_dataset.y)
    clf_file = os.path.join(args.top_data_dir,"training","model","clf")
    with open(clf_file,'w') as f:
        cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)
    print "-"*20


    print "Predict:"
    test_predicted = clf.predict(testing_dataset.X)
    print classification_report(testing_dataset.y, test_predicted)
    print "-"*20




if __name__=="__main__":
    main()

