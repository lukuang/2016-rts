"""
fit the training set to a classifier
"""

import os
import json
import sys
import re
import argparse
import codecs
import cPickle



def load_data_set(data_dir):
    X = json.load(open(os.path.join(data_dir,"X")))
    y = json.load(open(os.path.join(data_dir,"y")))
    return X,y


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
    else: 
        from sklearn import tree
        classifier = tree.DecisionTreeClassifier()

    return classifier

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    parser.add_argument('--method','-m',type=int,default=0,choices=range(4),
        help=
        """chose methods from:
                0:linear_svc
                1:logistic regression
                2:naive bayes
                3:decision  tree
        """)
    parser.add_argument("--cross_val","-c",action="store_true")
    parser.add_argument("--threshold","-t",action="store_true")
    args=parser.parse_args()

    X, y = load_data_set(args.data_dir)

    pos_support = 0
    neg_support = 0
    for i in y:
        if i==1:
            pos_support += 1
        else:
            neg_support += 1

    print "There are %d pos and %d neg" %(pos_support,neg_support) 
    if args.threshold:
        feature_size = len(X[0])
        for i in range(feature_size):
            new_data = []
            index = 0
            for sub_feature in X:
                new_data.append((sub_feature[i],y[index]))
                index+=1
            new_data = sorted(new_data,key=lambda x:x[0],reverse=True)
            with open("feature_%d"%i,'w') as f:
                f.write(json.dumps(new_data,indent=2))
            num_of_pos = 0
            precision = {}
            recall = {}
            f1 = {}
            max_f1 = .0
            max_index = 0
            max_precision = .0
            needed_value = [0.3,0.5,0.8]
            corresponding_metric = [[],[],[]]
            for index in range(len(new_data)):
                if new_data[index][1] == 1:
                    num_of_pos += 1
                    precision_now = num_of_pos*1.0/(index+1)
                    recall_now = num_of_pos*1.0/pos_support
                    precision[index] = precision_now
                    recall[index] = recall_now
                    try:
                        f1_now = 2.0*(precision_now*recall_now)/(precision_now+recall_now)
                    except ZeroDivisionError:
                        f1_now = 0.0

                    if new_data[index][0] in needed_value:
                        cr_index = needed_value.index(new_data[index][0])
                        corresponding_metric[cr_index] = [precision_now,recall_now,f1_now]
                    
                    # if precision_now >= max_precision:
                    #     max_precision = precision_now
                    if f1_now >= max_f1:
                        #max_precision = precision_now
                        max_f1 = f1_now
                        max_index = index
            print corresponding_metric
            #print "for feature %d, the best precision is %f and %d\n" %(i,max_precision,max_index)
            print "for feature %d, the best f1 is %f and %d\n" %(i,max_f1,max_index)
            print "precision %f, recall %f" %(precision[max_index],recall[max_index])
            print "Feature value is %f" %(new_data[max_index][0])
            #print recall
    else:   
        from sklearn import cross_validation
        from sklearn.metrics import classification_report
        from sklearn import metrics
        clf = get_classifier(args.method)

        if args.cross_val:
            predicted = cross_validation.cross_val_predict(clf,X,y,cv=5) 
            print classification_report(y, predicted)
        else:
            model_file = os.path.join(args.data_dir,"model")
            model = clf.fit(X,y)

            with open(model_file, 'wb') as fid:
                cPickle.dump(model, fid)    

if __name__=="__main__":
    main()

