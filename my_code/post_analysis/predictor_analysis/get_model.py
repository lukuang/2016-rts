"""
create model from mixture of 2011-12 & 2015 & 2016 data
"""

import os
import json
import sys
import re
import argparse
import codecs
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn import metrics
from sklearn import linear_model
from sklearn.metrics import classification_report
from sklearn.metrics import f1_score as f1
from sklearn.metrics import precision_score
import numpy as np
import cPickle


class DataSet(object):
    """Dataset
    """
    def __init__(self,dataset_dir,balanced):
        self._balanced = balanced
        self._dataset_dir = dataset_dir
        self._load_data_set()

    def _load_data_set(self):
        if self._balanced:
            temp_X = json.load(open(os.path.join(self._dataset_dir,"feature")))
            temp_y = json.load(open(os.path.join(self._dataset_dir,"label")))

            true_count = 0

            for single_y in temp_y:
                if single_y:
                   true_count += 1 

            percentage = true_count*1.0/(len(temp_y) - true_count)

            self._X = []
            self._y = []

            for i in range( len(temp_y) ):
                if temp_y[i]:
                    self._X.append(temp_X[i])
                    self._y.append(temp_y[i])
                else:
                    prob = random.uniform(0, 1)
                    if prob <= percentage:
                        self._X.append(temp_X[i])
                        self._y.append(temp_y[i])
            print "There are %d positive examples and the size of the balanced data set is %d" %(true_count,len(self._X))

        else:
            self._X = json.load(open(os.path.join(self._dataset_dir,"feature")))
            self._y = json.load(open(os.path.join(self._dataset_dir,"label")))

    @property
    def X(self):
        return self._X
    
    @property
    def y(self):
        return self._y
    

def load_data(top_data_dir,balanced=False):
    training_dir = os.path.join(top_data_dir,"training","data")
    dataset_11 = DataSet(training_dir,balanced)

    testing_dir = os.path.join(top_data_dir,"testing","data")
    dataset_1516 = DataSet(testing_dir,balanced)

    return dataset_11, dataset_1516

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
    parser.add_argument("dest_model_file")
    parser.add_argument("--balanced","-bl",action="store_true")
    parser.add_argument('--method','-m',type=int,default=2,choices=range(6),
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

    dataset_11, dataset_1516 = load_data(args.top_data_dir)
    clf = get_classifier(args.method)

    print "cross validation:"
    X = dataset_11.X + dataset_1516.X
    y = dataset_11.y + dataset_1516.y
    # training_predicted = cross_val_score(clf,X,y,cv=5,scoring='f1_macro')
    # print "The average f1 is: %f" %(sum(training_predicted)/float(len(training_predicted)))
    training_predicted = cross_val_predict(clf,X,y,cv=5)
    print classification_report(y, training_predicted,digits=3)
    print "-"*20

    print "Store model"
    clf=None
    clf = get_classifier(args.method)
    clf.fit(X,y)

    with open(args.dest_model_file,'w') as f:
        cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)





if __name__=="__main__":
    main()

