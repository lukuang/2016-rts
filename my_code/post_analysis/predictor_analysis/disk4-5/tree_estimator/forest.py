"""
forest class for tree estimator
"""

import os
import json
import sys
import re
import argparse
import codecs
from copy import deepcopy
import random
import math

from tree import Tree

class Forest(object):
    """
    class to to iterative training to generate trees
    """
    def __init__(self,query_data,error_threshold,number_of_iterations):
        self._query_data,self._error_threshold,self._number_of_iterations=\
            query_data,error_threshold,number_of_iterations

        self._trees = []

        self._weights = {}    
        self._index_cdf = [0]*len( self._query_data )

        self._epsilon = 1.0/len(self._query_data)


    def start_training(self):
        for i in range( len(self._query_data) ):
            sinlge_data = self._query_data[i]
            self._weights[i] = 1.0/len(self._query_data)

    

        for i in range(self._number_of_iterations):
            self._gene_cdf()

            sample_data = self._sampling_data()
            # print sample_data
            single_tree = Tree( sample_data )
            errors = single_tree.compute_error(self._query_data,self._error_threshold)
            alpha = self._compute_alpha(errors)
            self._update_weights(errors,alpha)
            self._trees.append({"alpha":alpha,"single_tree":single_tree})
            # print "alpha:%f" %(alpha)

    def _gene_cdf(self):
        for i in range( len(self._query_data) ):
            if i == 0:
                self._index_cdf[0] = self._weights[i] 
            else:
                # print "new cdf %f" %(self._weights[i]+self._index_cdf[i-1])
                self._index_cdf[i] = self._weights[i]+self._index_cdf[i-1] 



    def _sampling_data(self):
        # print self._index_cdf
        # sys.exit(-1)
        sample_data = []
        indecis = []
        for i in range( len(self._query_data) ):
            prob = random.uniform(0, 1)
            for j in  range( len(self._query_data) ):
                if prob <= self._index_cdf[j]:
                    sample_data.append( deepcopy(self._query_data[j]) )
                    indecis.append(j)
                    break

        # print "Sampled"
        # print indecis

        return sample_data


    def _compute_alpha(self,errors):
        # ek = .0
        # for i in self._weights:
        #     day_qid = self._query_data[i]["day_qid"]
        #     if errors[day_qid] != 0:
        #         ek += self._weights[i]*errors[day_qid]


        ek = (sum(errors.values())*1.0)/len(errors)
        # print "ek is %f" %(ek)
        return math.log( (1-ek+self._epsilon)/(ek+self._epsilon) )/2.0

    def _update_weights(self,errors,alpha):
        for i in self._weights:
            day_qid = self._query_data[i]["day_qid"]
            if errors[day_qid] == 0:
                self._weights[i] *= math.exp(-1*alpha)
            else:
                self._weights[i] *= math.exp(alpha)

        weight_sum = sum(self._weights.values())

        for i in self._weights:
            self._weights[i] /= weight_sum
        


    def output_result(self,test_data):
        output = {}
        for sinlge_data in test_data:
            day_qid = sinlge_data["day_qid"]
            value_pairs = sinlge_data["values"]
            if day_qid not in output:
                output[day_qid] = .0
            for tree in self._trees:
                alpha = tree["alpha"]
                single_tree = tree["single_tree"]

                output[day_qid] += alpha*single_tree.predict_value(value_pairs)

        return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()

if __name__=="__main__":
    main()