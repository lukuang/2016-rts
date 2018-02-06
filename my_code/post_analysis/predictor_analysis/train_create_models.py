"""
train and create models with 5-fold or alterantively for each collection
"""


import os
import json
import sys
import re
import argparse
import codecs
from sklearn.model_selection import cross_val_score
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
    datasets = {}
    for collection_name in os.walk(top_data_dir).next()[1]:
        collection_dir = os.path.join(top_data_dir,collection_name,"data")
        datasets[collection_name] = DataSet(collection_dir,balanced)


    return datasets

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
    parser.add_argument("--cross_validation","-cv",action="store_true")
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

    datasets = load_data(args.top_data_dir)
    clf = get_classifier(args.method)

    if args.cross_validation:
        X = []
        y = []
        for collection_name in datasets:
            X += datasets[collection_name].X
            y += datasets[collection_name].y
        print "cross validation:"
        scores = cross_val_score(clf,X,y,cv=10,scoring="f1")
        # print classification_report(y, predicted_y)
        # print scores

        print "%.3f" %(sum(scores)/len(scores))
        scores = map(str, scores)
        print "[%s]" %(",".join(scores))
        print "-"*20

    else:
        for testing_collection_name in datasets:
            print "For %s" %(testing_collection_name)
            testing_X = datasets[testing_collection_name].X
            testing_y = datasets[testing_collection_name].y
            training_X = []
            training_y = []

            for training_collection_name in datasets:
                if training_collection_name != testing_collection_name:
                    training_X += datasets[training_collection_name].X
                    training_y += datasets[training_collection_name].y
            # Training
            clf = None
            clf = get_classifier(args.method)
            clf.fit(training_X,training_y)
            clf_file = os.path.join(args.top_data_dir,testing_collection_name,"model","clf_trained_on_others")
            with open(clf_file,'w') as f:
                cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)


            # Test
            predicted_y = clf.predict(testing_X)
            print classification_report(testing_y, predicted_y,digits=2)
            # print "%.3f" %(f1(testing_y, predicted_y))
            print "-"*20
    





if __name__=="__main__":
    main()


