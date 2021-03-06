"""
fit model
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
import numpy as np
import cPickle

def load_data_set(data_dir):
    X = json.load(open(os.path.join(data_dir,"X")))
    y = json.load(open(os.path.join(data_dir,"y")))
    return X,y



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir")
    args= parser.parse_args()

    X,y = load_data_set(args.data_dir)
    regr = linear_model.LinearRegression()
    print "cross validation:"
    scores = cross_validation.cross_val_score(regr,X,y,cv=5, scoring='mean_squared_error',verbose=True)
    print scores 
    regr.fit(X,y)
    print "-"*20
    print 'Coefficients: \n', regr.coef_
    print "Residual sum of squares: %.2f"\
      % np.mean((regr.predict(X) - y) ** 2)
    #print regr.predict(X)
    #print y
    # Explained variance score: 1 is perfect prediction
    print 'Variance score: %.2f' % regr.score(X, y) 

    dest_file = os.path.join(args.data_dir,"coeff")
    with open(dest_file,'w') as f:
        f.write(json.dumps(list(regr.coef_)))

    regr_file = os.path.join(args.data_dir,"regr")
    with open(regr_file,"w") as f:
        cPickle.dump(regr, f, protocol=cPickle.HIGHEST_PROTOCOL)

if __name__=="__main__":
    main()

