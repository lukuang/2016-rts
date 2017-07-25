"""
check silent day detection performances for single term queries
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
from sklearn.metrics import f1_score as f1
from sklearn.metrics import precision_score
import numpy as np
import cPickle

sys.path.append("/infolab/node4/lukuang/2015-RTS/src/my_code/post_analysis/predictor_analysis")
from plot_silentDay_predictor import  Q_DIR,Expansion,RetrievalMethod

sys.path.append("/infolab/node4/lukuang/2015-RTS/src")
from my_code.distribution.data import Year


QREL_FILE = {
    Year.y2015:"/infolab/node4/lukuang/2015-RTS/2015-data/new_qrels.txt",
    Year.y2016:"/infolab/node4/lukuang/2015-RTS/src/2016/eval/qrels.txt",
    Year.y2011:"/infolab/node4/lukuang/2015-RTS/2011-data/raw/official_eval/new_qrels"
}


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
            self.label_dict = json.load(open(os.path.join(self._dataset_dir,"label_dict")))
            self.feature_dict = json.load(open(os.path.join(self._dataset_dir,"feature_dict")))

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


def get_judged_qid(qrel_file):
    qids = set()
    with open(qrel_file) as f:
        for line in f:
            line = line.rstrip()
            parts = line.split()
            qid = parts[0]
            qids.add(qid)

    return qids

def get_single_term_qids(query_dir,judged_qids):
    single_term_qids = set()
    day = os.walk(query_dir).next()[2][0]
    query_file = os.path.join(query_dir,day) 
    with open(query_file) as f:
        for line in f:
            line = line.rstrip()
            m = re.search("^(\w+):(.+)$",line)
            if not m:
                message = "Line malformat\n"
                message += "file name:%s\n" %(query_file)
                message += "line: %s\n" %(line)
                raise RuntimeError(message)
            else:
                qid = m.group(1)
                words = re.findall("\w+",m.group(2))
                if (qid in judged_qids)  and (len(words)==1 ):
                    single_term_qids.add(qid)
    return single_term_qids

def prepare_single_term_query_data(dataset, single_term_qids,year ):
    X_single = []
    y_single = []
    year_string = str(year)
    all_queries = dataset.label_dict[year_string]
    feature_names = dataset.feature_dict[year_string].keys()
    for day in all_queries:
        for qid in single_term_qids:
            if qid in all_queries[day]:
                single_feature_vector = []
                for f_name in sorted(feature_names):
                    single_feature_vector.append( dataset.feature_dict[year_string][f_name][day][qid] )
                X_single.append( single_feature_vector )
                if(dataset.label_dict[year_string][day][qid]):
                    y_single.append( 1 )
                else:
                    y_single.append( 0 )


    return X_single, y_single


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
    
    parser.add_argument("--expansion","-e",choices=list(map(int, Expansion)),default=0,type=int,
        help="""
            Choose the expansion:
                0:raw
                1:static:
                2:dynamic
        """)
    args=parser.parse_args()

    dataset_11, dataset_1516 = load_data(args.top_data_dir)
    clf = get_classifier(args.method)


    # get single term queries
    args.expansion = Expansion(args.expansion)
    single_term_queries = {}

    for year in Year:
        
        qrel_file = QREL_FILE[year]
        judged_qids = get_judged_qid(qrel_file)
        query_dir = Q_DIR[year][args.expansion]
        single_term_queries[year] = get_single_term_qids(query_dir,judged_qids)

    print single_term_queries

    # print "cross validation:"
    # training_predicted = cross_validation.cross_val_predict(clf,training_dataset.X,training_dataset.y,cv=5)
    # print classification_report(training_dataset.y, training_predicted)
    # print "-"*20

    # print "Test on 1516 data"
    print "load data from %s" %(args.top_data_dir)
    clf.fit(dataset_11.X,dataset_11.y)
    X_single_15, y_single_15 = prepare_single_term_query_data(dataset_1516, single_term_queries[Year.y2015],year.y2015 )
    X_single_16, y_single_16 = prepare_single_term_query_data(dataset_1516, single_term_queries[Year.y2016],year.y2016 )
    X_single_1516 = X_single_15 + X_single_16
    y_single_1516 = y_single_16 + y_single_16 
    predicted_single_1516 = clf.predict(X_single_1516)

    print classification_report(y_single_1516, predicted_single_1516)

    # print "Test on 11 data"
    
    clf.fit(dataset_1516.X,dataset_1516.y)
    X_single_11, y_single_11 = prepare_single_term_query_data(dataset_11, single_term_queries[Year.y2011],year.y2011 )
    predicted_single_11 = clf.predict(X_single_11)
    # print y_single_11, predicted_single_11
    print classification_report(y_single_11, predicted_single_11)

    f1_1516 = f1(y_single_1516, predicted_single_1516)
    f1_11 = f1(y_single_11,predicted_single_11)

    f1_average = (f1_1516 + f1_11)/2.0
    print "Positive f1: %f" %(f1_average)
    print "-"*20


    






if __name__=="__main__":
    main()



