"""
fit 2 model
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument("dest_dir")
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
            
    print "cross validation:"
    scores = cross_validation.cross_val_score(regr,threshold_feature_vector,threshold_vector,cv=5,verbose=True)
    predicted = cross_validation.cross_val_predict(clf,silent_feature_vector,silent_classification_vector,cv=5)
    print scores 
    regr.fit(threshold_feature_vector,threshold_vector)
    clf.fit(silent_feature_vector,silent_classification_vector)
    print "-"*20
    #print 'Coefficients: \n', regr.coef_
    print "Residual sum of squares: %.2f"\
      % np.mean((regr.predict(threshold_feature_vector) - threshold_vector) ** 2)
    # Explained variance score: 1 is perfect prediction
    print 'Variance score: %.2f' % regr.score(threshold_feature_vector, threshold_vector) 
    print classification_report(silent_classification_vector, predicted)

    clf_file = os.path.join(args.dest_dir,"clf")
    with open(clf_file,'w') as f:
        cPickle.dump(clf, f, protocol=cPickle.HIGHEST_PROTOCOL)

    regr_file = os.path.join(args.dest_dir,"regr")
    with open(regr_file,"w") as f:
        cPickle.dump(regr, f, protocol=cPickle.HIGHEST_PROTOCOL)


if __name__=="__main__":
    main()

