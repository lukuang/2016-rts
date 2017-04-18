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



    return DataSet(training_dir,balanced)

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

    dataset = load_data(args.top_data_dir)
    clf = get_classifier(args.method)

    print "cross validation:"
    training_predicted = cross_validation.cross_val_predict(clf,dataset.X,dataset.y,cv=5)
    print classification_report(dataset.y, training_predicted)
    print "-"*20

    # print "Test on 1516 data"
    
    clf.fit(dataset.X,dataset.y)
    clf_file = os.path.join(args.top_data_dir,"training","model","clf")
    with open(clf_file,'w') as f:
        cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)


    # print "Predict:"
    # predicted_1516 = clf.predict(dataset_1516.X)
    # # print classification_report(dataset_1516.y, predicted_1516)

    # # print "Test on 11 data"
    
    # clf.fit(dataset_1516.X,dataset_1516.y)
    # testing_mode_dir = os.path.join(args.top_data_dir,"testing","model")
    # if not os.path.exists(testing_mode_dir):
    #     os.mkdir(testing_mode_dir)
    # clf_file = os.path.join(args.top_data_dir,"testing","model","clf")
    # with open(clf_file,'w') as f:
    #     cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)


    # # print "Predict:"
    # predicted_11 = clf.predict(dataset_11.X)
    # # print classification_report(dataset_11.y, predicted_11)
    # # print classification_report(dataset_1516.y, predicted_1516)
    # # print precision_score(dataset_1516.y, predicted_1516)
    # f1_1516_macro = f1(dataset_1516.y, predicted_1516,average="macro")
    # f1_1516 = f1(dataset_1516.y, predicted_1516)

    # f1_11_macro = f1(dataset_11.y, predicted_11,average="macro")
    # f1_11 = f1(dataset_11.y, predicted_11)
    # f1_average = (f1_1516+f1_11)/2.0
    # f1_macro_average = (f1_1516_macro+f1_11_macro)/2.0

    # print "Positive f1: %f" %(f1_average)
    # print "Average f1: %f" %(f1_macro_average)
    # print "-"*20






if __name__=="__main__":
    main()

