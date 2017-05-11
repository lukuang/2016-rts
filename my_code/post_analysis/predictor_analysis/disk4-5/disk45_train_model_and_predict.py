"""
train model and do prediction. Show performances for both
"""

import os
import json
import sys
import re
import argparse
import codecs
# from sklearn import cross_validation
from sklearn import metrics
from sklearn import linear_model
from sklearn.metrics import classification_report
from copy import deepcopy
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
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
    dataset = DataSet(training_dir,balanced)

    

    return dataset

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
    parser.add_argument("--balanced","-bl",action="store_true")
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
    print "load data from %s" %(args.top_data_dir)
    dataset = load_data(args.top_data_dir)
    clf = get_classifier(args.method)
    num_of_split = 10
    skf = StratifiedKFold(n_splits=num_of_split,shuffle=True)
    # print dataset.X
    # print dataset.y
    f1_average = .0
    f1_macro_average = .0
    for training_index, test_index in skf.split(dataset.X, dataset.y):
        training_X = []
        training_y = []
        testing_X = []
        testing_y = []
        metrics = {}
        # print "%d training %d testing" %(len(training_index),len(test_index))
        # print training_index
        # print  test_index
        for i in training_index:
            training_X.append( dataset.X[i])
            training_y.append( dataset.y[i])

        for j in test_index:
            testing_X.append( dataset.X[j])
            testing_y.append( dataset.y[j])

        # print training_X
        # print testing_X
        clf.fit(training_X,training_y)  
        predicted_y = clf.predict(testing_X)
        # print classification_report(testing_y, predicted_y)
        f1_macro_average += f1(testing_y, predicted_y,average="macro")/(1.0*num_of_split)
        f1_average += f1(testing_y, predicted_y)/(1.0*num_of_split)


    
 



    # f1_11_macro = f1(dataset_11.y, predicted_11,average="macro")
    # f1_11 = f1(dataset_11.y, predicted_11)
    # f1_average = (f1_1516+f1_11)/2.0
    # f1_macro_average = (f1_1516_macro+f1_11_macro)/2.0

    print "Positive f1: %f" %(f1_average)
    print "Average f1: %f" %(f1_macro_average)
    print "-"*20






if __name__=="__main__":
    main()

