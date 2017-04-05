"""
tree class for tree estimator
"""

import os
import json
import sys
import re
import argparse
import codecs
import numpy as np
import math



def get_medain(query_data):
    ndcgs = [sinlge_data["ndcg"] for sinlge_data in query_data]
    ndcgs.sort()
    return ndcgs[ ( len(ndcgs)/2 ) ]

class Tree(object):
    """
    Tree class
    """

    # query_data is the data structure of [{"day_qid":day_qid,"values": [], "ndcg":ndcg}]
    # where day_qid is "day_qid" which consist of day and qid
    # values is the value pairs of [overlap,bucketed log(DF)]
    #
    # value is the value of the node which is used as output when new
    # data come in. weight is the weight for adaboost algorithm
    def __init__(self,query_data,value=1.0):
        self._value = value
        self._left = None
        self._right = None
        self._c = None

        self.construct_tree(query_data)
        



    def _compute_node_weight_vector(self,query_data):
        # compute node weight vector
        ndcg_median = get_medain(query_data)
        H = [[],[]]
        t = []
        for sinlge_data in query_data:
            day_qid = sinlge_data["day_qid"]
            value_pair = sinlge_data["values"][0]
            query_ndcg = sinlge_data["ndcg"]
            H[0].append(value_pair[0])
            H[1].append(value_pair[1])
            if query_ndcg <= ndcg_median:
                t.append(-1)
            else:
                t.append(1)

        c = np.dot( H,np.transpose(H) )
        c = np.linalg.pinv(c)
        c = np.dot( c,H )
        c = np.dot( c,np.transpose(t) )
        self._c = c
        # print "new c:"
        # print c


    def _generate_subtrees(self,query_data):
        # generate subtrees according to weight vector

        left_query_data = []
        right_query_data = []
        left_value = self._value/1.5
        right_value = self._value*1.2

        for sinlge_data in query_data:
            if ( len(sinlge_data["values"])>1 ):

                day_qid = sinlge_data["day_qid"]
                value_pair = sinlge_data["values"][0]
                query_ndcg = sinlge_data["ndcg"]

                temp_data = {}
                temp_data["day_qid"] =  day_qid
                temp_data["values"] = sinlge_data["values"][1:]
                temp_data["ndcg"] = query_ndcg

                # print np.dot(value_pair,self._c)
                if np.dot(value_pair,self._c) <= 0:
                    
                    left_query_data.append(temp_data)
                else:
                    right_query_data.append(temp_data)


        self._left = Tree(left_query_data,left_value)
        self._right = Tree(right_query_data,right_value)

    def predict_value(self,value_pairs):

        # if no left subtree (leaf node)
        # or if there are no value pairs left, return the
        # value of the node
        if not value_pairs:
            return self._value

        elif self._left is None and self._right is None:
            return self._value
        else:
            value_pair = value_pairs[0]
            if np.dot(value_pair,self._c) <= 0:
                return self._left.predict_value(value_pairs[1:])
            else:
                return self._right.predict_value(value_pairs[1:])


    def construct_tree(self,query_data):
        # construct subtrees if there are some query data
        if query_data:
            self._compute_node_weight_vector(query_data)
            self._generate_subtrees(query_data)


    def compute_error(self,query_data,error_threshold):
        errors = {}
        predicted_values = {}
        real_values = {}
        for sinlge_data in query_data:
            day_qid = sinlge_data["day_qid"]
            real_values[day_qid] = sinlge_data["ndcg"] 
            predicted_values[day_qid] = self.predict_value(sinlge_data["values"])

        predicted_values = sorted(predicted_values.items(),key=lambda x:x[1])
        real_values = sorted(real_values.items(),key=lambda x:x[1])

        predicted_rank = {}
        real_rank = {}
        for j in range( len(query_data) ):
            predicted_rank[ predicted_values[j][0] ] = j
            real_rank[ real_values[j][0] ] = j


        for day_qid in predicted_rank:
            single_error = abs(predicted_rank[day_qid]-real_rank[day_qid])
            if (single_error<error_threshold ):
                errors[day_qid] = 0
            else:
                errors[day_qid] = 1

        return errors







def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("")
    args=parser.parse_args()

if __name__=="__main__":
    main()

